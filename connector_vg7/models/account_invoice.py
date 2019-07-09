# -*- coding: utf-8 -*-
# Copyright 2019 Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from odoo import fields, models, api
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    original_state = fields.Char('Original Status')

    SKEYS = (['number'])
    CONTRAINTS = []
    KEEP = []
    DEFAULT = {
        'journal_id': '',
        'type': 'out_invoice',
    }
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

    SKEYS = (['invoice_id', 'sequence'])
    CONTRAINTS = []
    KEEP = []
    DEFAULT = {
        'account_id': '',
        'uom_id': '',
        'invoice_line_tax_ids': '',
    }
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
        return self.env['ir.model.synchro'].synchro(self, vals)
