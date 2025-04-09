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

    _sql_constraints = [
        ("ref_unique_odoo_id", "unique(odoo_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo16_id", "unique(odoo16_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo14_id", "unique(odoo14_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo12_id", "unique(odoo12_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo10_id", "unique(odoo10_id)", "Remote ref must be unique!"),
    ]

    odoo_id = fields.Integer("Odoo ID", copy=False)
    odoo16_id = fields.Integer("Odoo16 ID", copy=False)
    odoo14_id = fields.Integer("Odoo14 ID", copy=False)
    odoo12_id = fields.Integer("Odoo12 ID", copy=False)
    odoo10_id = fields.Integer("Odoo10 ID", copy=False)
    timestamp = fields.Datetime("Timestamp", copy=False, readonly=True)
    errmsg = fields.Char("Error message", copy=False, readonly=True)


class ProductProduct(models.Model):
    _inherit = "product.product"

    _sql_constraints = [
        ("ref_unique_odoo_id", "unique(odoo_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo16_id", "unique(odoo16_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo14_id", "unique(odoo14_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo12_id", "unique(odoo12_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo10_id", "unique(odoo10_id)", "Remote ref must be unique!"),
    ]

    odoo_id = fields.Integer("Odoo ID", copy=False)
    odoo16_id = fields.Integer("Odoo16 ID", copy=False)
    odoo14_id = fields.Integer("Odoo14 ID", copy=False)
    odoo12_id = fields.Integer("Odoo12 ID", copy=False)
    odoo10_id = fields.Integer("Odoo10 ID", copy=False)
    timestamp = fields.Datetime("Timestamp", copy=False, readonly=True)
    errmsg = fields.Char("Error message", copy=False, readonly=True)

    @api.model
    def preprocess(self, backend_id, vals):
        cache = self.env["synchro.cache"]
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

    _sql_constraints = [
        ("ref_unique_odoo_id", "unique(odoo_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo16_id", "unique(odoo16_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo14_id", "unique(odoo14_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo12_id", "unique(odoo12_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo10_id", "unique(odoo10_id)", "Remote ref must be unique!"),
    ]

    odoo_id = fields.Integer("Odoo ID", copy=False)
    odoo16_id = fields.Integer("Odoo16 ID", copy=False)
    odoo14_id = fields.Integer("Odoo14 ID", copy=False)
    odoo12_id = fields.Integer("Odoo12 ID", copy=False)
    odoo10_id = fields.Integer("Odoo10 ID", copy=False)


class UomCategory(models.Model):
    _inherit = "uom.category"

    _sql_constraints = [
        ("ref_unique_odoo_id", "unique(odoo_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo16_id", "unique(odoo16_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo14_id", "unique(odoo14_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo12_id", "unique(odoo12_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo10_id", "unique(odoo10_id)", "Remote ref must be unique!"),
    ]

    odoo_id = fields.Integer("Odoo ID", copy=False)
    odoo16_id = fields.Integer("Odoo16 ID", copy=False)
    odoo14_id = fields.Integer("Odoo14 ID", copy=False)
    odoo12_id = fields.Integer("Odoo12 ID", copy=False)
    odoo10_id = fields.Integer("Odoo10 ID", copy=False)


class ProductCategory(models.Model):
    _inherit = "product.category"

    _sql_constraints = [
        ("ref_unique_odoo_id", "unique(odoo_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo16_id", "unique(odoo16_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo14_id", "unique(odoo14_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo12_id", "unique(odoo12_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo10_id", "unique(odoo10_id)", "Remote ref must be unique!"),
    ]

    odoo_id = fields.Integer("Odoo ID", copy=False)
    odoo16_id = fields.Integer("Odoo16 ID", copy=False)
    odoo14_id = fields.Integer("Odoo14 ID", copy=False)
    odoo12_id = fields.Integer("Odoo12 ID", copy=False)
    odoo10_id = fields.Integer("Odoo10 ID", copy=False)


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    _sql_constraints = [
        ("ref_unique_odoo_id", "unique(odoo_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo16_id", "unique(odoo16_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo14_id", "unique(odoo14_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo12_id", "unique(odoo12_id)", "Remote ref must be unique!"),
        ("ref_unique_odoo10_id", "unique(odoo10_id)", "Remote ref must be unique!"),
    ]

    odoo_id = fields.Integer("Odoo ID", copy=False)
    odoo16_id = fields.Integer("Odoo16 ID", copy=False)
    odoo14_id = fields.Integer("Odoo14 ID", copy=False)
    odoo12_id = fields.Integer("Odoo12 ID", copy=False)
    odoo10_id = fields.Integer("Odoo10 ID", copy=False)
