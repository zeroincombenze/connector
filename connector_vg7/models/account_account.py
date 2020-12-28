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
    'Cash': '_account.data_account_type_liquidity',
    '.*Cassa': '_account.data_account_type_liquidity',
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


RE_TYPE_NAME_ID = {
    'Receivable': 'account.data_account_type_receivable',
    'Credit[oi]( client[ei])?': 'account.data_account_type_receivable',
    'Payable': 'account.data_account_type_payable',
    'Debit[oi]( fornitor[ei])?': 'account.data_account_type_payable',
    'Bank and Cash': 'account.data_account_type_liquidity',
    'Cas(h|sa)': '_account.data_account_type_liquidity',
    'Ban(a|he|k)( [eo] [Cc]assa)?': 'account.data_account_type_liquidity',
    'Credit Card': 'account.data_account_type_credit_card',
    'Carta di credito': 'account.data_account_type_credit_card',
    'Current Assets?': 'account.data_account_type_current_assets',
    'Assets?': 'account.data_account_type_current_assets',
    'Attività( correnti)?': 'account.data_account_type_current_assets',
    'Non-current Assets?': 'account.data_account_type_non_current_assets',
    'Attività non correnti': 'account.data_account_type_non_current_assets',
    'Prepayments': 'account.data_account_type_prepayments',
    'Risconti': 'account.data_account_type_prepayments',
    'Fixed Assets?': 'account.data_account_type_fixed_assets',
    'Immobilizzazioni': 'account.data_account_type_fixed_assets',
    'Current Liabilities': 'account.data_account_type_current_liabilities',
    'Liability': 'account.data_account_type_current_liabilities',
    'Passività( correnti)?': 'account.data_account_type_current_liabilities',
    'Non-current Liabilities?':
        'account.data_account_type_non_current_liabilities',
    'Passività non correnti':
        'account.data_account_type_non_current_liabilities',
    'Equity': 'account.data_account_type_equity',
    'Capitale': 'account.data_account_type_equity',
    'Current Year Earnings': 'account.data_unaffected_earnings',
    'Risultato operativo': 'account.data_unaffected_earnings',
    'Other Income': 'account.data_account_type_other_income',
    'Altri ricavi operativi': 'account.data_account_type_other_income',
    'Income': 'account.data_account_type_revenue',
    'Ricav[oi]': 'account.data_account_type_revenue',
    'Depreciation': 'account.data_account_type_depreciation',
    'Ammortamento': 'account.data_account_type_depreciation',
    'Costi': 'account.data_account_type_expenses',
    'Expenses?': 'account.data_account_type_expenses',
    'Cost of Revenue': 'account.data_account_type_direct_costs',
    'Costi operativi': 'account.data_account_type_direct_costs',
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
    timestamp = fields.Datetime('Timestamp', copy=False, readonly=True)
    errmsg = fields.Char('Error message', copy=False, readonly=True)

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
            self.env['ir.model.synchro'].logmsg('warning',
                '### Undefined account user type', model='account.account')
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
    def synchro(self, vals, disable_post=None, no_deep_fields=None,
                only_minimal=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post,
            no_deep_fields=no_deep_fields, only_minimal=only_minimal)

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

    @api.model_cr_context
    def _auto_init(self):
        res = super(AccountAccountType, self)._auto_init()
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

    def get_id_from_ref(self, vals):
        name = vals.get('name', '')
        ref_id = type_name = False
        if name:
            for regex in RE_TYPE_NAME_ID:
                if re.search(regex, name):
                    type_name = RE_TYPE_NAME_ID[regex]
                    if not type_name.startswith('_'):
                        ref_id = self.env.ref(type_name).id
                    break
        return ref_id, type_name

    def assure_values(self, vals, rec):
        # actual_model = 'account.account.type'
        if not vals.get('name') and rec:
            vals['name'] = rec.name
        ref_id, type_name = self.get_id_from_ref(vals)
        if type_name:
            if type_name == 'account.data_account_type_receivable':
                vals['type'] = 'receivable'
            elif type_name == 'account.data_account_type_payable':
                vals['type'] = 'payable'
            elif type_name in ('account.data_account_type_liquidity',
                               '_account.data_account_type_liquidity',
                               'account.data_account_type_credit_card'):
                vals['type'] = 'liquidity'
            else:
                vals['type'] = 'other'
        if 'type' not in vals:
            self.env['ir.model.synchro'].logmsg('warning',
                '### Undefined account type', model='account.account.type')
            if not rec:
                vals['type'] = 'other'
        return vals

    @api.model
    def synchro(self, vals, disable_post=None, no_deep_fields=None,
                only_minimal=None):
        if 'type' in vals:
            del vals['type']
        return self.env['ir.model.synchro'].synchro(self, vals,
            disable_post=disable_post,
            no_deep_fields=no_deep_fields, only_minimal=only_minimal)
