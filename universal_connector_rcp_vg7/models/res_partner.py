#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    _sql_constraints = [
        ('ref_unique_vg7_id', 'unique(vg7_id)', 'Remote ref must be unique!'),
    ]

    vg7_id = fields.Integer("VG7 ID", copy=False)
    vg72_id = fields.Integer("VG7 ID (2.nd)", copy=False)

    CONTRAINTS = [["id", "!=", "parent_id"]]

    def assure_values(self, vals, rec):
        binding_model = "res.partner"
        Binder = self.env[binding_model]
        if rec:
            for nm in ("type", "individual"):
                if nm not in vals and hasattr(self, nm):
                    vals[nm] = getattr(rec, nm)
            nm = "parent_id"
            if nm not in vals:
                vals[nm] = getattr(rec, nm).id
        if vals.get("type") not in ("delivery", "invoice"):
            vals["parent_id"] = False

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
            ids = Binder.search([("rea_code", "=", vals["rea_code"])])
            if ids:
                if not rec or ids[0].id != rec.id:
                    # _logger.info("Duplicate REA Code %s" % vals["rea_code"])
                    del vals["rea_code"]
        return vals
#
#
# class ResPartnerShipping(models.Model):
#     _name = "res.partner.shipping"
#     _inherit = "res.partner"
#
#     CONTRAINTS = ["id", "!=", "parent_id"]
#
#     vg7_id = fields.Integer("VG7 ID", copy=False)
#
#     @api.model
#     def synchro(
#         self,
#         vals,
#         only_minimal=True,
#         ttl=None,
#         running_in_queue=None,
#         jacket=None,
#         model_spec=False,
#         backend=None,
#         dir_mapper=None,
#         ctx=None,
#     ):
#         vals[":type"] = "delivery"
#         return super().synchro(
#             vals,
#             only_minimal=only_minimal,
#             ttl=ttl,
#             running_in_queue=running_in_queue,
#             jacket=jacket,
#             model_spec=model_spec,
#             backend=backend,
#             dir_mapper=dir_mapper,
#             ctx=ctx,
#         )
#
#
# class ResPartnerInvoice(models.Model):
#     _name = "res.partner.invoice"
#     _inherit = "res.partner"
#
#     CONTRAINTS = ["id", "!=", "parent_id"]
#
#     vg7_id = fields.Integer("VG7 ID", copy=False)
#
#     @api.model
#     def synchro(
#         self,
#         vals,
#         only_minimal=True,
#         ttl=None,
#         running_in_queue=None,
#         jacket=None,
#         model_spec=False,
#         backend=None,
#         dir_mapper=None,
#         ctx=None,
#     ):
#         vals[":type"] = "invoice"
#         return super().synchro(
#             vals,
#             only_minimal=only_minimal,
#             ttl=ttl,
#             running_in_queue=running_in_queue,
#             jacket=jacket,
#             model_spec=model_spec,
#             backend=backend,
#             dir_mapper=dir_mapper,
#             ctx=ctx,
#         )
#
#
# class ResPartnerSupplier(models.Model):
#     _name = "res.partner.supplier"
#     _inherit = "res.partner"
#
#     vg72_id = fields.Integer("VG7 ID", copy=False)
