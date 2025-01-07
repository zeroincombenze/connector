#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    odoo10_id = fields.Integer("Odoo10 ID", copy=False)
    odoo12_id = fields.Integer("Odoo12 ID", copy=False)
    odoo16_id = fields.Integer("Odoo16 ID", copy=False)

    @api.model_cr_context
    def _auto_init(self):
        res = super()._auto_init()
        self.env["synchro.backend"]._build_all_indexes(self)
        return res
