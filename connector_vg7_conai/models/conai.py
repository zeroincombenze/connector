# -*- coding: utf-8 -*-
#
# Copyright 2018-19 - SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
import logging

from odoo import api, fields, models

# from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class ItalyConaiProductCategory(models.Model):
    _inherit = 'italy.conai.product.category'

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo7 ID', copy=False)
    oe10_id = fields.Integer('Odoo7 ID', copy=False)

    CONTRAINTS = []

    @api.model_cr_context
    def _auto_init(self):
        res = super(ItalyConaiProductCategory, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.model
    def synchro(self, vals, disable_post=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post)


class ItalyConaiPartnerCategory(models.Model):
    _inherit = 'italy.conai.partner.category'

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo7 ID', copy=False)
    oe10_id = fields.Integer('Odoo7 ID', copy=False)

    CONTRAINTS = []

    @api.model_cr_context
    def _auto_init(self):
        res = super(ItalyConaiPartnerCategory, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.model
    def synchro(self, vals, disable_post=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post)
