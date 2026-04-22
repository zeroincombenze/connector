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

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

try:
    from unidecode import unidecode
except ImportError as err:
    _logger.debug(err)


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.multi
    @api.depends("name")
    def _set_dim_name(self):
        for partner in self:
            if partner.name:
                partner.dim_name = self.env["ir.model.synchro"].dim_text(partner.name)
            elif partner.parent_id:
                partner.dim_name = self.env["ir.model.synchro"].dim_text(
                    partner.parent_id.name
                )

    vg7_id = fields.Integer("VG7 ID", copy=False)
    vg72_id = fields.Integer("VG7 ID (2.nd)", copy=False)
    oe7_id = fields.Integer("Odoo7 ID", copy=False)
    oe8_id = fields.Integer("Odoo8 ID", copy=False)
    oe10_id = fields.Integer("Odoo10 ID", copy=False)
    dim_name = fields.Char(
        "Search Key", compute=_set_dim_name, store=True, readonly=True
    )
    timestamp = fields.Datetime("Timestamp", copy=False, readonly=True)
    errmsg = fields.Char("Error message", copy=False, readonly=True)

    CONTRAINTS = [["id", "!=", "parent_id"]]

    @api.model_cr_context
    def _auto_init(self):
        res = super(ResPartner, self)._auto_init()
        for prefix in ("vg7", "vg72", "oe7", "oe8", "oe10"):
            self.env["ir.model.synchro"]._build_unique_index(self._inherit, prefix)
        return res

    def wep_text(self, text):
        if text:
            return unidecode(text).strip()
        return text

    def dim_text(self, text):
        text = self.wep_text(text)
        if text:
            res = ""
            for ch in text:
                if ch.isalnum():
                    res += ch.lower()
            text = res
        return text

    @api.model
    def shirt_vals(self, vals, ext_ref):
        self.env["ir.model.synchro"].logmsg(
            "debug", ">>> res.partner.shirt_vals(%s,%s)" % (vals, ext_ref)
        )
        prefix1 = ext_ref.split(":")[0]
        prefix2 = "%s_" % ext_ref.split(":")[1]
        prefix = "%s:" % prefix1
        for field in vals.copy():
            if field.startswith(ext_ref):
                name = "%s" % field.replace(prefix2, "")
            elif field.startswith(prefix):
                name = field
            elif field.startswith(prefix2):
                name = "%s:%s" % (prefix1, field.replace(prefix2, ""))
            else:
                name = "%s:%s" % (prefix1, field)
            if name != field:
                vals[name] = vals[field]
                del vals[field]
        for nm in ("vg7:company", "vg7:name", "vg7:surename"):
            if nm in vals and (
                not isinstance(vals[nm], basestring) or not vals[nm].strip()
            ):
                del vals[nm]
        return vals

    @api.model
    def preprocess(self, backend, vals):
        def set_vg7_id(vals):
            for nm in ("customer_shipping_id", "vg7:id", "vg7_id"):
                if vals.get(nm):
                    if isinstance(vals[nm], basestring):
                        vals[nm] = int(vals[nm])
                    if vals.get("type"):
                        vals[nm] = self.env["ir.model.synchro"].get_loc_ext_id_value(
                            backend.id, "res.partner", vals[nm], spec=vals["type"]
                        )
            return vals

        _logger.info(">>> preprocess(%s)" % vals)  # debug
        cache = self.env["ir.model.synchro.cache"]
        # actual_model = "res.partner"
        spec = ""
        if cache.get_attr(backend.id, "PREFIX") == "vg7":
            if vals.get("type") == "delivery":
                vals = set_vg7_id(vals)
                for ext_ref in (
                    "vg7:piva",
                    "vg7:cf",
                    "vg7:esonerato_fe",
                    "vg7:codice_univoco",
                    "electronic_invoice_subjected",
                ):
                    if ext_ref in vals:
                        del vals[ext_ref]
                spec = vals["type"]
            elif vals.get("type") == "invoice":
                vals = set_vg7_id(vals)
                spec = vals["type"]
            else:
                for ext_ref in ("parent_id", "type_inv_addr"):
                    if ext_ref in vals:
                        del vals[ext_ref]
        return vals, spec

    @api.model
    def postprocess(self, backend_id, parent_id, vals):
        _logger.info(">>> postprocess(%d,%s)" % (parent_id, vals))  # debug
        cache = self.env["ir.model.synchro.cache"]
        model = "res.partner"
        done = False
        for ext_ref in ("vg7:shipping", "vg7:billing"):
            if cache.get_model_attr(backend_id, model, ext_ref):
                vals = {}
                for field in cache.get_model_attr(backend_id, model, ext_ref):
                    vals[field] = cache.get_model_attr(backend_id, model, ext_ref)[
                        field
                    ]
                vals["parent_id"] = parent_id
                cache.del_model_attr(backend_id, model, ext_ref)
                self.synchro(vals, chk_in_queue=True)
                done = True
        return done

    def assure_values(self, vals, rec):
        actual_model = "res.partner"
        actual_cls = self.env[actual_model]
        vals["lang"] = "it_IT"
        if rec:
            for nm in ("type", "individual"):
                if nm not in vals:
                    vals[nm] = getattr(rec, nm)
            nm = "parent_id"
            if nm not in vals:
                vals[nm] = getattr(rec, nm).id
        parent = False
        if vals.get("parent_id"):
            parent_id = int(vals["parent_id"])
            parent = actual_cls.search([("id", "=", parent_id)])
            if parent:
                parent = parent[0]
            else:
                del vals["parent_id"]
        elif rec and rec.parent_id:
            parent = rec.parent_id

        decl_is_company = True
        if "is_company" not in vals:
            vals["is_company"] = False if vals.get("individual") else True
            decl_is_company = False
        if vals.get("type") in ("delivery", "invoice"):
            if not decl_is_company:
                vals["is_company"] = False
            if parent and not isinstance(parent, (int, long)):
                # if (
                #     not vals.get('name')
                #     or vals['name'].startswith('Unknown')
                #     or vals.get('name') == parent.name
                # ):
                if vals.get("name") and (
                    vals.get("name") == parent.name
                    or vals.get("name", "").startswith("Unknown")
                ):
                    vals["name"] = False
                elif not vals.get("name"):
                    vals["name"] = False
            if parent and not isinstance(parent, (int, long)):
                for nm in (
                    "vat",
                    "fiscalcode",
                    "codice_destinatario",
                    "country_id",
                    "state_id",
                    "electronic_invoice_subjected",
                    "is_pa",
                    "ipa_code",
                ):
                    if (
                        not vals.get(nm)
                        and parent[nm]
                        and (not rec or (rec and not rec[nm]))
                    ):
                        if nm.endswith("_id"):
                            vals[nm] = parent[nm].id
                        else:
                            vals[nm] = parent[nm]
                if vals["type"] == "delivery":
                    for nm in (
                        "codice_destinatario",
                        "electronic_invoice_subjected",
                        "is_pa",
                        "ipa_code",
                    ):
                        vals[nm] = False
        else:
            if not vals.get("name") and not rec:
                if vals.get("vat") or vals.get("fiscalcode"):
                    vals["name"] = "Unknown"
                else:
                    # Force error
                    vals["name"] = None
            if parent and (vals.get("individual")
                           or vals.get("type") in ("delivery", "invoice")):
                vals["is_company"] = False

        if "codice_destinatario" in vals and not vals["codice_destinatario"]:
            del vals["codice_destinatario"]
        if vals.get("electronic_invoice_subjected") and not vals.get(
            "codice_destinatario"
        ):
            if rec and rec.codice_destinatario:
                vals["codice_destinatario"] = rec.codice_destinatario.strip()
            else:
                vals["electronic_invoice_subjected"] = False
        if "ipa_code" in vals and not vals["ipa_code"]:
            del vals["ipa_code"]
        if vals.get("is_pa") and not vals.get("ipa_code"):
            if rec and rec.ipa_code:
                vals["ipa_code"] = rec.ipa_code.strip()
            else:
                vals["is_pa"] = False
        if vals.get("rea_code"):
            ids = actual_cls.search([("rea_code", "=", vals["rea_code"])])
            if ids:
                if not rec or ids[0].id != rec.id:
                    _logger.info("Duplicate REA Code %s" % vals["rea_code"])
                    del vals["rea_code"]
        return vals

    @api.model
    def synchro(self, vals, chk_in_queue=None, only_minimal=None, no_deep_fields=None,
                no_del_child=False):
        if not chk_in_queue:
            vals[":type"] = "contact"
        return self.env["ir.model.synchro"].synchro(
            self,
            vals,
            chk_in_queue=chk_in_queue,
            only_minimal=only_minimal,
            no_deep_fields=no_deep_fields,
            no_del_child=no_del_child,
        )

    @api.multi
    def pull_record(self):
        self.env["ir.model.synchro"].pull_record(self)


class ResPartnerShipping(models.Model):
    _name = "res.partner.shipping"
    _inherit = "res.partner"

    CONTRAINTS = ["id", "!=", "parent_id"]

    @api.model
    def synchro(self, vals, chk_in_queue=None, only_minimal=None, no_deep_fields=None,
                no_del_child=False):
        # vals = self.env["res.partner"].shirt_vals(vals, "vg7:shipping")
        vals[":type"] = "delivery"
        return self.env["ir.model.synchro"].synchro(
            self,
            vals,
            chk_in_queue=chk_in_queue,
            only_minimal=only_minimal,
            no_deep_fields=no_deep_fields,
            no_del_child=no_del_child,
        )


class ResPartnerInvoice(models.Model):
    _name = "res.partner.invoice"
    _inherit = "res.partner"

    CONTRAINTS = ["id", "!=", "parent_id"]

    @api.model
    def synchro(self, vals, chk_in_queue=None, only_minimal=None, no_deep_fields=None,
                no_del_child=False):
        # vals = self.env["res.partner"].shirt_vals(vals, "vg7:billing")
        vals[":type"] = "invoice"
        return self.env["ir.model.synchro"].synchro(
            self,
            vals,
            chk_in_queue=chk_in_queue,
            only_minimal=only_minimal,
            no_deep_fields=no_deep_fields,
            no_del_child=no_del_child,
        )


class ResPartnerSupplier(models.Model):
    _name = "res.partner.supplier"
    _inherit = "res.partner"

    @api.model
    def synchro(self, vals, chk_in_queue=None, only_minimal=None, no_deep_fields=None,
                no_del_child=False):
        vals["supplier"] = True
        vals[":type"] = "contact"
        return self.env["ir.model.synchro"].synchro(
            self,
            vals,
            chk_in_queue=chk_in_queue,
            only_minimal=only_minimal,
            no_deep_fields=no_deep_fields,
            no_del_child=no_del_child,
        )
