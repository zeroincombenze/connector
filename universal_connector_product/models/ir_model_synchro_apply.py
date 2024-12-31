#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class IrModelSynchroApply(models.Model):
    _inherit = "ir.model.synchro.apply"

    def apply_uom(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id,
        vmodel,
        default=None,
        ctx=None,
        product=None,
    ):
        if (loc_name not in vals or not vals.get(loc_name)) and not vals[ext_ref]:
            if product or "product_id" in vals and not vmodel.startswith("product."):
                product = product or self.env["product.product"].browse(
                    vals["product_id"]
                )
                vals[ext_ref] = product.uom_id.id
            else:
                vals[ext_ref] = self.env.ref("uom.product_uom_unit").id
        return vals

    def apply_line_vals_from_prod(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id,
        vmodel,
        default=None,
        ctx=None,
    ):
        if vals.get("product_id"):
            Product = self.env["product.product"]
            product = Product.browse(vals["product_id"])
            if not vals.get("product_uom"):
                vals = self.apply_uom(
                    backend, vals, "product_uom", None, None, vmodel, product=product
                )
            if vmodel == "purchase.order.line" and not vals.get("taxes_id"):
                vals = self.apply_tax(
                    backend, vals, "taxes_id", None, None, vmodel, product=product
                )
            elif vmodel == "sale.order.line" and not vals.get("tax_id"):
                vals = self.apply_tax(
                    backend, vals, "tax_id", None, None, vmodel, product=product
                )
            elif vmodel == "account.invoice.line" and not vals.get(
                "invoice_line_tax_ids"
            ):
                vals = self.apply_tax(
                    backend,
                    vals,
                    "invoice_line_tax_ids",
                    None,
                    None,
                    vmodel,
                    product=product,
                )
            elif vmodel == "stock.picking.package.preparation.line" and not vals.get(
                "tax_ids"
            ):
                vals = self.apply_tax(
                    backend, vals, "tax_ids", None, None, vmodel, product=product
                )
            if vmodel == "account.invoice.line" and not vals.get("account_id"):
                vals = self.apply_account(
                    backend, vals, "account_id", None, None, vmodel, product=product
                )
        return vals

    def get_default_product(self):
        Cache = self.env["ir.model.synchro.cache"]
        product = Cache.get_struct_model_attr("product.product", "DEF_REC")
        if product:
            return product
        product = self.env["product.product"].search([("default_code", "=", "MISC")])
        if not product:
            product = self.env["product.product"].search([], limit=1)
        if product:
            product = product[0]
        Cache.set_struct_model_attr("product.product", "DEF_REC", product)
        return product

    def get_default_location_id(self):
        Cache = self.env["ir.model.synchro.cache"]
        location = Cache.get_struct_model_attr("stock.location", "DEF_ID")
        if location:
            return location.id
        location = self.env["stock.location"].search([], limit=1, order="id")
        if location:
            location = location[0]
            Cache.set_struct_model_attr("product.product", "DEF_ID", location.id)
            return location.id
        return False
