#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    vg7_id = fields.Integer("VG7 ID", copy=False)



class ProductProduct(models.Model):
    _inherit = "product.product"

    vg7_id = fields.Integer("VG7 ID", copy=False)


class UomUom(models.Model):
    _inherit = "uom.uom"

    vg7_id = fields.Integer("VG7 ID", copy=False)



class UomCategory(models.Model):
    _inherit = "uom.category"

    vg7_id = fields.Integer("VG7 ID", copy=False)



class ProductCategory(models.Model):
    _inherit = "product.category"

    vg7_id = fields.Integer("VG7 ID", copy=False)



class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    vg7_id = fields.Integer("VG7 ID", copy=False)
