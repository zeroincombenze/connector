#
# Copyright 2019-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    odoo10_id = fields.Integer("Odoo10 ID", copy=False)
    odoo12_id = fields.Integer("Odoo12 ID", copy=False)
    odoo16_id = fields.Integer("Odoo16 ID", copy=False)
    timestamp = fields.Datetime("Timestamp", copy=False, readonly=True)
    errmsg = fields.Char("Error message", copy=False, readonly=True)
    original_state = fields.Char("Original Status", copy=False)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    odoo10_id = fields.Integer("Odoo10 ID", copy=False)
    odoo12_id = fields.Integer("Odoo12 ID", copy=False)
    odoo16_id = fields.Integer("Odoo16 ID", copy=False)
    to_delete = fields.Boolean("Record to delete")
