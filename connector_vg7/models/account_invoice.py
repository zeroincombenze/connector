# -*- coding: utf-8 -*-
#
# Copyright 2018-19 - SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    original_state = fields.Char('Original Status')

    CONTRAINTS = []
    LINES_OF_REC = 'invoice_line_ids'
    LINE_MODEL = 'account.invoice.line'

    @api.model_cr_context
    def _auto_init(self):
        res = super(AccountInvoice, self)._auto_init()
        for prefix in ('vg7', 'oe7'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.model
    def set_defaults(self):
        for nm in ('payment_term_id',
                   'fiscal_position_id'):
            if nm == 'fiscal_position_id':
                partner_nm = 'property_account_position_id'
            else:
                partner_nm = 'property_%s' % nm
            if not getattr(self, nm):
                setattr(self, nm, getattr(self.partner_id, partner_nm))
        for nm in ('goods_description_id',
                   'carriage_condition_id',
                   'transportation_reason_id',
                   'transportation_method_id'):
            if hasattr(self, nm) and not getattr(self, nm):
                setattr(self, nm, getattr(self.partner_id, nm))

    @api.model
    def synchro(self, vals):
        return self.env['ir.model.synchro'].synchro(self, vals)

    @api.model
    def commit(self, id):
        return self.env['ir.model.synchro'].commit(self, id)


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    to_delete = fields.Boolean('Record to delete')

    CONTRAINTS = []
    PARENT_ID = 'invoice_id'

    @api.model_cr_context
    def _auto_init(self):
        res = super(AccountInvoiceLine, self)._auto_init()
        for prefix in ('vg7', 'oe7'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.model
    def synchro(self, vals):
        if 'id' in vals:
            del vals['id']
        return self.env['ir.model.synchro'].synchro(self, vals)
