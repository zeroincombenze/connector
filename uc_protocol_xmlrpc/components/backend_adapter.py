#
# Copyright 2019-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

import logging
from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OdooApiXmlrpc(models.Model):
    _name = "synchro.odoo.api.xmlrpc"
    _inherit = "abstract.odoo.api"
    _description = "Connector API with odoorpc library"

    def init_odoo_client_lib(self, pylib):
        """Initialize API of odoo-client-lib pypi
        odoo-client-lib manages xmlrpc protocol with python3 and replace the
        oerplib and erpeek packages that run only with python2;
        odoo-client-lib can manage json protocol, so it is a valid alternative
        to odoorpc library.
        This method is called by OdooAPI.__init__ with specific protocol"""
        try:
            import odoolib

            self._api = odoolib
            self._pypi_sign = pylib
        except ImportError:
            _logger.debug("Cannot import 'odoo-client-lib'")

    def api_login_xmlrpc(self):
        """Do login via xmlrpc.client
        Login is done calling http get of specific URL endpoint
        i.e. Odoo endpoint is
        http://URL/xmlrpc/2/common (see web module)"""
        self._login_endpoint = self._backend.get_login_endpoint(with_port=True)
        remote_peer = self._api.ServerProxy(self._login_endpoint)
        try:
            remote_peer.common.authenticate(
                self._backend.database, self._backend.login, self._backend.password, {}
            )
        except BaseException as e:
            _logger.exception(e)
            raise UserError(e)
        self._data_endpoint = self._backend.get_data_endpoint(with_port=True)
        remote_peer = self._api.ServerProxy(self._data_endpoint)
        self._remote_peer = remote_peer
