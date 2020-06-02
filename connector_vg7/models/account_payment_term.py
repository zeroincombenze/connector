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

try:
    from unidecode import unidecode
except ImportError as err:
    _logger.debug(err)
try:
    from os0 import os0
except ImportError as err:
    _logger.error(err)


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    @api.multi
    @api.depends('name')
    def _set_dim_name(self):
        for partner in self:
            partner.dim_name = self.env[
                'ir.model.synchro'].dim_text(partner.name)

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)
    dim_name = fields.Char('Search Key',
                           compute=_set_dim_name,
                           store=True,
                           readonly=True)

    CONTRAINTS = []

    @api.model_cr_context
    def _auto_init(self):
        res = super(AccountPaymentTerm, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    def wep_text(self, text):
        if text:
            return unidecode(text).strip()
        return text

    def dim_text(self, text):
        text = self.wep_text(text)
        if text:
            res = ''
            for ch in text:
                if ch.isalnum():
                    res += ch.lower()
            text = res
        return text

    @api.model
    def preprocess(self, channel_id, vals):
        self.env['ir.model.synchro'].logmsg('debug',
            '>>> account.payment.term.preprocess()')
        cache = self.env['ir.model.synchro.cache']
        if 'vg7:date_scadenza' in vals:
            num_dues = len(vals['vg7:date_scadenza'])
            if num_dues:
                rate = 100.0 / num_dues
            else:
                rate = 100.0
            child_vals = []
            for num, line in enumerate(vals['vg7:date_scadenza']):
                seq = num + 1
                line_vals = {}
                for item in line:
                    line_vals['vg7:%s' % item] = line[item]
                line_vals[':sequence'] = seq
                if seq == num_dues:
                    line_vals[':value'] = 'balance'
                else:
                    line_vals[':value'] = 'percent'
                    line_vals[':value_amount'] = rate
                child_vals.append(line_vals)
            vals['vg7:date_scadenza'] = child_vals
        return vals, ''

    def postprocess(self, channel_id, parent_id, vals):
        # _logger.info(
        #     '> postprocess(%d,%s)' % (parent_id, vals))  # debug
        return False

    @api.model
    def synchro(self, vals, disable_post=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post)


class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)
    to_delete = fields.Boolean('Record to delete')

    CONTRAINTS = []
    PARENT_ID = 'payment_id'

    @api.model_cr_context
    def _auto_init(self):
        res = super(AccountPaymentTermLine, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.model
    def synchro(self, vals, disable_post=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post)
