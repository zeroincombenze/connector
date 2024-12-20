#
# Copyright 2018-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from future.utils import PY3
import logging
from datetime import datetime, timedelta

from odoo import models

from python_plus import str2bool

_logger = logging.getLogger(__name__)


class IrModelSynchroApply(models.Model):
    _name = "ir.model.synchro.apply"
    _inherit = "ir.model"

    def is_purchase(self, vals, vmodel):
        return vmodel == "purchase.order.line" or vals.get("type") in (
            "in_invoice",
            "in_refund",
        )

    def apply_set_value(
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
        if loc_name not in vals and not vals.get(ext_ref) and default:
            vals[ext_ref] = default
        return vals

    def apply_set_tmp_name(
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
        if loc_name in vals and vals[loc_name]:
            return vals
        if (
            not PY3
            and vmodel.startswith("res.partner")
            and vals.get("type") in ("delivery", "invoice")
        ):  # pragma: no cover
            return vals
        if not vals.get(ext_ref):
            if default:
                vals[ext_ref] = default
            elif loc_ext_id in vals:
                if loc_name in ("code", "default_code"):
                    vals[ext_ref] = "code%s" % vals[loc_ext_id]
                else:
                    vals[ext_ref] = "Unknown %s" % vals[loc_ext_id]
            else:
                vals[ext_ref] = "Unknown %s" % loc_name
        return vals

    def apply_upper(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id,
        vmodel,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if ext_ref in vals and isinstance(vals[ext_ref], str):
            vals[ext_ref] = vals[ext_ref].upper()
        return vals

    def apply_lower(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id,
        vmodel,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if ext_ref in vals and isinstance(vals[ext_ref], str):
            vals[ext_ref] = vals[ext_ref].lower()
        return vals

    def apply_bool(
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
        if ext_ref in vals:
            vals[ext_ref] = str2bool(vals[ext_ref], False)
        return vals

    def apply_str(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id,
        vmodel,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if ext_ref in vals:
            vals[ext_ref] = str(vals[ext_ref])
        return vals

    def apply_not(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id,
        vmodel,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if ext_ref in vals:
            if isinstance(vals[ext_ref], (int, bool)):
                vals[ext_ref] = not vals[ext_ref]
            else:
                vals[ext_ref] = not str2bool(vals[ext_ref], True)
        return vals

    def apply_vat(
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
        """External vat may not contain ISO code"""
        if ext_ref in vals and isinstance(vals[ext_ref], str):
            vals[ext_ref] = vals[ext_ref].strip()
            if len(vals[ext_ref]) == 11 and vals[ext_ref].isdigit():
                vals[ext_ref] = "IT%s" % vals[ext_ref]
        return vals

    def apply_invoice_number(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id,
        vmodel,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        """Invoice number"""
        if ext_ref in vals:
            vals["move_name"] = vals[ext_ref]
        return vals

    def apply_journal(
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
        if "journal_id" not in vals:
            journal = self.env["account.invoice"]._default_journal()
            if journal:
                vals["journal_id"] = journal[0].id
        return vals

    def apply_account(
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
        if (loc_name not in vals or not vals.get(loc_name)) and (
            product or "product_id" in vals
        ):
            product = product or self.env["product.product"].browse(vals["product_id"])
            accounts = product.product_tmpl_id._get_product_accounts()
            if accounts:
                if self.is_purchase(vals, vmodel):
                    vals[loc_name] = accounts["expense"].id
                else:
                    vals[loc_name] = accounts["income"].id
            else:
                if "journal_id" in vals:
                    journal_id = vals["journal_id"]
                else:
                    journal_id = self.env["account.invoice"]._default_journal()
                journal = self.env["account.journal"].browse(journal_id)
                if self.is_purchase(vals, vmodel):
                    vals[loc_name] = journal.default_debit_account_id.id
                else:
                    vals[loc_name] = journal.default_credit_account_id.id
        return vals

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
        if loc_name not in vals or not vals.get(loc_name):
            if product or "product_id" in vals:
                product = product or self.env["product.product"].browse(
                    vals["product_id"]
                )
                vals[loc_name] = product.uom_id.id
            else:
                vals[loc_name] = self.env.ref("uom.product_uom_unit").id
        return vals

    def apply_tax(
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
        if (loc_name not in vals or not vals.get(loc_name)) and (
            product or "product_id" in vals
        ):
            product = product or self.env["product.product"].browse(vals["product_id"])
            if self.is_purchase(vals, vmodel):
                tax = product.supplier_taxes_id
            else:
                tax = product.taxes_id
            if tax:
                vals[loc_name] = [(6, 0, [tax.id])]
        return vals

    def apply_partner_info(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id,
        vmodel,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        doc_type = "sale"
        if loc_name in vals:
            return vals
        if vals.get("partner_id"):
            partner = self.env["res.partner"].browse(vals.get("partner_id"))
        elif vals.get("order_id"):
            if vals.get("order_number"):
                doc_type = "purchase"
                partner = self.env["purchase.order"].browse(vals["order_id"]).partner_id
            else:
                partner = self.env["sale.order"].browse(vals["order_id"]).partner_id
        elif vals.get("invoice_id"):
            partner = self.env["account.invoice"].browse(vals["invoice_id"]).partner_id
        else:
            return vals
        if loc_name == "fiscal_position_id":
            partner_nm = "property_account_position_id"
        elif loc_name in ("pricelist_id", "payment_term_id"):
            if doc_type == "purchase":
                partner_nm = "property_supplier_%s" % loc_name
            else:
                partner_nm = "property_%s" % loc_name
        else:
            partner_nm = loc_name
        if partner_nm in partner:
            try:
                vals[loc_name] = partner[partner_nm].id
            except BaseException:
                vals[loc_name] = partner[partner_nm]
        return vals

    def apply_partner_address(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id,
        vmodel,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if (
            loc_name in vals
            and isinstance(vals.get(loc_name), int)
            and vals[loc_name] > 0
        ):
            return vals
        if "partner_id" in vals:
            vals[loc_name] = vals["partner_id"]
        return vals

    def apply_company_info(
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
        if loc_name in vals:
            return vals
        company_id = vals.get("company_id")
        if not company_id:
            return vals
        company = (
            self.env["res.company"]
            .with_context({"lang": self.env.user.lang})
            .browse(company_id)
        )
        if loc_name == "note":
            partner_nm = "sale_note"
        else:
            partner_nm = loc_name
        if partner_nm in company:
            try:
                vals[loc_name] = company[partner_nm].id
            except BaseException:
                vals[loc_name] = company[partner_nm]
        return vals

    def apply_get_global(
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
        if loc_name not in vals and not vals.get(ext_ref):
            ctx = ctx or {}
            if loc_name in ctx:
                vals[ext_ref] = ctx[loc_name]
        return vals

    def apply_datetime(
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
        if vals.get(ext_ref) and len(vals[ext_ref].split(" ")) == 1:
            vals[ext_ref] = "%s 00:00:00" % vals[ext_ref]
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

    ############################
    # ODOO MIGRATION FUNCTIONS #
    ############################
    def apply_oe_account_tax_amount(
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
        Api = self.env["synchro.api"]
        synchro_model = self.env["ir.model.synchro"].get_synchro_model_from_loc(
            backend, vmodel
        )
        vals[loc_name] = Api.odoo_tnl_value_from_to(
            backend, synchro_model, vals[ext_ref], loc_name
        )
        return vals

    def apply_oe_account_account_type_name(
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
        if not vals.get(loc_name):
            Api = self.env["synchro.api"]
            synchro_model = self.env["ir.model.synchro"].get_synchro_model_from_loc(
                backend, vmodel
            )
            names = Api.odoo_tnl_value_from_to(
                backend, synchro_model, vals[ext_ref], loc_name
            )
            name = vals.get("name", "").lower()
            if isinstance(names, list):
                for nm in names:
                    if nm == name:
                        vals[loc_name] = nm
                        break
        return vals

    def apply_oe_account_account_type(
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
        if vals[ext_ref] == "view":
            vals[loc_name] = "other"
        else:
            vals[loc_name] = vals[ext_ref]
        return vals

    def apply_today(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id,
        vmodel,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if not vals.get(loc_name):
            vals[ext_ref] = datetime.today().strftime("%Y-%m-%d")
        return vals

    def apply_now(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id,
        vmodel,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if not vals.get(loc_name):
            vals[ext_ref] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        return vals

    def apply_next_week_day(
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
        if not vals.get(loc_name):
            vals[ext_ref] = (datetime.today() + timedelta(7)).strftime(
                "%Y-%m-%d %H:%M:%S"
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
