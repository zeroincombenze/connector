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
    _name = "synchro.odoo.api.jsonrpc"
    _inherit = "abstract.odoo.api"
    _description = "Connector API by JSON RPC protocol"

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
