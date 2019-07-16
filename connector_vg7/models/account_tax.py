# -*- coding: utf-8 -*-
# Copyright 2019 Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from odoo import fields, models, api
from odoo.exceptions import UserError
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
        for partner in self:
            partner.dim_name = self.env[
                'ir.model.synchro'].dim_text(partner.name)

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    dim_name = fields.Char('Search Key',
                           compute=_set_dim_name,
                           store=True,
                           readonly=True)

    CONTRAINTS = []

    @api.model_cr_context
    def _auto_init(self):
        res = super(AccountTax, self)._auto_init()
        for prefix in ('vg7', 'oe7'):
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
    def synchro(self, vals):
        return self.env['ir.model.synchro'].synchro(self, vals)
