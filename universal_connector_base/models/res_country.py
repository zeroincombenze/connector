#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResCountry(models.Model):
    _inherit = "res.country"

    oe7_id = fields.Integer("Odoo7 ID", copy=False)
    oe8_id = fields.Integer("Odoo8 ID", copy=False)
    oe10_id = fields.Integer("Odoo10 ID", copy=False)
    oe12_id = fields.Integer("Odoo12 ID", copy=False)
    oe16_id = fields.Integer("Odoo16 ID", copy=False)

    @api.model_cr_context
    def _auto_init(self):
        res = super()._auto_init()
        self.env["synchro.channel"]._build_all_indexes(self)
        return res


class ResCountryState(models.Model):
    _inherit = "res.country.state"

    oe7_id = fields.Integer("Odoo7 ID", copy=False)
    oe8_id = fields.Integer("Odoo8 ID", copy=False)
    oe10_id = fields.Integer("Odoo10 ID", copy=False)
    oe12_id = fields.Integer("Odoo12 ID", copy=False)
    oe16_id = fields.Integer("Odoo16 ID", copy=False)

    @api.model_cr_context
    def _auto_init(self):
        res = super()._auto_init()
        self.env["synchro.channel"]._build_all_indexes(self)
        return res
