#
# Copyright 2019-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    oe7_id = fields.Integer("Odoo7 ID", copy=False)
    oe8_id = fields.Integer("Odoo8 ID", copy=False)
    oe10_id = fields.Integer("Odoo10 ID", copy=False)
    oe12_id = fields.Integer("Odoo12 ID", copy=False)
    oe16_id = fields.Integer("Odoo16 ID", copy=False)
    timestamp = fields.Datetime("Timestamp", copy=False, readonly=True)
    errmsg = fields.Char("Error message", copy=False, readonly=True)

    CONTRAINTS = [["id", "!=", "parent_id"]]

    @api.model_cr_context
    def _auto_init(self):
        res = super()._auto_init()
        self.env["synchro.channel"]._build_all_indexes(self)
        return res

    def __assure_values(self, vals, rec):
        actual_model = "res.partner"
        actual_cls = self.env[actual_model]
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
            if parent and not isinstance(parent, int):
                if vals.get("name") and (
                    vals.get("name") == parent.name
                    or vals.get("name", "").startswith("Unknown")
                ):
                    vals["name"] = False
                elif not vals.get("name"):
                    vals["name"] = False
            if parent and not isinstance(parent, int):
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
            if parent and vals.get("individual"):
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
    def synchro(
        self,
        vals,
        backend=None,
        only_minimal=True,
        ttl=None,
        running_in_queue=None,
    ):
        if only_minimal:
            vals[":type"] = vals.get(":type", "contact")
        return super().synchro(
            vals,
            backend=backend,
            only_minimal=only_minimal,
            ttl=ttl,
            running_in_queue=running_in_queue,
        )
