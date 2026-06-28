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


class AccountTax(models.Model):
    _name = "account.tax"
    _inherit = ["account.tax", "abstract.db.key"]

    @api.multi
    @api.depends("name")
    def _set_dim_name(self):
        for tax in self:
            tax.dim_name = self.env["ir.model.synchro.cache"].hashname(tax.name)

    dim_name = fields.Char(
        "Search Key", compute=_set_dim_name, store=True, readonly=True
    )

    @api.model_cr_context
    def _auto_init(self):
        res = super(AccountTax, self)._auto_init()
        for prefix in ("vg7", "oe7", "oe8", "oe10"):
            self.env["ir.model.synchro"]._build_unique_index(self._inherit, prefix)
        return res

    @api.model
    def preprocess(self, backend, vals):
        if (
            "type_tax_use" not in vals
            and backend.identity == "vg7"
        ):
            vals["type_tax_use"] = "sale"
        return vals, ""

    def assure_values(self, vals, rec):
        if not vals.get("amount"):
            vals["amount"] = rec.amount if rec else 0
        return vals
