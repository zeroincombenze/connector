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


class AccountPaymentTerm(models.Model):
    _name = "account.payment.term"
    _inherit = ["account.payment.term", "abstract.db.key"]

    @api.multi
    @api.depends("name")
    def _set_dim_name(self):
        for payment in self:
            payment.dim_name = self.env["ir.model.synchro.cache"].hashname(payment.name)

    dim_name = fields.Char(
        "Search Key", compute=_set_dim_name, store=True, readonly=True
    )

    @api.model_cr_context
    def _auto_init(self):
        res = super(AccountPaymentTerm, self)._auto_init()
        for prefix in ("vg7", "oe7", "oe8", "oe10"):
            self.env["ir.model.synchro"]._build_unique_index(self._inherit, prefix)
        return res

    @api.model
    def preprocess(self, backend_id, vals):
        if "vg7:date_scadenza" in vals:
            num_dues = len(vals["vg7:date_scadenza"])
            if num_dues:
                rate = 100.0 / num_dues
            else:
                rate = 100.0
            child_vals = []
            for num, line in enumerate(vals["vg7:date_scadenza"]):
                # First Odoo sequence is 9
                seq = num + 9
                line_vals = {}
                for item in line:
                    line_vals["vg7:%s" % item] = line[item]
                line_vals[":sequence"] = seq
                if seq == num_dues:
                    line_vals[":value"] = "balance"
                else:
                    line_vals[":value"] = "percent"
                    line_vals[":value_amount"] = rate
                child_vals.append(line_vals)
            vals["vg7:date_scadenza"] = child_vals
        return vals, ""


class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    vg7_id = fields.Integer("VG7 ID", copy=False)
    oe7_id = fields.Integer("Odoo7 ID", copy=False)
    oe8_id = fields.Integer("Odoo8 ID", copy=False)
    oe10_id = fields.Integer("Odoo10 ID", copy=False)
    to_delete = fields.Boolean("Record to delete")

    CONTRAINTS = []
    PARENT_ID_NAME = "payment_id"

    @api.model_cr_context
    def _auto_init(self):
        res = super(AccountPaymentTermLine, self)._auto_init()
        for prefix in ("vg7", "oe7", "oe8", "oe10"):
            self.env["ir.model.synchro"]._build_unique_index(self._inherit, prefix)
        return res
