# -*- coding: utf-8 -*-
# Copyright 2019 Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from odoo import fields, models, api
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    original_state = fields.Char('Original Status')

    CONTRAINTS = []
    DEFAULT = {}

    @api.model_cr_context
    def _auto_init(self):
        res = super(SaleOrder, self)._auto_init()
        for prefix in ('vg7', 'oe7'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.model
    def synchro(self, vals):
        return self.env['ir.model.synchro'].synchro(self, vals)

    @api.model
    def commit(self, id):
        return self.env['ir.model.synchro'].commit(self, id)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    to_delete = fields.Boolean('Record to delete')

    CONTRAINTS = []

    @api.model_cr_context
    def _auto_init(self):
        res = super(SaleOrderLine, self)._auto_init()
        for prefix in ('vg7', 'oe7'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.model
    def synchro(self, vals):
        return self.env['ir.model.synchro'].synchro(self, vals)
