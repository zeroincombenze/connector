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


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    vg72_id = fields.Integer('VG7 ID (2.nd)', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)

    @api.model_cr_context
    def _auto_init(self):
        res = super(ResPartnerBank, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.model
    def preprocess(self, channel_id, vals):
        """
        Odoo                      Counterpart   Fields
        res.partner.bank          bank          description, IBAN, customer_id
        res.partner.bank.company  bank_accounts bank, iban, id_odoo
        """
        if 'id_odoo' in vals:
            return vals, 'company'
        return vals, ''

    @api.multi
    def pull_record(self):
        self.env['ir.model.synchro'].pull_record(self)


class ResPartnerBankCompany(models.Model):
    _name = "res.partner.bank.company"
    _inherit = "res.partner.bank"

    @api.model
    def synchro(self, vals, disable_post=None,
                only_minimal=None, no_deep_fields=None):
        if not disable_post:
            vals[':type'] = 'company'
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post,
            only_minimal=only_minimal, no_deep_fields=no_deep_fields)

    @api.multi
    def pull_record(self):
        self.env['ir.model.synchro'].pull_record(self)
