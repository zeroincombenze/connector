#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
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
    _name = "synchro.apply"
    _description = "Functions to convert field data"

    def is_purchase(self, vals, vmodel):
        return vmodel == "purchase.order.line" or vals.get("type") in (
            "in_invoice",
            "in_refund",
        )

    def apply_odoo_migrate(
            self,
            mapper,
            vals,
            loc_name,
            ext_ref,
            default=None,
            ctx=None,
    ):
        Api = self.env["synchro.api"]
        dir_mapper = mapper.model_id
        vals[ext_ref] = Api.odoo_tnl_value_from_loc_to_ext(
            mapper.backend_id, dir_mapper.name, vals[ext_ref], loc_name)
        return vals

    def apply_none(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):
        return vals

    def apply_set_tmp_name(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):
        if (
            not PY3
            and mapper.model_id.name.startswith("res.partner")
            and vals.get("type") in ("delivery", "invoice")
        ):  # pragma: no cover
            return vals
        loc_ext_id = mapper.model_id.get_loc_ext_id()
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
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if ext_ref in vals and isinstance(vals[ext_ref], str):
            vals[ext_ref] = vals[ext_ref].upper()
        return vals

    def apply_lower(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if ext_ref in vals and isinstance(vals[ext_ref], str):
            vals[ext_ref] = vals[ext_ref].lower()
        return vals

    def apply_bool(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):
        if ext_ref in vals:
            vals[ext_ref] = str2bool(vals[ext_ref], False)
        return vals

    def apply_str(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if ext_ref in vals:
            vals[ext_ref] = str(vals[ext_ref])
        return vals

    def apply_not(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if ext_ref in vals:
            if isinstance(vals[ext_ref], (int, bool)):
                vals[ext_ref] = not vals[ext_ref]
            else:
                vals[ext_ref] = not str2bool(vals[ext_ref], True)
        return vals

    def apply_strip(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):
        if ext_ref in vals and isinstance(vals[ext_ref], str):
            vals[ext_ref] = vals[ext_ref].strip()
        return vals

    def apply_sanitize_vat(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
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
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        """Invoice number"""
        if ext_ref in vals:
            vals["move_name"] = vals[ext_ref]
        return vals

    def apply_journal(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):
        if "journal_id" not in vals:
            journal = self.env["account.invoice"]._default_journal()
            if journal:
                vals["journal_id"] = journal[0].id
        return vals

    def apply_property(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):
        if (
            (loc_name not in vals or not vals.get(loc_name))
            and not vals.get(ext_ref)
            and mapper.fields_id
        ):
            domain = [("fields_id", "=", mapper.fields_id.id)]
            if "company_id" in vals:
                domain.append(("company_id", "=", vals["company_id"]))
            value = self.env["ir.property"].search(domain)
            if value:
                vals[ext_ref] = int(value[0].value_reference.split(",", 1)[1])
        return vals

    def apply_account(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
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
                if self.is_purchase(vals, mapper.model_id.name):
                    vals[loc_name] = accounts["expense"].id
                else:
                    vals[loc_name] = accounts["income"].id
            else:
                if "journal_id" in vals:
                    journal_id = vals["journal_id"]
                else:
                    journal_id = self.env["account.invoice"]._default_journal()
                journal = self.env["account.journal"].browse(journal_id)
                if self.is_purchase(vals, mapper.model_id.name):
                    vals[loc_name] = journal.default_debit_account_id.id
                else:
                    vals[loc_name] = journal.default_credit_account_id.id
        return vals

    def apply_tax(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
        product=None,
    ):
        if (loc_name not in vals or not vals.get(loc_name)) and (
            product or "product_id" in vals
        ):
            product = product or self.env["product.product"].browse(vals["product_id"])
            if self.is_purchase(vals, mapper.model_id.name):
                tax = product.supplier_taxes_id
            else:
                tax = product.taxes_id
            if tax:
                vals[loc_name] = [(6, 0, [tax.id])]
        return vals

    def apply_partner_info(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
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
        mapper,
        vals,
        loc_name,
        ext_ref,
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
        mapper,
        vals,
        loc_name,
        ext_ref,
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
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):
        if (
            (loc_name not in vals or not vals.get(loc_name))
            and not vals.get(ext_ref)
            and mapper.required
        ):
            ctx = ctx or {}
            if loc_name in ctx:
                vals[ext_ref] = ctx[loc_name]
        return vals

    def apply_selection(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):
        if (loc_name not in vals or not vals.get(loc_name)) and not vals.get(ext_ref):
            struct = self.env[mapper.model_id.name].fields_get()
            value = struct[loc_name].get("selection", [""])[0]
            vals[ext_ref] = value[0] if isinstance(value, (list, tuple)) else value
        return vals

    def apply_float(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):
        struct = self.env[mapper.model_id.name].fields_get()
        if struct[loc_name]["type"] in ("float", "monetary"):
            if (loc_name not in vals or not vals.get(loc_name)) and not vals.get(
                ext_ref
            ):
                vals[ext_ref] = 1.0
            elif isinstance(vals.get(ext_ref), str):
                vals[ext_ref] = eval(vals[ext_ref])
        return vals

    def apply_integer(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):
        struct = self.env[mapper.model_id.name].fields_get()
        if struct[loc_name]["type"] == "integer":
            if (loc_name not in vals or not vals.get(loc_name)) and not vals.get(
                ext_ref
            ):
                vals[ext_ref] = 0
            elif isinstance(vals.get(ext_ref), str) and vals[ext_ref].isdigit():
                vals[ext_ref] = int(vals[ext_ref])
        return vals

    def apply_datetime(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):
        if vals.get(ext_ref) and len(vals[ext_ref].split(" ")) == 1:
            vals[ext_ref] = "%s 00:00:00" % vals[ext_ref]
        return vals

    ############################
    # ODOO MIGRATION FUNCTIONS #
    ############################
    def apply_oe_account_tax_amount(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):
        Api = self.env["synchro.api"]
        dir_mappper = mapper.model_id
        vals[loc_name] = Api.odoo_tnl_value_from_loc_to_ext(
            mapper.backend_id, dir_mappper.name, vals[ext_ref], loc_name
        )
        return vals

    def apply_oe_account_account_type_name(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):
        if not vals.get(loc_name):
            Api = self.env["synchro.api"]
            dir_mapper = mapper.model_id
            names = Api.odoo_tnl_value_from_loc_to_ext(
                mapper.backend_id, dir_mapper.name, vals[ext_ref], loc_name
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
        mapper,
        vals,
        loc_name,
        ext_ref,
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
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if (loc_name not in vals or not vals.get(loc_name)) and not vals.get(ext_ref):
            vals[ext_ref] = datetime.today().strftime("%Y-%m-%d")
        return vals

    def apply_now(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if (
            (loc_name not in vals or not vals.get(loc_name))
            and not vals.get(ext_ref)
            and default
        ):
            vals[ext_ref] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        return vals

    def apply_next_week_day(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):
        if (
            (loc_name not in vals or not vals.get(loc_name))
            and not vals.get(ext_ref)
            and default
        ):
            vals[ext_ref] = (datetime.today() + timedelta(7)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        return vals
