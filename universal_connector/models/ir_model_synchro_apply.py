# -*- coding: utf-8 -*-
#
# Copyright 2019-26 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging
from datetime import datetime, timedelta
import re

from odoo import fields, models
# from odoo import release

_logger = logging.getLogger(__name__)

try:
    from os0 import os0
except ImportError as err:  # pragma: no cover
    _logger.error(err)
# try:
#     from clodoo import transodoo
# except ImportError as err:
#     _logger.error(err)


def split_fragments(text, maxctr=3, minlen=2):
    items = []
    while True:
        x = re.search(r"[^\w]+", text)
        if not x:
            if len(text) > minlen:
                items.append(text.lower())
            break
        item = text[: x.start()].lower()
        if len(item) > minlen:
            items.append(item)
        text = text[x.end():]
    fragments = []
    while len(fragments) < maxctr:
        min_len = 0
        candidate = ""
        for item in items:
            if item not in fragments and len(item) > min_len:
                min_len = len(item)
                candidate = item
        if not candidate:
            break
        fragments.append(candidate)
    return fragments


class IrModelSynchroApply(models.Model):
    _name = "ir.model.synchro.apply"
    _inherit = "ir.model"

    def is_purchase(self, vals, vmodel):
        return (
            vmodel == "purchase.order.line"
            or vals.get("type") in ("in_invoice", "in_refund")
        )

    def apply_set_value(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if not vals.get(ext_ref) and default:
            vals[ext_ref] = default
        return vals

    def apply_set_tmp_name(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if vals.get(ext_ref) or loc_name in vals and vals[loc_name]:
            return vals
        if loc_name == "name" and vals.get("type") in ("delivery", "invoice"):
            return vals
        if not vals.get(ext_ref) and default:
            vals[ext_ref] = default
        if ext_ref in vals:
            if loc_name == loc_ext_id_name:
                if isinstance(vals[ext_ref], basestring):
                    vals[ext_ref] = int(vals[ext_ref])
            if loc_name == "code":
                vals[ext_ref] = "Code %s" % vals[ext_ref]
            else:
                vals[ext_ref] = "Unknown %s" % vals[ext_ref]
        return vals

    def apply_upper(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if ext_ref in vals and isinstance(vals[ext_ref], basestring):
            vals[ext_ref] = vals[ext_ref].upper()
        return vals

    def apply_lower(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if ext_ref in vals and isinstance(vals[ext_ref], basestring):
            vals[ext_ref] = vals[ext_ref].lower()
        return vals

    def apply_bool(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if ext_ref in vals:
            vals[ext_ref] = os0.str2bool(vals[ext_ref], False)
        return vals

    def apply_str(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if ext_ref in vals:
            vals[loc_name] = str(vals[ext_ref])
        return vals

    def apply_not(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if ext_ref in vals:
            if isinstance(vals[ext_ref], (int, long, bool)):
                vals[ext_ref] = not vals[ext_ref]
            else:
                vals[ext_ref] = not os0.str2bool(vals[ext_ref], True)
        return vals

    def apply_person(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        """First name and/or last name (they are latest fields processed)"""
        if loc_name and ext_ref in vals:
            vals[loc_name] = vals[ext_ref]
            del vals[ext_ref]
        if vals.get("firstname") or vals.get("lastname"):
            if (
                not vals.get("name")
                or vals.get("name", "").startswith("Unknown")
                or (vals.get("lastname") and vals["lastname"] in vals.get("name", ""))
                or (vals.get("firstname") and vals["firstname"] in vals.get("name", ""))
            ):
                if self.env.user.company_id.partner_id.splitmode.startswith("F"):
                    vals["name"] = (
                        vals.get("firstname", "")
                        + " "
                        + vals.get("lastname", "")
                    ).replace("  ", " ").strip()
                else:
                    vals["name"] = (
                        vals.get("lastname", "")
                        + " "
                        + vals.get("firstname", "")
                    ).replace("  ", " ").strip()
                vals["individual"] = True if vals.get(
                    "firstname") and vals.get("lastname") else False
        if "firstname" in vals and "lastname" in vals:
            del vals["firstname"]
            del vals["lastname"]
        if vals.get("type") in ("delivery", "invoice"):
            vals["individual"] = False
            vals["is_company"] = False
        else:
            vals["is_company"] = True
        return vals

    def apply_vat(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        """External vat may not contain ISO code"""
        if ext_ref in vals:
            if isinstance(vals[ext_ref], basestring):
                if len(vals[ext_ref]) == 11 and vals[ext_ref].isdigit():
                    vals[ext_ref] = "IT%s" % vals[ext_ref]
                if vmodel == "res.partner":
                    vals["individual"] = False
        return vals

    def apply_street_number(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        """Street number"""
        if ext_ref in vals:
            if "street" in vals:
                loc_name = "street"
            else:
                loc_name = "%s:street" % ext_ref[0:3]
            if loc_name in vals and vals[loc_name] and vals[ext_ref]:
                vals[loc_name] = "%s, %s" % (vals[loc_name], vals[ext_ref])
        return vals

    def apply_decode(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if ext_ref in vals and isinstance(vals[ext_ref], basestring):
            vals[ext_ref] = vals[ext_ref].replace("\r", "")
        return vals

    def apply_uom(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
        product=None,
    ):
        if (loc_name not in vals or not vals.get(loc_name)) and not vals.get(ext_ref):
            if product or "product_id" in vals:
                product = product or self.env["product.product"].browse(
                    vals["product_id"])
                vals[loc_name] = product.uom_id.id
            else:
                vals[loc_name] = self.env.ref("product.product_uom_unit").id
        return vals

    def apply_category_uom(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
        product=None,
    ):
        if (
            (loc_name not in vals or not vals.get(loc_name)) and vals.get("name")
        ):
            if vals["name"].upper() in ("NR", "N", "N.", "PZ"):
                vals[loc_name] = self.env.ref("product.product_uom_categ_unit").id
            elif vals["name"].upper() in ("M", "MT"):
                vals[loc_name] = self.env.ref("product.uom_categ_length").id
            else:
                vals[loc_name] = self.env.ref("product.product_uom_categ_unit").id
        return vals

    def apply_tax(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
        product=None,
    ):
        company_id = vals.get("company_id") or self.env.user.company_id.id
        type_tax_use = "purchase" if self.is_purchase(vals, vmodel) else "sale"

        def tax_by_rate(value):
            return self.env["account.tax"].search([
                ("company_id", "=", company_id),
                ("amount", "=", value),
                ("type_tax_use", "=", type_tax_use)], limit=1)

        def tax_by_code(value):
            return self.env["account.tax"].search([
                ("company_id", "=", company_id),
                ("description", "=", value),
                ("type_tax_use", "=", type_tax_use)], limit=1)

        tax = False
        if (
                loc_name in vals
                and isinstance(vals[loc_name], basestring)
                and ext_ref not in vals
        ):  # pragma: no cover
            vals[ext_ref] = vals[loc_name]
            del vals[loc_name]
        if loc_name not in vals or not vals.get(loc_name):
            has_value = ext_ref.startswith("vg7") and ext_ref in vals and vals[ext_ref]
            if has_value:
                if isinstance(vals[ext_ref], basestring):
                    is_numb = re.match(r"\d+(\.\d+)?$", vals[ext_ref].strip())
                    if not is_numb:
                        tax = tax_by_code(vals[ext_ref])
                    if not tax and is_numb:
                        vals[ext_ref] = eval(vals[ext_ref])
                if not tax and isinstance(vals[ext_ref], (int, long, float)):
                    if vals[ext_ref] > 0:
                        tax = tax_by_rate(vals[ext_ref])
                    if not tax:
                        tax = self.env["account.tax"].search([
                            ("company_id", "=", company_id),
                            ("vg7_id", "=", vals[ext_ref])], limit=1)
            if not tax and (product or "product_id" in vals):
                product = product or self.env["product.product"].browse(
                    vals["product_id"])
                if self.is_purchase(vals, vmodel):
                    tax = product.supplier_taxes_id
                else:
                    tax = product.taxes_id
            if not tax:
                tax = backend.tax_id or tax_by_rate(22)
        if tax:
            fiscalpos = self.env["ir.model.synchro.cache"].get_model_attr(
                backend.id, vmodel, "__%s_FP" % vmodel,
            )
            if fiscalpos:
                for tax_line in fiscalpos.tax_ids:
                    if tax_line.tax_src_id == tax:
                        tax = tax_line.tax_dest_id
                        break
            vals[loc_name] = [(6, 0, [tax.id])]
        return vals

    def apply_agents(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        def _prepare_line_agents_data(partner):
            rec = []
            for agent in partner.agents:
                rec.append({"agent": agent.id, "commission": agent.commission.id})
            return rec

        if loc_name in vals:
            return vals
        if vals.get("partner_id"):
            partner = self.env["res.partner"].browse(vals.get("partner_id"))
        elif vals.get("order_id"):
            partner = self.env["sale.order"].browse(vals["order_id"]).partner_id
        elif vals.get("invoice_id"):
            partner = self.env["account.invoice"].browse(vals["invoice_id"]).partner_id
        else:
            partner = False
        if not partner:
            return vals
        if hasattr(partner, "agents") and partner.agents:
            line_agents_data = _prepare_line_agents_data(partner)
            if line_agents_data:
                vals[loc_name] = [
                    (0, 0, line_agent_data) for line_agent_data in line_agents_data
                ]
        return vals

    def apply_partner_info(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        # doc_type = "sale"
        if loc_name in vals:
            return vals
        if vals.get("partner_id"):
            partner = self.env["res.partner"].browse(vals.get("partner_id"))
        elif vals.get("order_id"):
            partner = self.env["sale.order"].browse(vals["order_id"]).partner_id
        elif vals.get("invoice_id"):
            partner = self.env["account.invoice"].browse(vals["invoice_id"]).partner_id
        else:
            return vals
        if loc_name == "fiscal_position_id":
            partner_nm = "property_account_position_id"
        elif loc_name in ("pricelist_id", "payment_term_id"):
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
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        def get_item_val(name):
            return vals[ext_ref].get(name, vals[ext_ref].get("shipping_" + name, ""))

        if (
            "partner_id" in vals
            and ext_ref in vals
            and isinstance(vals[ext_ref], dict)
        ):
            partner = self.env["res.partner"].browse(vals["partner_id"])
            if not loc_name:
                loc_name = "partner_shipping_id"
            vals[loc_name] = vals["partner_id"]
            domain = [("type", "=", "delivery")]
            ship_vals = {"type": "delivery"}
            item = (get_item_val("name") + " "
                    + get_item_val("surename")).strip() or False
            # if item:
            #     domain.append(("name", "=", item))
            ship_vals["name"] = item
            if (
                    get_item_val("street")
                    and get_item_val("street_number")
            ):
                item = (get_item_val("street") + ", "
                        + str(get_item_val("street_number"))).strip() or False
            else:
                item = False
            if item:
                domain.append(("street", "=", item))
            ship_vals["street"] = item
            item = get_item_val("city").strip() or False
            if item:
                domain.append(("city", "=", item))
            ship_vals["city"] = item
            item = str(get_item_val("postal_code")).strip() or False
            if item:
                domain.append(("zip", "=", item))
            ship_vals["zip"] = item
            if domain:
                domain.append(("parent_id", "=", vals["partner_id"]))
                ship_vals["parent_id"] = vals["partner_id"]

                if self.env["ir.model.synchro"].compare_vals_rec(
                        ship_vals, partner, "delivery"):
                    partner_shipping = fields.first(
                        self.env["res.partner"].search(domain))
                    if not partner_shipping:
                        partner_shipping = fields.first(
                            self.env["res.partner"].search(
                                domain + [("active", "=", False)]))
                        if partner_shipping:
                            partner_shipping = partner
                else:
                    partner_shipping = partner
                if not partner_shipping:
                    try:
                        partner_shipping = self.env["res.partner"].create(ship_vals)
                    except BaseException:
                        pass
                if partner_shipping:
                    vals[loc_name] = partner_shipping.id
        return vals

    def apply_merge_shipping_address(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if isinstance(vals.get(ext_ref), dict):
            if "customer_shipping_id" in vals[ext_ref]:
                if isinstance(vals[ext_ref]["customer_shipping_id"], basestring):
                    vals[ext_ref]["id"] = int(
                        vals[ext_ref]["customer_shipping_id"]) + 100000000
                elif isinstance(vals[ext_ref]["customer_shipping_id"], (int, long)):
                    vals[ext_ref]["id"] = (
                        vals[ext_ref]["customer_shipping_id"] + 100000000)
                del vals[ext_ref]["customer_shipping_id"]
            self.env["ir.model.synchro.cache"].set_model_attr(
                backend.id, vmodel, "__%s" % "partner.shipping", vals[ext_ref]
            )
        return vals

    def apply_merge_invoice_address(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if isinstance(vals.get(ext_ref), dict):
            prefix = ext_ref.split(":")[0]
            for k, v in vals[ext_ref].items():
                if not k.startswith("billing_"):
                    continue
                ext_name = prefix + ":" + k.split("_", 1)[1]
                if ext_name not in vals and vals[ext_ref][k]:
                    vals[ext_name] = vals[ext_ref][k]
            self.env["ir.model.synchro.cache"].set_model_attr(
                backend.id, vmodel, "__%s" % "partner.invoice", vals[ext_ref]
            )
        return vals

    def apply_company_info(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
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
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if loc_name in vals:
            return vals
        ctx = ctx or {}
        if loc_name in ctx:
            vals[loc_name] = ctx[loc_name]
        return vals

    def apply_set_einvoice(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if vals.get(ext_ref):
            if len(vals[ext_ref]) == 7:
                vals["electronic_invoice_subjected"] = True
                vals["is_pa"] = False
            elif len(vals[ext_ref]) == 6:
                vals["electronic_invoice_subjected"] = False
                vals["is_pa"] = True
                vals["ipa_code"] = vals[ext_ref]
        return vals

    def apply_set_is_pa(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if len(vals.get(ext_ref, "")) == 6:
            vals["is_pa"] = True
        return vals

    def apply_iban(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if vals.get(ext_ref):
            vals[ext_ref] = vals[ext_ref].replace(" ", "")
        elif vals.get("vg7:ABI") and vals.get("vg7:CAB"):
            vals[ext_ref] = "IT00A%s%s000000000000" % (vals["ABI"], vals["CAB"])
        return vals

    def apply_eom(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if vals.get(ext_ref):
            eom = os0.str2bool("%s" % vals[ext_ref], False)
            if eom:
                vals["option"] = "day_after_invoice_date"
            else:
                vals["option"] = "fix_day_following_month"
            del vals[ext_ref]
        if vals.get("vg7:scadenza"):
            if (
                isinstance(vals["vg7:scadenza"], basestring)
                and vals["vg7:scadenza"].isdigit()
            ):
                num_days = int(vals["vg7:scadenza"])
            elif isinstance(vals["vg7:scadenza"], (int, long)):
                num_days = vals["vg7:scadenza"]
            else:
                num_days = False
            if num_days:
                Cache = self.env["ir.model.synchro.cache"]
                if Cache.get_struct_model_attr("account.payment.term.line", "months"):
                    vals["months"] = num_days / 30
                    vals["days"] = 0
                else:
                    vals["days"] = num_days - 2
        return vals

    def apply_set_inv_warn(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if vals.get(ext_ref):
            vals["invoice_warn"] = "warning"
        return vals

    def apply_datetime(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if vals.get(ext_ref):
            if len(vals[ext_ref].split(" ")) == 1:
                vals[ext_ref] = "%s 00:00:00" % vals[ext_ref]
        return vals

    def apply_set_order_state(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        vals[loc_name] = "sale"
        return vals

    def apply_set_purchase_order_state(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if vals.get(ext_ref):
            state = vals[ext_ref]
            if state in ("draft", "cancel", "purchase"):
                vals[loc_name] = state
        elif not vals.get(loc_name):
            vals[loc_name] = "purchase"
        return vals

    # def apply_set_weight_vg7(
    #     self,
    #     backend,
    #     vals,
    #     loc_name,
    #     ext_ref,
    #     loc_ext_id_name,
    #     vmodel,
    #     default=None,
    #     ctx=None,
    # ):
    #     if vals.get(ext_ref):
    #         vals[loc_name] = vals[ext_ref]
    #         for nm in ("product_uom_qty", "vg7:peso"):
    #             if nm in vals:
    #                 vals[loc_name] = vals[ext_ref] * vals[nm]
    #                 break
    #     return vals

    def apply_unit_price_vg7(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if vals.get(ext_ref):
            vals[ext_ref] = round(vals[ext_ref] * 0.82, 3)
        return vals

    def apply_prod_by_name(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if (
                loc_name == "product_id"
                and "name" in vals
                and not isinstance(vals.get(ext_ref), (int, long))
        ):
            Product = self.env["product.product"]
            prod_name = vals["name"]
            for ln in vals["name"].split("\n"):
                if "Nome prodotto:" in ln:
                    prod_name = ln.split(":", 1)
                    break
            prod_name = self.env["ir.model.synchro.cache"].hashname(
                prod_name, like=True)
            tmpl_name = prod_name
            if "bg7_job_name" in vals:
                prod_name += "%" + self.env["ir.model.synchro.cache"].hashname(
                    vals["vg7:job_name"], like=True)
            elif "job_name" in vals:
                prod_name += "%" + self.env["ir.model.synchro.cache"].hashname(
                    vals["job_name"], like=True)
            prod_name = "%" + prod_name + "%"
            prods = Product.search([("name", "ilike", prod_name)], limit=1)
            self.env["ir.model.synchro"].logmsg(
                "debug",
                "%(model)s.search(%(domain)s) -> %(id)s",
                model=Product._name,
                id=prods[0].id if prods else None,
                ctx={
                    "domain": "[(\"name\", \"ilike\", \"%s\")]" % prod_name,
                    "LOGLEVEL": backend. tracelevel,
                },
            )
            if not prods and prod_name != tmpl_name:
                tmpl_name = "%" + tmpl_name + "%"
                prods = Product.search([("name", "ilike", tmpl_name)], limit=1)
                self.env["ir.model.synchro"].logmsg(
                    "debug",
                    "%(model)s.search(%(domain)s) -> %(id)s",
                    model=Product._name,
                    id=prods[0].id if prods else None,
                    ctx={
                        "domain": "[(\"name\", \"ilike\", \"%s\")]" % tmpl_name,
                        "LOGLEVEL": backend.tracelevel,
                    },
                )
            if not prods:
                prods = Product.search([("default_code", "=", "MISC")])
            if prods:
                vals[loc_name] = fields.first(prods).id
        return vals

    def apply_job_name(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if "name" in vals and vals.get(ext_ref):
            vals["name"] = vals["name"] + "\n" + vals[ext_ref]
        return vals

    def apply_line_vals_from_prod(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if vals.get("product_id"):
            pass
        return vals

    def apply_product_vg7_naming(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        name_field = des_field = ""
        for field in vals.keys():
            if ":" in field and field.split(":")[1] == "name":
                name_field = field
            elif ":" in field and field.split(":")[1] == "description":
                des_field = field
            elif field == "name":
                name_field = field
            elif field == "description_sale":
                name_field = field
        if des_field and vals[des_field] and (not name_field or not vals[name_field]):
            vals[name_field] = vals[des_field]
            del vals[des_field]
        return vals

    def apply_today(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if not vals.get(ext_ref):
            vals[ext_ref] = datetime.today().strftime("%Y-%m-%d")
        return vals

    def apply_now(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if not vals.get(ext_ref):
            vals[ext_ref] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        return vals

    def apply_next_week_day(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if not vals.get(ext_ref):
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
