# -*- coding: utf-8 -*-
#
# Copyright 2019-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import re
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

try:
    from unidecode import unidecode
except ImportError as err:
    _logger.debug(err)

RE_NAME_2_UTYPE = {
    'Acq': 'account.data_account_type_expenses',
    'Banc(a|he|k)': 'account.data_account_type_liquidity',
    'Canoni': 'account.data_account_type_expenses',
    'Cash': 'account.data_account_type_liquidity',
    '.*Cassa': 'account.data_account_type_liquidity',
    'Clienti': 'account.data_account_type_receivable',
    'Crediti.*soci': 'account.data_account_type_receivable',
    'Crediti.*[Cc]lienti': 'account.data_account_type_receivable',
    'Customer': 'account.data_account_type_receivable',
    'Debiti.*[Cc]lienti': 'account.data_account_type_payable',
    'Debiti.*[Ff]ornitori': 'account.data_account_type_payable',
    '.*Immobilizzazioni': 'account.data_account_type_fixed_assets',
    'Impianto.*Ampliamento': 'account.data_account_type_non_current_assets',
    'Effetti': 'account.data_account_type_receivable',
    'FA': 'account.data_account_type_current_liabilities',
    'Fondo': 'account.data_account_type_current_liabilities',
    'Fornitori': 'account.data_account_type_payable',
    'IVA': 'account.data_account_type_current_liabilities',
    'Purchase': 'account.data_account_type_expenses',
    'QA': 'account.data_account_type_depreciation',
    'Ricavi': 'account.data_account_type_revenue',
    'Rimb.*[Ss]pese': 'account.data_account_type_other_income',
    'Risconti': 'account.data_account_type_prepayments',
    'Supplier': 'account.data_account_type_payable',
    'Tass(a|e)': 'account.data_account_type_current_liabilities',
    '': 'account.data_account_type_revenue',
}

RE_NAME_2_TTYPE = {
    'Banc(a|he|k)': 'liquidity',
    'Cash': 'liquidity',
    'Cassa': 'liquidity',
    'Crediti': 'receivable',
    'Debiti': 'payable',
    'Payable': 'payable',
    'Receivable': 'receivable',
    '': 'other',
}

class AccountAccount(models.Model):
    _inherit = "account.account"

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
        res = super(AccountAccount, self)._auto_init()
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

    def search_4_type(self, vals, rec):
        """Account type is changed across Odoo versions
        account.account:
            -8.0 | user_type | type
                type: receivable,payable,liquidity,other,view
            9-0+ | user_type_id | internal_type
                internal_type: receivable,payable,liquidity,other

        account.account.type:
            -8.0 | code | report_type
                report_type: asset,liability,income,expense,none
            9.0+ | name | type
                type: receivable,payable,liquidity,other

        convertion table:
        -8.0 (code/name)      | 9.0+ (name)
        receivable/Receivable   Receivable
        payable/Payable         Payable
        bank/Bank               Bank and Cash
        cash/Cash               ^^^
        check/Check             Credit Card
        asset/Asset             Current Assets
        ^^^                     Non-current Assets
        ^^^                     Fixed Asset
        liability/Liability     Current Liabilities
        ^^^                     Non-current Liabilities
        tax/Tax                 ^^^
        income/Income           Income
        ^^^                     Other Income
        expense/Expense         Expenses
        ^^^                     Depreciation
        ^^^                     Cost of Revenue
        ^^^                     Prepayments
        ^^^                     Current Year Earnings
        equity/Equity           Equity
        view/*
        """
        name = vals.get('name')
        if (name and
                (not vals.get('user_type_id') or
                 vals['user_type_id'] == self.env.ref(
                            'account.data_account_type_receivable')) and
                (not rec or
                 (rec and
                  (not rec.user_type_id or
                   rec.user_type_id == self.env.ref(
                              'account.data_account_type_receivable'))))):
            vals['user_type_id'] = self.env.ref(RE_NAME_2_UTYPE['']).id
            for regex in RE_NAME_2_UTYPE:
                if re.search(regex, name):
                    vals['user_type_id'] = self.env.ref(
                        RE_NAME_2_UTYPE[regex]).id
                    break
        elif not rec:
            vals['user_type_id'] = self.env.ref(RE_NAME_2_UTYPE['']).id
        return vals

    def assure_values(self, vals, rec):
        # actual_model = 'account.account'
        if not vals.get('user_type_id'):
            vals = self.search_4_type(vals, rec)
        if vals.get('user_type_id'):
            type_id = int(vals['user_type_id'])
            cls_type = self.env['account.account.type']
            if cls_type.search([('id', '=', type_id)]):
                acct = cls_type.browse(type_id)
            else:
                acct = cls_type.search([])[0]
        elif rec and rec.user_type_id:
            acct = rec.user_type_id
        if (acct.type in ('payable', 'receivable') and
                (not rec or not rec.reconcile)):
            vals['reconcile'] = True
        return vals

    @api.model
    def synchro(self, vals, disable_post=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post)

    @api.multi
    def pull_record(self):
        self.env['ir.model.synchro'].pull_record(self)


class AccountAccountType(models.Model):
    _inherit = "account.account.type"

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
        res = super(AccountAccountType, self)._auto_init()
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

    def assure_values(self, vals, rec):
        # actual_model = 'account.account.type'
        if not vals.get('type') and not rec:
            name = vals.get('name', '')
            if (name.find('Bank') >= 0 or name.find('Card') >= 0 or
                    name.find('Banc') >= 0 or name.find('Cart') >= 0):
                vals['type'] = 'liquidity'
            elif name.find('Payable') >= 0 or name.find('Debiti') >= 0:
                vals['type'] = 'payable'
            elif name.find('Receivable') >= 0 or name.find('Crediti') >= 0:
                vals['type'] = 'receivable'
            else:
                vals['type'] = 'other'
        return vals

    @api.model
    def synchro(self, vals, disable_post=None):
        if 'type' in vals:
            del vals['type']
        return self.env['ir.model.synchro'].synchro(self, vals)
