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
# from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OdooApiXmlrpc(models.Model):
    _name = "synchro.odoo.api.requests"
    _inherit = "abstract.odoo.api"
    _description = "Connector API with odoorpc library"

    def init_requests(self, pylib):
        try:
            import requests
            self._api = requests
            self._pypi_sign = pylib
        except ImportError:
            _logger.debug("Cannot import 'import requests'")

    def api_login(self):
        headers = {'Authorization': 'access_token %s' % self._backend.password}
        endpoint = self._backend.get_login_endpoint()
        try:
            response = requests.get(                               # noqa: F821
                endpoint, headers=headers, verify=False)
        except BaseException:
            _logger.debug("Http response %s'" % getattr(
                response, 'status_code', 'N/A'))
            return None
        self._remote_peer = response
