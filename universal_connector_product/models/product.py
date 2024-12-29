#
# Copyright 2018-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

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


class ProductProduct(models.Model):
    _inherit = "product.product"

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

    @api.model
    def preprocess(self, backend_id, vals):
        cache = self.env["ir.model.synchro.cache"]
        if ("vg7_id" in vals or "vg7:id" in vals) and cache.get_attr(
            backend_id, "NO_VARIANTS"
        ):
            tmpl_vals = vals.copy()
            if "id" in tmpl_vals:
                del tmpl_vals["id"]
            id = self.env["product.template"].synchro(tmpl_vals)
            if id > 0:
                vals["product_tmpl_id"] = id


class UomUom(models.Model):
    _inherit = "uom.uom"

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


class UomCategory(models.Model):
    _inherit = "uom.category"

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


class ProductCategory(models.Model):
    _inherit = "product.category"

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


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

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
