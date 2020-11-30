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


class AccountTax(models.Model):
    _inherit = "account.tax"

    @api.multi
    @api.depends('name')
    def _set_dim_name(self):
        for tax in self:
            tax.dim_name = self.env[
                'ir.model.synchro'].dim_text(tax.name)

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)
    dim_name = fields.Char('Search Key',
                           compute=_set_dim_name,
                           store=True,
                           readonly=True)
    timestamp = fields.Datetime('Timestamp', copy=False, readonly=True)
    errmsg = fields.Char('Error message', copy=False, readonly=True)

    @api.model_cr_context
    def _auto_init(self):
        res = super(AccountTax, self)._auto_init()
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
        if ('type_tax_use' not in vals and
                self.env['synchro.channel'].browse(
                    channel_id).identity == 'vg7'):
            vals['type_tax_use'] = 'sale'
        return vals, ''

    def assure_values(self, vals, rec):
        if not vals.get('amount'):
            if rec:
                vals['amount'] = rec.amount
            else:
                vals['amount'] = 0
        return vals

    @api.model
    def synchro(self, vals, disable_post=None,
                only_minimal=None, no_deep_fields=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post,
            only_minimal=only_minimal, no_deep_fields=no_deep_fields)
