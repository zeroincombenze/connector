# -*- coding: utf-8 -*-
#
# Copyright 2019-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResLang(models.Model):
    _inherit = "res.lang"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)

    @api.model
    def synchro(self, vals, disable_post=None,
                only_minimal=None, no_deep_fields=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post,
            only_minimal=only_minimal, no_deep_fields=no_deep_fields)
