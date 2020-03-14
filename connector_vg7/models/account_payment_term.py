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
        _logger.info(
            '> preprocess(%s)' % vals)
        cache = self.env['ir.model.synchro.cache']
        if 'vg7:date_scadenza' in vals:
            for num, line in enumerate(vals['vg7:date_scadenza']):
                line_vals = {}
                for item in line:
                    line_vals['vg7:%s' % item] = line[item]
                if (line_vals.get('vg7:scadenza') and
                        int(line_vals.get('vg7:fine_mese'))):
                    if (int(line_vals['vg7:scadenza']) % 30) == 0:
                        line_vals['vg7:scadenza'] = int(line_vals['vg7:scadenza']) - 2
                cache.set_model_attr(
                    channel_id, 'account.payment.term.line', '%d' % num,
                    line_vals)
            del vals['vg7:date_scadenza']
        return vals, ''

    def postprocess(self, channel_id, parent_id, vals):
        _logger.info(
            '> postprocess(%d,%s)' % (parent_id, vals))  # debug
        cache = self.env['ir.model.synchro.cache']
        model = 'account.payment.term.line'
        cls = self.env[model]
        num = 0
        while 1:
            kk = '%d' % num
            if not cache.get_model_attr(channel_id, model, kk):
                break
            vals = {}
            for field in cache.get_model_attr(channel_id, model, kk):
                vals[field] = cache.get_model_attr(
                    channel_id, model, kk)[field]
            vals['parent_id'] = parent_id
            cache.del_model_attr(channel_id, model, kk)
            self.env['ir.model.synchro'].synchro(
                cls, vals, disable_post=True)
            num += 1

    @api.model
    def synchro(self, vals, disable_post=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post)
