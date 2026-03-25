# -*- coding: utf-8 -*-
#
# Copyright 2019-26 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
# import re
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

try:
    from unidecode import unidecode
except ImportError as err:
    _logger.debug(err)


# RE_NAME_2_UTYPE = {
#     "Acq": "account.data_account_type_expenses",
#     "Banc(a|he|k)": "account.data_account_type_liquidity",
#     "Canoni": "account.data_account_type_expenses",
#     "Cash": "_account.data_account_type_liquidity",
#     ".*Cassa": "_account.data_account_type_liquidity",
#     "Clienti": "account.data_account_type_receivable",
#     "Crediti.*soci": "account.data_account_type_receivable",
#     "Crediti.*[Cc]lienti": "account.data_account_type_receivable",
#     "Customer": "account.data_account_type_receivable",
#     "Debiti.*[Cc]lienti": "account.data_account_type_payable",
#     "Debiti.*[Ff]ornitori": "account.data_account_type_payable",
#     ".*Immobilizzazioni": "account.data_account_type_fixed_assets",
#     "Impianto.*Ampliamento": "account.data_account_type_non_current_assets",
#     "Effetti": "account.data_account_type_receivable",
#     "FA": "account.data_account_type_current_liabilities",
#     "Fondo": "account.data_account_type_current_liabilities",
#     "Fornitori": "account.data_account_type_payable",
#     "IVA": "account.data_account_type_current_liabilities",
#     "Purchase": "account.data_account_type_expenses",
#     "QA": "account.data_account_type_depreciation",
#     "Ricavi": "account.data_account_type_revenue",
#     "Rimb.*[Ss]pese": "account.data_account_type_other_income",
#     "Risconti": "account.data_account_type_prepayments",
#     "Supplier": "account.data_account_type_payable",
#     "Tass(a|e)": "account.data_account_type_current_liabilities",
#     "": "account.data_account_type_revenue",
# }
#
#
# RE_TYPE_NAME_ID = {
#     "Receivable": "account.data_account_type_receivable",
#     "Credit[oi]( client[ei])?": "account.data_account_type_receivable",
#     "Payable": "account.data_account_type_payable",
#     "Debit[oi]( fornitor[ei])?": "account.data_account_type_payable",
#     "Bank and Cash": "account.data_account_type_liquidity",
#     "Cas(h|sa)": "_account.data_account_type_liquidity",
#     "Ban(a|he|k)( [eo] [Cc]assa)?": "account.data_account_type_liquidity",
#     "Credit Card": "account.data_account_type_credit_card",
#     "Carta di credito": "account.data_account_type_credit_card",
#     "Current Assets?": "account.data_account_type_current_assets",
#     "Assets?": "account.data_account_type_current_assets",
#     "Attività( correnti)?": "account.data_account_type_current_assets",
#     "Non-current Assets?": "account.data_account_type_non_current_assets",
#     "Attività non correnti": "account.data_account_type_non_current_assets",
#     "Prepayments": "account.data_account_type_prepayments",
#     "Risconti": "account.data_account_type_prepayments",
#     "Fixed Assets?": "account.data_account_type_fixed_assets",
#     "Immobilizzazioni": "account.data_account_type_fixed_assets",
#     "Current Liabilities": "account.data_account_type_current_liabilities",
#     "Liability": "account.data_account_type_current_liabilities",
#     "Passività( correnti)?": "account.data_account_type_current_liabilities",
#     "Non-current Liabilities?": "account.data_account_type_non_current_liabilities",
#     "Passività non correnti": "account.data_account_type_non_current_liabilities",
#     "Equity": "account.data_account_type_equity",
#     "Capitale": "account.data_account_type_equity",
#     "Current Year Earnings": "account.data_unaffected_earnings",
#     "Risultato operativo": "account.data_unaffected_earnings",
#     "Other Income": "account.data_account_type_other_income",
#     "Altri ricavi operativi": "account.data_account_type_other_income",
#     "Income": "account.data_account_type_revenue",
#     "Ricav[oi]": "account.data_account_type_revenue",
#     "Depreciation": "account.data_account_type_depreciation",
#     "Ammortamento": "account.data_account_type_depreciation",
#     "Costi": "account.data_account_type_expenses",
#     "Expenses?": "account.data_account_type_expenses",
#     "Cost of Revenue": "account.data_account_type_direct_costs",
#     "Costi operativi": "account.data_account_type_direct_costs",
# }


class AccountAccount(models.Model):
    _inherit = "account.account"

    @api.multi
    @api.depends("name")
    def _set_dim_name(self):
        for partner in self:
            partner.dim_name = self.env["ir.model.synchro"].dim_text(partner.name)

    vg7_id = fields.Integer("VG7 ID", copy=False)
    oe7_id = fields.Integer("Odoo7 ID", copy=False)
    oe8_id = fields.Integer("Odoo8 ID", copy=False)
    oe10_id = fields.Integer("Odoo10 ID", copy=False)
    dim_name = fields.Char(
        "Search Key", compute=_set_dim_name, store=True, readonly=True
    )
    timestamp = fields.Datetime("Timestamp", copy=False, readonly=True)
    errmsg = fields.Char("Error message", copy=False, readonly=True)

    @api.model_cr_context
    def _auto_init(self):
        res = super(AccountAccount, self)._auto_init()
        for prefix in ("vg7", "oe7", "oe8", "oe10"):
            self.env["ir.model.synchro"]._build_unique_index(self._inherit, prefix)
        return res

    def wep_text(self, text):
        if text:
            return unidecode(text).strip()
        return text

    def dim_text(self, text):
        text = self.wep_text(text)
        if text:
            res = ""
            for ch in text:
                if ch.isalnum():
                    res += ch.lower()
            text = res
        return text
