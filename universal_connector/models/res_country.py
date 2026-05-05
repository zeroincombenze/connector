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

from odoo import api, models

_logger = logging.getLogger(__name__)


class ResCountry(models.Model):
    _name = "res.country"
    _inherit = ["res.country", "abstract.db.key"]

    @api.model_cr_context
    def _auto_init(self):
        res = super(ResCountry, self)._auto_init()
        for prefix in ("vg7", "oe7", "oe8", "oe10"):
            self.env["ir.model.synchro"]._build_unique_index(self._inherit, prefix)
        return res

    @api.multi
    def pull_record(self):
        self.env["ir.model.synchro"].pull_record(self)


class ResCountryState(models.Model):
    _name = "res.country.state"
    _inherit = ["res.country.state", "abstract.db.key"]

    @api.model_cr_context
    def _auto_init(self):
        res = super(ResCountryState, self)._auto_init()
        for prefix in ("vg7", "oe7", "oe8", "oe10"):
            self.env["ir.model.synchro"]._build_unique_index(self._inherit, prefix)
        return res
