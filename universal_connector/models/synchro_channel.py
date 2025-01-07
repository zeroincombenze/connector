#
# Copyright 2019-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class SynchroChannel(models.Model):
    _inherit = "synchro.backend"

    @api.model
    def find_model_channel(self, model_name=None, ext_model=None):
        if model_name:
            domain = [("name", "=", model_name)]
        elif ext_model:
            domain = [("counterpart_name", "=", ext_model)]
        else:
            return None
        if self.id:
            domain.append(("backend_id", "=", self.id))
        rec = self.env["synchro.model"].search(domain, order="sequence")
        if rec:
            rec = rec[0]
        return rec
