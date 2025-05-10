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
import re
import itertools

from odoo import models

from python_plus import str2bool

_logger = logging.getLogger(__name__)


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
    _inherit = "synchro.apply"

    def apply_person(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        """First name and/or last name"""
        if ext_ref in vals and loc_name != ext_ref:
            vals[loc_name] = vals[ext_ref]
            del vals[ext_ref]
        if "firstname" in vals and vals["firstname"] is None:
            del vals["firstname"]
        if "lastname" in vals and vals["lastname"] is None:
            del vals["lastname"]
        if "firstname" in vals and "lastname" in vals:
            if vals["firstname"] or vals["lastname"]:
                if hasattr(
                    self.env.user.company_id.partner_id, "splitmode"
                ) and self.env.user.company_id.partner_id.splitmode.startswith("F"):
                    vals["name"] = (
                        (vals.get("firstname", "") + " " + vals.get("lastname", ""))
                        .replace("  ", " ")
                        .strip()
                    )
                else:
                    vals["name"] = (
                        (vals.get("lastname", "") + " " + vals.get("firstname", ""))
                        .replace("  ", " ")
                        .strip()
                    )
                vals["is_company"] = False
                if not PY3:
                    vals["individual"] = True
            else:
                vals["is_company"] = True
                if not PY3:
                    vals["individual"] = False
            del vals["firstname"]
            del vals["lastname"]
        return vals

    def apply_street_number(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        """Street number"""
        if ext_ref in vals:
            if "street" in vals:
                loc_name = "street"
            else:
                loc_name = "%s:street" % ext_ref[0:3]
            if loc_name in vals:
                vals[loc_name] = "%s, %s" % (vals[loc_name], vals[ext_ref])
            del vals[ext_ref]
        return vals

    def apply_agents(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):  # pragma: no cover
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

    def apply_set_einvoice(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if vals.get(ext_ref):
            if len(vals[ext_ref]) == 7:
                vals["electronic_invoice_subjected"] = True
                vals["is_pa"] = False
            elif len(vals[ext_ref]) == 6:
                vals["electronic_invoice_subjected"] = False
                vals["is_pa"] = True
                vals["ipa_code"] = vals[ext_ref]
                if loc_name in vals:
                    del vals[loc_name]
        return vals

    def apply_set_is_pa(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if len(vals.get(ext_ref, "")) == 6:
            vals["is_pa"] = True
        return vals

    def apply_iban(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if vals.get(ext_ref):
            vals[loc_name] = vals[ext_ref].replace(" ", "")
        elif vals.get("vg7:ABI") and vals.get("vg7:CAB"):
            vals[loc_name] = "IT00A%s%s000000000000" % (vals["ABI"], vals["CAB"])
        return vals

    def apply_eom(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if vals.get(ext_ref):
            eom = str2bool("%s" % vals[ext_ref], False)
            if eom:
                vals["option"] = "day_after_invoice_date"
            else:
                vals["option"] = "fix_day_following_month"
            del vals[ext_ref]
        if vals.get("vg7:scadenza"):
            if (
                isinstance(vals["vg7:scadenza"], str)
                and vals["vg7:scadenza"].isdigit()
            ):
                num_days = int(vals["vg7:scadenza"])
            elif isinstance(vals["vg7:scadenza"], int):
                num_days = vals["vg7:scadenza"]
            else:
                num_days = False
            if num_days:
                Cache = self.env["synchro.cache"]
                if Cache.get_struct_model_attr("account.payment.term.line", "months"):
                    vals["months"] = num_days / 30
                    vals["days"] = 0
                else:
                    vals["days"] = num_days - 2
        return vals

    def apply_set_inv_warn(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if vals.get(ext_ref):
            vals["invoice_warn"] = "warning"
            vals[loc_name] = vals[ext_ref]
        return vals

    def apply_set_order_state(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if vals.get(ext_ref):
            if vals.get(ext_ref) and (
                isinstance(vals[ext_ref], int)
                or (isinstance(vals[ext_ref], str) and vals[ext_ref].isdigit())
            ):
                state = {
                    1: "draft",
                    2: "sale",
                    3: "sale",
                    4: "sale",
                    5: "cancel",
                    6: "cancel",
                    7: "sale",
                    8: "sale",
                    9: "sale",
                    10: "sale",
                    11: "sale",
                    12: "draft",
                    13: "sale",
                    14: "sale",
                    15: "sale",
                    16: "sale",
                }.get(int(vals[ext_ref]), "")
            else:
                state = vals[ext_ref]
            if state in ("draft", "cancel", "sale"):
                vals[loc_name] = state
        return vals

    def apply_set_weight_vg7(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if vals.get(ext_ref):
            vals[loc_name] = vals[ext_ref]
            for nm in ("product_uom_qty", "vg7:peso"):
                if nm in vals:
                    vals[loc_name] = vals[ext_ref] * vals[nm]
                    break
        return vals

    def apply_unit_price_vg7(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):  # pragma: no cover
        if vals.get(ext_ref):
            vals[loc_name] = round(vals[ext_ref] * 0.82, 3)
        return vals

    def apply_prod_by_name(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):
        Product = self.env["product.product"]
        field = ext_ref if vals.get(ext_ref) else "name"
        fragments = split_fragments(vals[field])
        if len(fragments) == 0:
            prods = Product.search([("default_code", "=", "MISC")])
        elif len(fragments) == 1:
            prods = Product.search([("name", "ilike", fragments[0])])
        else:
            domain = []
            for perms in itertools.permutations(fragments, len(fragments) - 1):
                text = "%"
                for perm in perms:
                    text += perm + "%"
                domain.append(("name", "ilike", text))
            for i in range(len(domain) - 1):
                domain.insert(0, "|")
            prods = Product.search(domain)
        if not prods:
            prods = Product.search([("default_code", "=", "MISC")])
        if prods:
            vals[loc_name] = prods[0].id
        return vals

    def apply_product_vg7_naming(
        self,
        mapper,
        vals,
        loc_name,
        ext_ref,
        default=None,
        ctx=None,
    ):  # pragma: no cover
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

        if vals.get(ext_ref):
            vals[loc_name] = vals[ext_ref]
            del vals[ext_ref]
        if ext_ref in vals:
            del vals[ext_ref]
        return vals
