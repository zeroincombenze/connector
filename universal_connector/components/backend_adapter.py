#
# Copyright 2019-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

import logging
import sys

from odoo import _
from odoo.addons.component.core import AbstractComponent
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OdooAPI(object):

    def init_xmlrpc_client(self, pylib):
        """Initialize API of python xmlrpc client
        This method is called by OdooAPI.__init__ with specific protocol"""
        try:
            from xmlrpc import client
            self._api = client
            self._pypi_sign = pylib
        except ImportError:
            _logger.debug("Cannot import 'xmlrpc.client'")

    def init_odoorpc(self, pylib):
        """Initialize API of odoorpc pypi
        odoorpc is the most common pypi used to connect Odoo instances via json;
        it replaces the oerplib and erppeek packages that use xmlrpc protocol.
        This method is called by OdooAPI.__init__ with specific protocol"""
        try:
            import odoorpc
            self._api = odoorpc
            self._pypi_sign = pylib
        except ImportError:
            _logger.debug("Cannot import 'odoorpc'")

    def init_odoo_client_lib(self, pylib):
        """Initialize API of odoo-client-lib pypi
        odoo-client-lib manages xmlrpc protocol with python3 and replace the
        oerplib and erpeek packages that run only with python2;
        odoo-client-lib can manage json protocol, so it is a avlid alternative
        to odoorpc library.
        This method is called by OdooAPI.__init__ with specific protocol"""
        try:
            import odoolib
            self._api = odoolib
            self._pypi_sign = pylib
        except ImportError:
            _logger.debug("Cannot import 'odoo-client-lib'")

    def init_oerplib(self, pylib):
        """Initialize API of oerplib pypi
        oerplib was the most common pypi with python2 used to connect Odoo
        instances via xmlrcp;
        this method can be called only in Odoo 10.0 or less.
        This method is called by OdooAPI.__init__ with specific protocol"""
        if sys.version_info == 2:
            try:
                import odoorpc
                self._api = odoorpc
                self._pypi_sign = pylib
            except ImportError:
                _logger.debug("Cannot import 'odoorpc'")

    # TODO> to export into universal_connector_json_over_http
    def init_requests(self, pylib):
        """Initialize API of python requests library
        requests manages Odoo access via web interface like GUI interface
        see web module to furthermore information
        This method is called by OdooAPI.__init__ with specific protocol"""
        try:
            import requests
            self._api = requests
            self._pypi_sign = pylib
        except ImportError:
            _logger.debug("Cannot import 'import requests'")

    def __init__(self, backend):
        """Initialize API in order to manage the backend connection.
        Load python or PYPI library needed and store its instance in self._api
        Load self._pypi_sign to inform end-user.

        Args:
            backend (obj): backend instance to retrieve connection params

        Returns:
            None: backend _api and _pypi_sign fields are updated
        """
        self._backend = backend
        self._remote_peer = None
        self._api = None
        self._pypi_sign = None
        self._login_endpoint = backend.hostname
        self._data_endpoint = backend.hostname
        pylibs = ''
        if self._backend.protocol_id:
            pylibs = self._backend.protocol_id.pylib
            for pylib in pylibs.split(','):
                _api = 'init_%s' % pylib.replace('.', '_').replace('-', '_')
                if hasattr(self, _api):
                    getattr(self, _api)(pylib)
                    if self._pypi_sign:
                        break
        if not self._pypi_sign:
            raise UserError(
                _(
                    "No python neither RCP library found!\n"
                    "Please install %s" % (pylibs or 'odoorpc')
                )
            )

    def api_login_xmlrpc_client(self):
        """Do login via xmlrpc.client
        Login is done calling http get of specific URL endpoint
        i.e. Odoo endpoint is
        http://URL/xmlrpc/2/common (see web module)"""
        self._login_endpoint = self._backend.get_login_endpoint(with_port=True)
        remote_peer = self._api.ServerProxy(self._login_endpoint)
        try:
            remote_peer.common.authenticate(
                self._backend.database,
                self._backend.login,
                self._backend.password,
                {})
        except BaseException as e:
            _logger.exception(e)
            raise UserError(e)
        self._data_endpoint = self._backend.get_data_endpoint(with_port=True)
        remote_peer = self._api.ServerProxy(self._data_endpoint)
        self._remote_peer = remote_peer

    def api_login_odoorpc(self):
        """Do login via odoorpc
        Login is done calling specific login function after connection function
        (see odoorpc docs)"""
        remote_peer = self._api.ODOO(
            host=self._backend.hostname,
            port=self._backend.port,
            protocol=self._backend.protocol_id.code,
        )
        try:
            remote_peer.login(
                db=self._backend.database,
                login=self._backend.login,
                password=self._backend.password,
            )
        except self.api.error.RPCError as e:
            _logger.exception(e)
            raise UserError(e)
        self._remote_peer = remote_peer

    def api_login_odoo_client_lib(self):
        """Do login via odoo-client-lib
        Login is done calling specific login function; there is no connection
        function to call (see odoo-client-lib docs)"""
        try:
            remote_peer = self._api.get_connection(
                hostname=self._backend.hostname,
                database=self._backend.database,
                protocol=self._backend.protocol_id.code,
                port=self._backend.port,
                login=self._backend.login,
                password=self._backend.password,
            )
            remote_peer.check_login()
        except BaseException as e:
            _logger.exception(e)
            raise UserError(e)
        self._remote_peer = remote_peer

    # TODO> to export into universal_connector_json_over_http
    def api_login_requests_http_json(self):
        """Do login via requests
        requests is rest protocol, so there is no any login function to call;
        so a generic api is called in order to test valid login."""
        headers = {'Authorization': 'access_token %s' % self._backend.password}
        self._login_endpoint = self._backend.get_login_endpoint()
        response = False
        try:
            response = self._api.get(                              # noqa: F821
                self._login_endpoint, headers=headers, verify=False)
        except BaseException as e:
            _logger.debug("Http response %s'" % getattr(
                response, 'status_code', 'N/A'))
            _logger.exception(e)
            raise UserError(e)
        self._remote_peer = response

    def api_login_generic(self):
        """Do generic login
        Based on backend protocol, the specific login function is called.

        Args:
            self._backend (obj): backend instance to retrieve login params
        Returns:
            None: backend _remote_peer field is updated"""
        if self._api:
            # API initialized
            _api_login = ('api_login_%s_%s' % (
                self._pypi_sign,
                self._backend.protocol_id.code)).replace(
                '.', '_').replace('+', '_').replace('-', '_')
            if hasattr(self, _api_login):
                # Do specific protocol and library login
                getattr(self, _api_login)()
            else:
                _api_login = ('api_login_%s' % self._pypi_sign).replace(
                    '.', '_').replace('+', '_').replace('-', '_')
                if hasattr(self, _api_login):
                    # Do libray login
                    getattr(self, _api_login)()
                else:
                    raise UserError(
                        _(
                            "No python neither RCP library found!\n"
                            "Please install %s" % (
                                self._backend._pypi_sign or 'odoorpc')
                        )
                    )

    @property
    def api(self):
        self.api_login_generic()
        if self._backend.default_lang_id:
            _logger.debug(
                "Associated lang %s to location" %
                self._backend.default_lang_id
            )
            # self._remote_peer.env.context[
            #     "lang"] = self._backend.default_lang_id
        # _logger.info(
        #     "Created a new Odoo API instance and logged in with context %s"
        #     % self._remote_peer.env.context
        # )
        return self._remote_peer

    def complete_check(self):
        self.api_login_generic()
        if self._backend.version:
            # Remote peer is Odoo: check if remote version matches with
            # required version
            if (self._backend.protocol_id.code.startswith('jsonrpc') and
                    self._pypi_sign == 'odoorpc'):
                try:
                    server_version = self._remote_peer.version
                except BaseException:
                    server_version = ''
            elif (self._backend.protocol_id.code.startswith('xmlrpc') and
                  self._pypi_sign == 'oerplib'):
                try:
                    server_version = self._remote_peer.db.server_version()
                except BaseException:
                    server_version = ''
            else:
                server_version = self._backend.version
            if not server_version.startswith(self._backend.version):
                raise UserError(
                    _(
                        "Server indicates version %s. Please adapt your conf"
                        % server_version
                    )
                )

    def __enter__(self):
        # we do nothing, api is lazy
        return self

    def __exit__(self, type, value, traceback):
        _logger.debug(traceback)


class OdooCRUDAdapter(AbstractComponent):
    """ External Records Adapter for Odoo """

    _name = "odoo.crud.adapter"
    _inherit = ["base.backend.adapter", "base.synchro.connector"]
    _usage = "backend.adapter"

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids """
        raise NotImplementedError

    def read(self, id, attributes=None):                # pylint: disable=W8106
        """ Returns the information of a record """
        raise NotImplementedError

    def search_read(self, filters=None):
        """ Search records according to some criterias
        and returns their information"""
        raise NotImplementedError

    def create(self, data):                             # pylint: disable=W8106
        """ Create a record on the external system """
        raise NotImplementedError

    def write(self, id, data):                          # pylint: disable=W8106
        """ Update records on the external system """
        raise NotImplementedError

    def delete(self, id):
        """ Delete a record on the external system """
        raise NotImplementedError

    def execute(self, id, data):
        """ Execute method for a record on the external system """
        raise NotImplementedError


class GenericAdapter(AbstractComponent):
    _name = "synchro.adapter"
    _inherit = "odoo.crud.adapter"

    # _odoo_model = None
    # _admin_path = None

    def search(self, filters=None, model=None):
        """ Search records according to some criterias
        and returns a list of ids
        :rtype: list
        """

        ext_model = model or self._odoo_model

        try:
            odoo_api = self.work.odoo_api.api
        except AttributeError:
            raise AttributeError(
                "You must provide a odoo_api attribute with a "
                "OdooAPI instance to be able to use the "
                "Backend Adapter."
            )

        model = odoo_api.env[ext_model]
        return model.search(filters if filters else [])

    def read(self, id, attributes=None, model=None,     # pylint: disable=W8106
             context=None):
        """ Returns the information of a record
        :rtype: dict
        """
        arguments = [int(id)]
        ext_model = model or self._odoo_model
        if attributes:
            # Avoid to pass Null values in attributes. Workaround for
            # https://bugs.launchpad.net/openerp-connector-Odoo/+bug/1210775
            # When Odoo is installed on PHP 5.4 and the compatibility patch
            # http://odoo.com/blog/Odoo-news/Odoo-now-supports-php-54
            # is not installed, calling info() with None in attributes
            # would return a wrong result (almost empty list of
            # attributes). The right correction is to install the
            # compatibility patch on odoo.
            arguments.append(attributes)

        try:
            odoo_api = self.work.odoo_api.api
        except AttributeError:
            raise AttributeError(
                "You must provide a odoo_api attribute with a "
                "OdooAPI instance to be able to use the "
                "Backend Adapter."
            )
        model = odoo_api.env[ext_model]
        if context:
            return model.with_context(context).browse(arguments)
        return model.browse(arguments)

    def create(self, data):                             # pylint: disable=W8106
        ext_model = self._odoo_model
        try:
            odoo_api = self.work.odoo_api.api
        except AttributeError:
            raise AttributeError(
                "You must provide a odoo_api attribute with a "
                "OdooAPI instance to be able to use the "
                "Backend Adapter."
            )
        model = odoo_api.env[ext_model]
        return model.create(data)

    def write(self, id, data):                          # pylint: disable=W8106
        arguments = [int(id)]
        # ext_model = self._odoo_model
        try:
            odoo_api = self.work.odoo_api.api
        except AttributeError:
            raise AttributeError(
                "You must provide a odoo_api attribute with a "
                "OdooAPI instance to be able to use the "
                "Backend Adapter."
            )
        model = odoo_api.env[self._odoo_model]
        object_id = model.browse(arguments)
        # TODO: Check the write implementation of odoorpc
        return object_id.write(data)
