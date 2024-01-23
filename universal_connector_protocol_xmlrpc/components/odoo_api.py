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

_logger = logging.getLogger(__name__)


class OdooApiOerplib(models.AbstractModel):
    _name = "synchro.odoo.api.oerplib"
    _description = "API with XML RPC protocol by oerplib (only Odoo 10.0-)"

    def api_set_env(self, ignore_error=None, backend=None):
        backend.login_endpoint = backend.hostname
        backend.data_endpoint = backend.hostname
        return self

    def api_connect(self, ignore_error=None, backend=None):
        return None
