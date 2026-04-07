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


class SaleOrder(models.Model):
    _inherit = "sale.order"

    vg7_id = fields.Integer("VG7 ID", copy=False)
    oe7_id = fields.Integer("Odoo7 ID", copy=False)
    oe8_id = fields.Integer("Odoo8 ID", copy=False)
    oe10_id = fields.Integer("Odoo10 ID", copy=False)
    original_state = fields.Char("Original Status", copy=False)
    timestamp = fields.Datetime("Timestamp", copy=False, readonly=True)
    errmsg = fields.Char("Error message", copy=False, readonly=True)

    @api.model_cr_context
    def _auto_init(self):
        res = super(SaleOrder, self)._auto_init()
        for prefix in ("vg7", "oe7", "oe8", "oe10"):
            self.env["ir.model.synchro"]._build_unique_index(self._inherit, prefix)
        return res

    @api.model
    def set_defaults(self):
        for nm in ("pricelist_id", "payment_term_id", "fiscal_position_id"):
            if nm == "fiscal_position_id":
                partner_nm = "property_account_position_id"
            else:
                partner_nm = "property_%s" % nm
            if not getattr(self, nm):
                setattr(self, nm, getattr(self.partner_id, partner_nm))
        for nm in (
            "goods_description_id",
            "carriage_condition_id",
            "transportation_reason_id",
            "transportation_method_id",
        ):
            if hasattr(self, nm) and not getattr(self, nm):
                setattr(self, nm, getattr(self.partner_id, nm))
        for nm in ("partner_invoice_id", "partner_shipping_id"):
            if not getattr(self, nm):
                setattr(self, nm, self.partner_id.id)
        nm = "note"
        partner_nm = "sale_note"
        if not getattr(self, nm):
            setattr(self, nm, getattr(self.company_id, partner_nm))

    def assure_values(self, vals, rec):
        for nm in ("partner_shipping_id", "partner_invoice_id"):
            if isinstance(vals.get(nm), int) and vals[nm] <= 0:
                del vals[nm]
            if not vals.get(nm) and not rec and vals.get('partner_id'):
                vals[nm] = vals["partner_id"]
        return vals

    @api.model
    def commit(self, id):
        return self.env["ir.model.synchro"].commit(self, id)

    @api.model
    def synchro(self, vals, chk_in_queue=None, only_minimal=None, no_deep_fields=None,
                no_del_child=False):
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


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    vg7_id = fields.Integer("VG7 ID", copy=False)
    oe7_id = fields.Integer("Odoo7 ID", copy=False)
    oe8_id = fields.Integer("Odoo8 ID", copy=False)
    oe10_id = fields.Integer("Odoo10 ID", copy=False)
    to_delete = fields.Boolean("Record to delete")

    @api.model_cr_context
    def _auto_init(self):
        res = super(SaleOrderLine, self)._auto_init()
        for prefix in ("vg7", "oe7", "oe8", "oe10"):
            self.env["ir.model.synchro"]._build_unique_index(self._inherit, prefix)
        return res

    def assure_values(self, vals, rec):
        nm = "product_id"
        if (not isinstance(vals.get(nm), int) or not vals.get(nm)) and not rec:
            product = self.env["ir.model.synchro.apply"].get_default_product()
            if product:
                vals[nm] = product.id
        if not vals.get("price_unit") and not rec:
            vals["price_unit"] = 0.0
        return vals

    @api.model
    def synchro(self, vals, chk_in_queue=None, only_minimal=None, no_deep_fields=None,
                no_del_child=False):
        return self.env["ir.model.synchro"].synchro(
            self,
            vals,
            chk_in_queue=chk_in_queue,
            only_minimal=only_minimal,
            no_deep_fields=no_deep_fields,
            no_del_child=no_del_child,
        )
