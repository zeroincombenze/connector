#!/usr/bin/env python
# -*- coding: utf-8 -*-
# flake8: noqa
from __future__ import print_function, unicode_literals
from __future__ import division
from __future__ import absolute_import
from future import standard_library

standard_library.install_aliases()  # noqa: E402
from past.builtins import basestring
from builtins import *  # noqa
from builtins import input

import os
import sys
from datetime import date, datetime, timedelta
import time
from os0 import os0

try:
    from clodoo import clodoo
except ImportError:
    import clodoo
try:
    from z0lib.z0lib import z0lib
except ImportError:
    from z0lib import z0lib
# import pdb      # pylint: disable=deprecated-module

__version__ = "10.0.0.2.5"
ref_dt_today = date.today().strftime("%Y-%m-%d")
ref_dt_m_1 = (date.today() - timedelta(33)).strftime("%Y-%m-%d")
ref_dt_m_2 = (date.today() - timedelta(64)).strftime("%Y-%m-%d")
ref_ts_m_1 = "%s 12:34:56" % ref_dt_m_1

EXT_COMPANY_ID = 2
TEST_IBAN = "IT60X0542811101000000123456"
MODEL_WITH_CHILD = (
    "account.payment.term",
    "account.invoice",
    "account.move",
    "sale.order",
    "stock.picking.package.preparation",
)
MODEL_TO_COMMIT = (
    "account.invoice",
    "account.move",
    "sale.order",
    "stock.picking.package.preparation",
)
MODEL_WITH_COMPANY = (
    "account.account",
    "account.invoice",
    "account.invoice.line",
    "account.journal",
    "account.payment.term",
    "account.move",
    "account.move.line",
    "account.tax",
    "res.partner.bank",
    "sale.order",
    "sale.order.line",
    "stock.picking.package.preparation",
    "stock.picking.package.preparation.line",
)
CANDIDATE_KEYS = (
    "acc_number",
    "login",
    "default_code",
    "code",
    "key",
    "serial_number",
    "description",
    "comment",
    "name",
    "dim_name",
)
M2M_FIELDS = ("bank_ids", "tax_ids", "tax_id", "invoice_line_tax_ids")
M2O_FIELDS = ("product_uom", "payment_term")
STATUS_VALUE = {
    "vg7:order_state": {1: "draft", 2: "sale"},
    "vg7:state": True,
    "oe8:state": {"manual": "sale"},
}
UNCHECK_FIELDS = (
    "vg7:date_scadenza",
    "vg7:shipping",
    "vg7:billing",
    "vg7:surename",
    "vg7:name",
    "id",
    "vg7:street_number",
    "vg7:order_rows",
    "oe8:line_id",
    "oe8:line_ids",
    "oe8:order_line",
    "oe8:invoice_line",
    "oe8:invoice_line_ids",
    "vg7:order_id",
    "vg7:order_row_id",  ## TO remove
)
UNCHECK_MODEL_FIELDS = {
    "account.tax": ["vg7:description", "vg7:code"],
    "account.payment.term.line": ["oe8:days", "oe8:value"],  # TODO
}
UNCHECK_DRAFT_FIELDS = {
    "stock.picking.package.preparation.line": ["sale_id", "sale_line_id"]
}
WRONG_DATA = {
    "region": ["TO", "(TO)"],
    "street": ["", "Via Porta Vecchia"],
    "shipping_name": ["$", "Agro Latte Due s.n.c."],
    "name": ["CLIENTI", "Crediti v/clienti Italia"],
    "order_state": [2, 1],
    "product_name": ["Product Alpha", "Prodotto AA"],
    "customer_shipping_id": [12, -1],
    "description": ["RiBA 30GG/FM", "RB 30gg DFFM"],
}
FAILED_TRX = {
    "vg7:res.partner:wrong": {7: -7},
    "vg7:res.partner:None": {7: -7},
    "vg7:res.partner.shipping:None": {102: -7},
    # 'vg7:account.tax:only_amount': {101: -7, 115: -7},
}
# Default value to add before validation data
SOME_DEFAULT = {
    "res.country.state": [
        {
            "domain": ["code", "in", ["TO", "MI", "BO", "NA", "CE"]],
            "value": ["country_id", "res.country.IT"],
        }
    ],
    "product.product": [
        {
            "domain": ["default_code", "=~", "AA"],
            "value": [":product_tmpl_id", "product.template.A"],
        },
        {
            "domain": ["default_code", "=~", "BB"],
            "value": [":product_tmpl_id", "product.template.B"],
        },
        {
            "domain": ["default_code", "=~", "CC"],
            "value": [":product_tmpl_id", "product.template.C"],
        },
    ],
    "sale.order": [
        {"domain": ["id", "in", [131, 210]], "value": ["note", "company_note"]}
    ],
    "stock.picking.package.preparation": [
        {"domain": ["id", "=", 7], "value": ["state", "done"]}
    ],
}
SET_DEFAULT_FROM_CTX = {
    "res.country": [{"domain": ["code", "=", "IT"], "value": "res.country.IT"}],
    "product.template": [
        {"domain": ["default_code", "=~", "AA"], "value": "product.template.A"},
        {"domain": ["default_code", "=~", "BB"], "value": "product.template.B"},
        {"domain": ["default_code", "=~", "CC"], "value": "product.template.C"},
    ],
}
NAME_REFS = {
    "account.account.type": [
        {"domain": ["name", "=", "Receivable"], "value": ["name", "Crediti clienti"]},
        {"domain": ["name", "=", "Payable"], "value": ["name", "Debiti fornitori"]},
        {"domain": ["name", "=", "Bank and Cash"], "value": ["name", "Banca o cassa"]},
        {"domain": ["name", "=", "Credit Card"], "value": ["name", "Carta di Credito"]},
        {
            "domain": ["name", "=", "Current Assets"],
            "value": ["name", "Attività correnti"],
        },
        {
            "domain": ["name", "=", "Non-current Assets"],
            "value": ["name", "Attività non correnti"],
        },
        {"domain": ["name", "=", "Prepayments"], "value": ["name", "Risconti"]},
        {
            "domain": ["name", "=", "Fixed Assets"],
            "value": ["name", "Immobilizzazioni"],
        },
        {
            "domain": ["name", "=", "Current Liabilities"],
            "value": ["name", "Passività correnti"],
        },
        {
            "domain": ["name", "=", "Non-current Liabilities"],
            "value": ["name", "Passività non correnti"],
        },
        {"domain": ["name", "=", "Equity"], "value": ["name", "Capitale"]},
        {
            "domain": ["name", "=", "Current Year Earnings"],
            "value": ["name", "Risultato operativo"],
        },
        {"domain": ["name", "=", "Income"], "value": ["name", "Ricavi"]},
        {
            "domain": ["name", "=", "Other Income"],
            "value": ["name", "Altri ricavi operativi"],
        },
        {"domain": ["name", "=", "Depreciation"], "value": ["name", "Ammortamento"]},
        {"domain": ["name", "=", "Expenses"], "value": ["name", "Costi"]},
        {
            "domain": ["name", "=", "Cost of Revenue"],
            "value": ["name", "Costi operativi"],
        },
    ],
    "product.template": [
        {"domain": ["default_code", "=~", "AA"], "value": ["name", "Prodotto Alpha"]},
        {"domain": ["default_code", "=~", "BB"], "value": ["name", "Prodotto Beta"]},
        {"domain": ["default_code", "=~", "CC"], "value": ["name", "Prodotto Chi"]},
    ],
}

TNL_VG7_TABLES = {
    "account.account": "",
    "account.account.type": "",
    "account.invoice": "",
    "account.invoice.line": "",
    "account.payment.term": "payments",
    "account.payment.term.line": "",
    "account.tax": "tax_codes",
    # 'crm.team': '',
    "delivery.carrier": "couriers",
    "italy.conai.product.category": "conai",
    "italy.conai.partner.category": "esenzione_conai",
    "product.product": "products",
    "product.template": "",
    "product.uom": "ums",
    "res.currency": "",
    "res.country": "countries",
    "res.country.state": "regions",
    "res.partner": "customers",
    "res.partner.bank": "banks",
    "res.partner.bank.company": "bank_accounts",
    "res.partner.shipping": "customers_shipping_addresses",
    "res.partner.supplier": "suppliers",
    "stock.picking.package.preparation": "ddt",
    "stock.picking.package.preparation.line": "",
    "stock.picking.transportation_reason": "causals",
    "sale.order": "orders",
    "sale.order.line": "",
}
TNL_OE8_TABLES = {}
TNL_TEXT_2_M2 = {
    "country_id": {"Italia": "base.it"},
    "tax_id": {"22v": "z0bug.tax_22v"},
    "state_id": {"TORINO": "base.state_it_pe", "MILANO": "base.state_it_mi"},
}
TNL_VG7_DICT = {
    "account.account": {},
    "account.invoice": {"number": "move_name"},
    "account.invoice.line": {"partner_id": False, "vg7_partner_id": False},
    "account.payment.term": {"code": False, "description": "name"},
    "account.payment.term.line": {
        "scadenza": False,
        "fine_mese": False,
        "giorni_fine_mese": "payment_days",
    },
    "account.tax": {
        "aliquota": "amount",
        "code": ["name", "nounknown"],
        "description": ["name", "nounknown"],
    },
    "italy.conai.product.category": {
        "description": "name",
        "prezzo_unitario": "conai_price_unit",
    },
    "product.product": {
        "conai_id": "conai_category_id",
        "code": "default_code",
        "description": "name",
    },
    "product.template": {
        "conai_id": False,
        "code": "default_code",
        "description": "name",
    },
    "product.uom": {"code": "name"},
    "res.country": {"description": ["name", "nocase"]},
    "res.country.state": {"description": ["name", "nocase"]},
    "res.partner": {
        "bank_id": "bank_ids",
        "billing_pec": "pec_destinatario",
        "cf": "fiscalcode",
        "codice_univoco": "codice_destinatario",
        "company": "name",
        "country": "country_id",
        "customer_id": "parent_id",
        "customer_billing_id": "vg7_id",
        "customer_shipping_id": "vg7_id",
        "esonerato_fe": "electronic_invoice_subjected",
        "name": "firstname",
        "note": "invoice_warn_msg",
        "payment_id": "property_payment_term_id",
        "piva": "vat",
        "postal_code": "zip",
        "region": "state_id",
        "region_id": "state_id",
        "surename": "lastname",
        "tax_code_id": False,
        "telephone2": "mobile",
        "telephone": "phone",
        "street_number": False,
    },
    "res.partner.bank": {
        "IBAN": "acc_number",
        "customer_id": "partner_id",
        "description": False,
    },
    "sale.order": {
        "name": "client_order_ref",
        "date": "date_order",
        "order_number": ["name", "nounknown"],
        "customer_id": "partner_id",
        "payment_id": "payment_term_id",
        "customer_shipping_id": "partner_shipping_id",
        "courier_id": False,
        "agent_id": False,
        "order_state": "state",
    },
    "sale.order.line": {
        "product_name": "name",
        "unitary_price": "price_unit",
        "quantity": "product_uom_qty",
        "partner_id": False,
        "vg7_partner_id": False,
        "job_name": False,
    },
    "stock.picking.package.preparation": {
        "numero_colli": "parcels",
        "customer_id": "partner_id",
        "customer_shipping_id": "partner_shipping_id",
        "vettori_prima_riga": False,
        "voce_doganale": False,
        "aspetto_esteriore_dei_beni": "goods_description_id",
        "causal_id": "transportation_reason_id",
        "vettori_seconda_riga": False,
        "note": False,
        "peso_netto": False,
        "tipo_porto": False,
        "peso_lordo": False,
        "ora_ritiro": False,
        "data_emissione": "date",
        "data_ritiro": "date_done",
        "mezzo": False,
    },
    "stock.picking.package.preparation.line": {
        # 'ddt_id': 'package_preparation_id',
        "ddt_id": False,
        "descrizione": "name",
        "quantita": "product_uom_qty",
        "prezzo_unitario": "price_unit",
        "order_id": "sale_id",
        "order_row_id": "sale_line_id",
        "tax_code_id": "tax_ids",
        "product_id": False,
        "tax_id": False,
        "peso": "weight",
        "um": False,
        "um_id": "product_uom_id",
        # 'um_id': False,
        "conai_id": "conai_category_id",
    },
    "stock.picking.transportation_reason": {"code": False, "description": "name"},
}
TNL_OE8_DICT = {
    "account.account.type": {"code": False, "report_type": "type"},
    "account.account": {"user_type": "user_type_id"},
    "account.move": {"line_id": "line_ids"},
    "account.move.line": {"tax_code_id": "tax_ids", "tax_amount": False},
    "account.invoice": {
        "payment_term": "payment_term_id",
        "internal_number": "move_name",
    },
    "account.invoice.line": {
        "uos_id": "uom_id",
        "invoice_line_tax_id": "invoice_line_tax_ids",
    },
    "sale.order": {"payment_term": "payment_term_id"},
}
TABLE_OF_REF_FIELD = {
    "account_id": "account.account",
    "bank_id": "res.partner.bank",
    "bank_ids": "res.partner.bank",
    "company_id": "res.company",
    "country_id": "res.country",
    "conai_category_id": "italy.conai.product.category",
    "goods_description_id": "stock.picking.goods_description",
    "invoice_id": "account.invoice",
    "journal_id": "account.journal",
    "move_id": "account.move",
    "order_id": "sale.order",
    "partner_id": "res.partner",
    "partner_invoice_id": "res.partner",
    "partner_shipping_id": "res.partner",
    "payment_id": "account.payment.term",
    "payment_term_id": "account.payment.term",
    "product_id": "product.product",
    "product_uom": "product.uom",
    "product_uom_id": "product.uom",
    "product_tmpl_id": "product.template",
    "property_payment_term_id": "account.payment.term",
    "sale_id": "sale.order",
    "sale_line_id": "sale.order.line",
    "state_id": "res.country.state",
    "supplier_taxes_id": "account.tax",
    "taxes_id": "account.tax",
    "tax_id": "account.tax",
    "tax_ids": "account.tax",
    "transportation_reason_id": "stock.picking.transportation_reason",
    "uom_id": "product.uom",
    "uom_po_id": "product.uom",
    "uos_id": "product.uom",
    "user_type_id": "account.account.type",
}
# Record structure:
# 0:model, 1:child_ids, 2:parent_field, 3:ext_child_field, 4:function,
# 5:rec_type, 6:multi-child
TABLE_OF_REF_CHILD = {
    "account.invoice": [
        "account.invoice.line",
        "invoice_line_ids",
        "invoice_id",
        {"oe8": "invoice_line"},
        "get_invoice_line_vals",
        False,
        True,
        {"oe8": "invoice_line"},
        "get_invoice_line_vals",
        False,
        True,
    ],
    "account.move": [
        "account.move.line",
        "line_ids",
        "move_id",
        {"oe8": "line_id"},
        "get_move_line_vals",
        False,
        True,
    ],
    "account.payment.term": [
        "account.payment.term.line",
        "line_ids",
        "payment_id",
        {"vg7": "date_scadenza", "oe8": "line_ids"},
        "get_payment_term_line_vals",
        False,
        True,
    ],
    "product.product": [
        "product.product",
        False,
        False,
        False,
        False,
        "product",
        False,
    ],
    "res.partner": [
        "res.partner",
        "child_ids",
        "parent_id",
        False,
        False,
        False,
        False,
    ],
    "res.partner.shipping": [
        "res.partner",
        "child_ids",
        "parent_id",
        {"vg7": "shipping"},
        "get_shipping_vals",
        "delivery",
        False,
    ],
    "res.partner.invoice": [
        "res.partner",
        "child_ids",
        "parent_id",
        {"vg7": "billing"},
        "get_billing_vals",
        "invoice",
        False,
    ],
    "sale.order": [
        "sale.order.line",
        "order_line",
        "order_id",
        {"vg7": "order_rows", "oe8": "order_line"},
        "get_sale_order_line_vals",
        False,
        True,
    ],
    "stock.picking.package.preparation": [
        "stock.picking.package.preparation.line",
        "line_ids",
        "package_preparation_id",
        {"vg7": "order_rows"},
        "get_ddt_line_vals",
        False,
        True,
    ],
}
MODULE_LIST = [
    "account",
    "account_payment_term_extension",
    "date_range",
    "purchase",
    "sale",
    "stock",
    "l10n_it_fiscal",
    "l10n_it_fiscalcode",
    "l10n_it_ddt",
    "l10n_it_einvoice_out",
    "l10n_it_ricevute_bancarie",
    "universal_connector",
    "partner_bank",
    "mk_test_env",
    "l10n_it_conai",
    "connector_vg7_conai",
]

# Warning! Data name not ending with "_DEF" is saved into csv file so every
# record must be contains all fields e and all fields must be in the same order
ACCOUNT_ACCOUNT_TYPE_DEF = [
    {
        "id": "account.data_account_type_receivable",
        "name": "Receivable",
        "type": "receivable",
    },
    {"id": "account.data_account_type_payable", "name": "Payable", "type": "payable"},
    {
        "id": "account.data_account_type_liquidity",
        "name": "Bank and Cash",
        "type": "liquidity",
    },
    {
        "id": "account.data_account_type_credit_card",
        "name": "Credit Card",
        "type": "liquidity",
    },
    {
        "id": "account.data_account_type_current_assets",
        "name": "Current Assets",
        "type": "other",
    },
    {
        "id": "account.data_account_type_non_current_assets",
        "name": "Non-current Assets",
        "type": "other",
    },
    {
        "id": "account.data_account_type_prepayments",
        "name": "Prepayments",
        "type": "other",
    },
    {
        "id": "account.data_account_type_fixed_assets",
        "name": "Fixed Assets",
        "type": "other",
    },
    {
        "id": "account.data_account_type_current_liabilities",
        "name": "Current Liabilities",
        "type": "other",
    },
    {
        "id": "account.data_account_type_non_current_liabilities",
        "name": "Non-current Liabilities",
        "type": "other",
    },
    {"id": "account.data_account_type_equity", "name": "Equity", "type": "other"},
    {
        "id": "account.data_unaffected_earnings",
        "name": "Current Year Earnings",
        "type": "other",
    },
    {
        "id": "account.data_account_type_other_income",
        "name": "Other Income",
        "type": "other",
    },
    {"id": "account.data_account_type_revenue", "name": "Income", "type": "other"},
    {
        "id": "account.data_account_type_depreciation",
        "name": "Depreciation",
        "type": "other",
    },
    {"id": "account.data_account_type_expenses", "name": "Expenses", "type": "other"},
    {
        "id": "account.data_account_type_direct_costs",
        "name": "Cost of Revenue",
        "type": "other",
    },
]
ACCOUNT_ACCOUNT_TYPE_OE8 = [
    {"id": 1, "code": "receivable", "name": "Receivable", "report_type": "receivable"},
    {"id": 2, "code": "payable", "name": "Payable", "report_type": "payable"},
    {"id": 3, "code": "bank", "name": "Bank", "report_type": "liquidity"},
    {"id": 4, "code": "cash", "name": "Cash", "report_type": "liquidity"},
    {"id": 5, "code": "asset", "name": "Assets", "report_type": "other"},
    {"id": 6, "code": "liability", "name": "Liability", "report_type": "other"},
    {"id": 7, "code": "income", "name": "Income", "report_type": "other"},
    {"id": 8, "code": "expense", "name": "Expense", "report_type": "other"},
    {"id": 9, "code": "credit_card", "name": "Credit Card", "report_type": "liquidity"},
    {"id": 10, "code": "equity", "name": "Equity", "report_type": "other"},
]
ACCOUNT_ACCOUNT_DEF = [
    {
        "code": "152100",
        "name": "Crediti v/clienti Italia",
        "user_type_id": "account.data_account_type_receivable",
    },
    {
        "code": "250100",
        "name": "Debiti v/fornitori Italia",
        "user_type_id": "account.data_account_type_payable",
    },
    {
        "code": "180002",
        "name": "Banca",
        "user_type_id": "account.data_account_type_liquidity",
    },
]
ACCOUNT_ACCOUNT_VG7 = []
ACCOUNT_ACCOUNT_OE8 = [
    {"id": 152, "code": "152100", "name": "CLIENTI", "user_type": 1},
    {"id": 250, "code": "250100", "name": "FORNITORI", "user_type": 2},
    {"id": 180, "code": "180002", "name": "Banca Pop. Zero", "user_type": 3},
    {"id": 510, "code": "510000", "name": "Ricavi vendite", "user_type": 7},
]
ACCOUNT_INVOICE_VG7 = []
ACCOUNT_INVOICE_LINE_VG7 = []
ACCOUNT_INVOICE_OE8 = [
    {
        "id": 131,
        "account_id": 152,
        "date_invoice": ref_dt_today,
        "internal_number": "SAJ/2021/0002",
        "journal_id": 1,
        "number": "SAJ/2021/0002",
        "partner_id": 101,
        "partner_shipping_id": 101,
        "payment_term": 31,
        "state": "open",
        "type": "out_invoice",
        "reference": "1234 del 2021",
        "origin": "Test 8.0",
    }
]
ACCOUNT_INVOICE_LINE_OE8 = [
    {
        "id": 131,
        "invoice_id": 131,
        "account_id": 510,
        "invoice_line_tax_id": [1],
        "name": "Product Alpha",
        "price_unit": 1.05,
        "discount": 0.0,
        "product_id": 1,
        "uos_id": 10,
        "quantity": 50,
    },
    {
        "id": 131,
        "invoice_id": 131,
        "account_id": 510,
        "invoice_line_tax_id": [1],
        "name": "Product Beta",
        "price_unit": 5.38,
        "discount": 0.0,
        "product_id": 2,
        "uos_id": 10,
        "quantity": 1,
    },
]
ACCOUNT_JOURNAL_VG7 = []
ACCOUNT_JOURNAL_OE8 = [
    {"id": 1, "code": "INV", "name": "Customer Invoices", "type": "sale"},
    {"id": 2, "code": "BILL", "name": "Supplier Bills", "type": "purchase"},
    {"id": 3, "code": "GEN", "name": "Generic", "type": "general"},
]
ACCOUNT_MOVE_VG7 = []
ACCOUNT_MOVE_LINE_VG7 = []
ACCOUNT_MOVE_OE8 = [
    {
        "id": 2001,
        "name": "BNK/2020/0001",
        "journal_id": 3,
        "date": ref_dt_m_1,
        "narration": "Test connector",
        "ref": "payment",
        "state": "posted",
    }
]
ACCOUNT_MOVE_LINE_OE8 = [
    {
        "id": 2001,
        "move_id": 2001,
        "name": "BNK/2020/0001",
        "ref": "payment",
        "account_id": 180,
        "journal_id": 3,
        "debit": 100.0,
        "credit": 0.0,
        "partner_id": False,
        "date_maturity": ref_dt_today,
        "product_id": False,
        "product_uom_id": False,
        "quantity": 0.0,
        "tax_amount": 0.0,
        "tax_code_id": None,
    },
    {
        "id": 2001,
        "move_id": 2001,
        "name": "BNK/2020/0001",
        "ref": "payment",
        "debit": 0.0,
        "credit": 100.0,
        "account_id": 152,
        "journal_id": 3,
        "partner_id": 101,
        "date_maturity": ref_dt_today,
        "product_id": False,
        "product_uom_id": False,
        "quantity": 0.0,
        "tax_amount": 0.0,
        "tax_code_id": None,
    },
]
ACCOUNT_TAX_DEF = [
    {
        "id": "z0bug.tax_22v",
        "type_tax_use": "sale",
        "name": "IVA 22% su vendite",
        "description": "22v",
        "amount": 22,
    },
    {
        "id": "z0bug.tax_10v",
        "type_tax_use": "sale",
        "name": "IVA 10% su vendite",
        "description": "10v",
        "amount": 10,
    },
    {
        "id": "z0bug.tax_4v",
        "type_tax_use": "sale",
        "name": "IVA 4% su vendite",
        "description": "4v",
        "amount": 4,
    },
    {
        "id": "z0bug.tax_a15v",
        "type_tax_use": "sale",
        "name": "Vend.escluso art.15 DPR633",
        "description": "a15v",
        "amount": 0,
    },
    {
        "id": "z0bug.tax_22a",
        "type_tax_use": "purchase",
        "name": "IVA 22% da acquisti",
        "description": "22a",
        "amount": 22,
    },
]
ACCOUNT_TAX_VG7 = [
    {"id": 22, "code": "22%", "description": "", "aliquota": 22},
    {"id": 4, "code": "4%", "description": "", "aliquota": 4},
    {"id": 101, "code": "A1", "description": "Forfettario art. 101", "aliquota": 0},
    {"id": 115, "code": "15", "description": "Art. 15", "aliquota": 0},
]
ACCOUNT_TAX_OE8 = [
    {
        "id": 1,
        "description": "22v",
        "name": "IVA 22% a debito",
        "amount": 22,
        "type_tax_use": "sale",
    },
    {
        "id": 10,
        "description": "10v",
        "name": "IVA 10% a debito",
        "amount": 10,
        "type_tax_use": "sale",
    },
    {
        "id": 2,
        "description": "22a",
        "name": "IVA 22% a credito",
        "amount": 22,
        "type_tax_use": "purchase",
    },
]
PAYMENT_TERM_DEF = [
    {"id": "z0bug.payment_1", "name": "RiBA 30GG/FM"},
    {"id": "z0bug.payment_2", "name": "RiBA 30/60 GG/FM"},
    {"id": "z0bug.payment_3", "name": "BB 30GG/FM+10"},
    {"id": "z0bug.payment_4", "name": "SEPA DD 30GG"},
]
PAYMENT_TERM_VG7 = [
    {"id": 30, "code": "30", "description": "RiBA 30GG/FM"},
    {"id": 31, "code": "30", "description": "RiBA 30GG/FM+10"},
    {"id": 3060, "code": "31", "description": "RiBA 30/60 GG/FM"},
]
PAYMENT_TERM_LINE_VG7 = [
    {"id": 30, "scadenza": 30, "giorni_fine_mese": 0, "fine_mese": 1},
    {"id": 31, "scadenza": 30, "giorni_fine_mese": 10, "fine_mese": 1},
    {"id": 3060, "scadenza": 30, "giorni_fine_mese": 0, "fine_mese": 1},
    {"id": 3060, "scadenza": 60, "giorni_fine_mese": 0, "fine_mese": "S"},
]
PAYMENT_TERM_OE8 = [
    {"id": 30, "name": "RiBA 30GG/FM"},
    {"id": 31, "name": "RiBA 30/60 GG/FM"},
]
PAYMENT_TERM_LINE_OE8 = [
    {"id": 30, "payment_id": 30, "value": "balance", "days": 30},
    {
        "id": 31,
        "payment_id": 31,
        # 'value': 'procent',
        "value": "percent",
        "days": 30,
    },
    {"id": 31, "payment_id": 31, "value": "balance", "days": 60},
]
CONAI_PROD_DEF = [
    {"code": "CA", "name": "Carta", "conai_price_unit": 30},
    {"code": "AC", "name": "Acciaio", "conai_price_unit": 3},
]
CONAI_PROD_VG7 = [
    {"id": 1, "code": "CA", "description": "Carta ondulata", "prezzo_unitario": 35},
    {"id": 10, "code": "AC", "description": "Acciaio", "prezzo_unitario": 18},
]
PURCHASE_ORDER_VG7 = []
PURCHASE_ORDER_LINE_VG7 = []
PURCHASE_ORDER_OE8 = []
PURCHASE_ORDER_LINE_OE8 = []
PRODUCT_PRODUCT_DEF = [
    {
        "id": "z0bug.product_product_1",
        "default_code": "AAA",
        "name": "Product Alpha",
        "conai_id": False,
    },
    {
        "id": "z0bug.product_product_2",
        "default_code": "BBB",
        "name": "Product Beta",
        "conai_id": False,
    },
    {
        "id": "z0bug.product_product_3",
        "default_code": "CCC",
        "name": "Product Chi",
        "conai_id": False,
    },
    {
        "id": "z0bug.product_template_SB",
        "default_code": "SP-BANC",
        "name": "Spese Bancarie",
        "conai_id": False,
    },
]
PRODUCT_PRODUCT_VG7 = [
    {"id": 1, "code": "AAA", "description": "Product Alpha", "conai_id": 1},
    {"id": 2, "code": "BBB", "description": "Product Beta", "conai_id": 1},
    {"id": 3, "code": "CCC", "description": "Product CC", "conai_id": False},
]
PRODUCT_PRODUCT_OE8 = [
    {"id": 1, "product_tmpl_id": 1, "default_code": "AAA", "name": "Product Alpha"},
    {"id": 2, "product_tmpl_id": 2, "default_code": "BBB", "name": "Product Beta"},
    {"id": 3, "product_tmpl_id": 3, "default_code": "CCC", "name": "Product CC"},
]
PRODUCT_TEMPLATE_DEF = [
    {
        "id": "z0bug.product_template_1",
        "default_code": "AA",
        "name": "Product Alpha",
        "conai_id": False,
    },
    {
        "id": "z0bug.product_template_2",
        "default_code": "BB",
        "name": "Product Beta",
        "conai_id": False,
    },
    {
        "id": "z0bug.product_template_3",
        "default_code": "CC",
        "name": "Product Chi",
        "conai_id": False,
    },
    {
        "id": "z0bug.product_template_SB",
        "default_code": "SP-BANC",
        "name": "Spese Bancarie",
        "conai_id": False,
    },
]
PRODUCT_TEMPLATE_VG7 = [
    {"id": 1, "code": "AA", "description": "Product Alpha", "conai_id": 1},
    {"id": 2, "code": "BB", "description": "Product Beta", "conai_id": 1},
    {"id": 3, "code": "CC", "description": "Product CC", "conai_id": False},
]
PRODUCT_TEMPLATE_OE8 = [
    {
        "id": 1,
        "default_code": "AA",
        "name": "Product Alpha",
        "type": "consu",
        "uom_id": 10,
        "uom_po_id": 10,
        "taxes_id": 1,
        "supplier_taxes_id": 2,
    },
    {
        "id": 2,
        "default_code": "BB",
        "name": "Product Beta",
        "type": "consu",
        "uom_id": 10,
        "uom_po_id": 10,
        "taxes_id": 1,
        "supplier_taxes_id": 2,
    },
    {
        "id": 3,
        "default_code": "CC",
        "name": "Product CC",
        "type": "consu",
        "uom_id": 10,
        "uom_po_id": 10,
        "taxes_id": 1,
        "supplier_taxes_id": 2,
    },
]
PRODUCT_UOM_DEF = [
    {"id": "product.product_uom_unit", "name": "Unit(s)"},
    {"id": "product.product_uom_kgm", "name": "kg"},
]
PRODUCT_UOM_VG7 = [
    {"id": 1, "code": "NR"},
    {"id": 2, "code": "KG"},
    {"id": 5, "code": "m"},
]
PRODUCT_UOM_OE8 = [
    {"id": 10, "name": "Unit(s)"},
    {"id": 12, "name": "kg"},
    {"id": 15, "name": "m"},
]
RES_COMPANY_VG7 = []
RES_COMPANY_OE8 = [{"id": EXT_COMPANY_ID, "partner_id": 3, "name": "Test Company"}]
RES_COUNTRY_VG7 = [
    {"id": 39, "code": "IT", "description": "Italia"},
    {"id": 49, "code": "DE", "description": "Germania"},
]
RES_COUNTRY_OE8 = [
    {"id": 39, "code": "IT", "name": "Italia"},
    {"id": 44, "code": "UK", "name": "Regno Unito"},
]
RES_COUNTRY_STATE_VG7 = [
    {"id": 2, "code": "MI", "description": "Milano"},
    {"id": 11, "code": "TO", "description": "Torino"},
    {"id": 54, "code": "BO", "description": "Bologna"},
    {"id": 81, "code": "NA", "description": "Napoli"},
    {"id": 82, "code": "CE", "description": "Caserta"},
]
RES_COUNTRY_STATE_OE8 = [
    {"id": 2, "country_id": 39, "code": "MI", "name": "Milano"},
    {"id": 11, "country_id": 39, "code": "TO", "name": "Torino"},
    {"id": 54, "country_id": 39, "code": "BO", "name": "Bologna"},
    {"id": 81, "country_id": 39, "code": "NA", "name": "Napoli"},
    {"id": 82, "country_id": 39, "code": "CE", "name": "Caserta"},
]
RES_PARTNER_SHIPPING = [
    {
        "customer_shipping_id": 101,
        "customer_id": 11,
        "shipping_name": "Partner A",
        "shipping_surename": "",
        "shipping_country_id": 39,
        "shipping_region_id": 11,
        "shipping_postal_code": "35100",
        "shipping_city": "Padova",
    },
    {
        "customer_shipping_id": 102,
        "customer_id": 12,
        "shipping_name": "",
        "shipping_surename": "",
        "shipping_country_id": 39,
        "shipping_region_id": 11,
        "shipping_postal_code": "10061",
        "shipping_city": "S. Secondo fraz. Pinasca",
    },
]
RES_PARTNER_BILLING = [
    {
        "customer_billing_id": 11,
        "customer_id": 11,
        "billing_country_id": 39,
        "billing_name": "",
        "billing_street": "Via Porta Nuova",
        "billing_street_number": "1",
        "billing_postal_code": "",
        "billing_city": "Torino",
        "billing_piva": "00385870480",
        "billing_bank_id": None,
    },
    {
        "customer_billing_id": 12,
        "customer_id": 12,
        "billing_country_id": 39,
        "billing_name": "",
        "billing_street": None,
        "billing_street_number": None,
        "billing_postal_code": "",
        "billing_city": "",
        "billing_piva": "",
        "billing_bank_id": 2468,
    },
]
RES_PARTNER_DEF = [
    {
        "id": "z0bug.res_partner_2",
        "name": "Agro Latte Due  s.n.c.",
        "street": "Via II Giugno, 22",
        "country_id": "base.it",
        "zip": "10060",
        "city": "S. Secondo Pinerolo",
        "state_id": "base.state_it_to",
        "vat": "IT02345670018",
        "goods_description_id": "l10n_it_ddt.goods_description_SFU",
        "carriage_condition_id": "l10n_it_ddt.carriage_condition_PAF",
        "transportation_method_id": "l10n_it_ddt.transportation_method_COR",
        "customer": True,
        "supplier": False,
    },
    {
        "id": "z0bug.res_partner_4",
        "name": "Delta 4 s.r.l.",
        "street": "C.so IV Marzo, 33",
        "country_id": "base.it",
        "zip": "65122",
        "city": "Pescara",
        "state_id": "base.state_it_pe",
        "vat": "IT06631580013",
        "goods_description_id": None,
        "carriage_condition_id": None,
        "transportation_method_id": None,
        "customer": False,
        "supplier": True,
    },
]
RES_PARTNER_VG7 = [
    {
        "id": 11,
        "company": "Partner A",
        "name": None,
        "surename": None,
        "street": "",
        "street_number": "",
        "postal_code": "10100",
        "city": "Torino",
        "region": "TORINO",
        "region_id": 11,
        "country_id": "Italia",
        "esonerato_fe": "1",
        "piva": "",
        "cf": "",
        "payment_id": 30,
        "goods_description_id": False,
        "carriage_condition_id": False,
        "transportation_method_id": False,
        "splitmode": None,
    },
    {
        # Agro Latte Due  s.n.c.
        "id": 12,
        "company": None,
        "name": None,
        "surename": None,
        "street": None,
        "street_number": None,
        "postal_code": None,
        "city": None,
        "region": None,
        "region_id": None,
        "country_id": None,
        "esonerato_fe": None,
        "piva": "02345670018",
        "cf": "",
        "payment_id": None,
        "goods_description_id": None,
        "carriage_condition_id": None,
        "transportation_method_id": None,
        "splitmode": None,
    },
    {
        # None
        "id": 7,
        "company": None,
        "name": None,
        "surename": None,
        "street": None,
        "street_number": None,
        "postal_code": None,
        "city": None,
        "region": None,
        "region_id": None,
        "country_id": None,
        "esonerato_fe": None,
        "piva": None,
        "cf": None,
        "payment_id": None,
        "goods_description_id": "l10n_it_ddt.goods_description_SFU",
        "carriage_condition_id": "l10n_it_ddt.carriage_condition_PAF",
        "transportation_method_id": "l10n_it_ddt.transportation_method_COR",
        "splitmode": None,
    },
    {
        # New record
        "id": 17,
        "company": None,
        "name": "Mario",
        "surename": "Rossi",
        "street": None,
        "street_number": None,
        "postal_code": None,
        "city": None,
        "region": None,
        "region_id": None,
        "country_id": "Italia",
        "esonerato_fe": None,
        "piva": None,
        "cf": "RSSMRA69C02D612M",
        "payment_id": None,
        "goods_description_id": False,
        "carriage_condition_id": False,
        "transportation_method_id": False,
        "splitmode": "LF",
    },
]
RES_PARTNER_OE8 = [
    {"id": 1, "name": "admbot", "email": "admbot@example.com"},
    {"id": 3, "name": "Test Company", "email": "info@example.com"},
    {"id": 101, "name": "Partner A", "email": "partnera@example.com"},
]
RES_PARTNER_SUPPLIER_VG7 = [
    {
        "id": 14,
        "company": "Delta 4 s.r.l.",
        "name": None,
        "surename": None,
        "street": "Via Sofocle",
        "street_number": "14",
        "postal_code": "20864",
        "city": "Milano",
        "region": "MILANO",
        "region_id": 2,
        "country_id": 39,
        "piva": "06631580013",
        "cf": "01781920150",
    }
]
RES_PARTNER_BANK_VG7 = [
    {
        "id": 2468,
        "description": "Banca Popolare",
        # IT60X0542811101000000123456
        "IBAN": TEST_IBAN,
        "customer_id": 12,
    }
]
RES_PARTNER_BANK_OE8 = []
RES_USERS_VG7 = []
RES_USERS_OE8 = [{"id": 13, "login": "admbot", "partner_id": 1}]
SALE_ORDER_VG7 = [
    {
        "id": 131,
        "customer_id": 11,
        "customer_shipping_id": 101,
        "order_number": "210131",
        "date": ref_dt_m_1,
        "order_state": 2,
        "payment_id": 31,
        "billing": {},
        "shipping": {},
    },
    {
        "id": 210,
        "customer_id": 12,
        "customer_shipping_id": 12,
        "order_number": "210210",
        "date": ref_dt_m_1,
        "order_state": 2,
        "payment_id": 30,
        "billing": {},
        "shipping": {},
    },
]
SALE_ORDER_LINE_VG7 = [
    {
        "id": 131,
        "order_id": 131,
        "job_name": "Product Alpha",
        "product_name": "Product Alpha",
        "quantity": 50,
        "unitary_price": 1.05,
        "tax_id": "22v",
    },
    {
        "id": 131,
        "order_id": 131,
        "job_name": "Product Beta",
        "product_name": "Product Beta",
        "quantity": 1,
        "unitary_price": 5.38,
        "tax_id": "22v",
    },
    {
        "id": 210,
        "order_id": 210,
        "job_name": "Product Alpha",
        "product_name": "Product Alpha",
        "quantity": 100,
        "unitary_price": 1.05,
        "tax_id": "22v",
    },
    {
        "id": 210,
        "order_id": 210,
        "job_name": "Product Beta",
        "product_name": "Product Beta",
        "quantity": 60,
        "unitary_price": 5.38,
        "tax_id": "22v",
    },
]
SALE_ORDER_OE8 = [
    {
        "id": 80,
        "name": "SO080",
        "date_order": ref_ts_m_1,
        "partner_id": 101,
        "client_order_ref": "1234 del 2021",
        "origin": "Test 8.0",
        "partner_invoice_id": 101,
        "partner_shipping_id": 101,
        "payment_term": 30,
        "state": "manual",
        "transportation_reason_id": 1,
    }
]
SALE_ORDER_LINE_OE8 = [
    {
        "id": 80,
        "order_id": 80,
        "name": "Product Alpha",
        "product_id": 1,
        "product_tmpl_id": 1,
        "price_unit": 1.05,
        "discount": 0.0,
        "product_uom": 10,
        "product_uom_qty": 50,
        "tax_id": [1],
    }
]
STOCK_PICKING_TRANSPORTATION_REASON_VG7 = [
    {"id": 3, "code": "V", "description": "Vendita"},
    {"id": 4, "code": "L", "description": "Conto Lavoro"},
]
STOCK_PICKING_TRANSPORTATION_REASON_OE8 = [
    {"id": 1, "name": "Vendita", "to_be_invoiced": 1}
]
STOCK_PICKING_PACKAGE_PREPARATION_VG7 = [
    {
        "id": 7,
        "ddt_number": "1234",
        "numero_colli": 1,
        "customer_id": 11,
        "vettori_prima_riga": "",
        "vettori_seconda_riga": "",
        "voce_doganale": "",
        "aspetto_esteriore_dei_beni": "BANCALI",
        "causal_id": 3,
        "note": "Si prega di controllate i dati entro le 24h.",
        "peso_netto": 9.0,
        "tipo_porto": "FRANCO",
        "peso_lordo": 10.0,
        "ora_ritiro": "18:30:00",
        "data_emissione": "2020-11-30",
        # 'data_ritiro': '2020-11-30',
        "mezzo": "MITTENTE",
    }
]
STOCK_PICKING_PACKAGE_PREPARATION_LINE_VG7 = [
    {
        "id": 7,
        "ddt_id": 7,
        "product_id": 1,
        "quantita": 50,
        "prezzo_unitario": 1.05,
        "order_id": 131,
        "order_row_id": 1310,
        "descrizione": "Product Alpha",
        "conai_id": 1,
        "tax_code_id": 22,
    },
    {
        "id": 7,
        "ddt_id": 7,
        "product_id": 2,
        "quantita": 1,
        "prezzo_unitario": 5.38,
        "order_id": 131,
        "order_row_id": 1311,
        "descrizione": "Product Beta",
        "conai_id": 1,
        "tax_code_id": 22,
    },
]
STOCK_PICKING_PACKAGE_PREPARATION_OE8 = []
STOCK_PICKING_PACKAGE_PREPARATION_LINE_OE8 = []


def get_csv_path(identity):
    root = os.path.join(
        os.path.dirname(os.path.expanduser(os.environ.get("HOME_DEVEL", "~/devel"))),
        "clodoo",
        "test",
    )
    if not identity:
        return root
    return os.path.join(root, (identity.split(":")[0]))


def env_ref(ctx, xref, retxref_id=None):
    def simulate_xref(xrefs, model, by=None):
        by = by or "name"
        tok = xrefs[1].split("_")[-1]
        domain = [(by, "=", tok)]
        domain.append(("company_id", "=", ctx["company_id"]))
        recs = clodoo.searchL8(ctx, model, domain)
        if len(recs) == 1:
            return recs[0]
        return False

    if " " in xref:
        return xref
    xrefs = xref.split(".")
    if len(xrefs) == 2:
        model = "ir.model.data"
        ids = clodoo.searchL8(
            ctx, model, [("module", "=", xrefs[0]), ("name", "=", xrefs[1])]
        )
        if ids:
            if retxref_id:
                return ids[0]
            return clodoo.browseL8(ctx, model, ids[0]).res_id
        elif xref.startswith("z0bug.tax_"):
            return simulate_xref(xrefs, "account.tax", by="description")
    return False


def write_log(ctx, mesg, eol=None):
    with open(ctx["logfn"], "a") as fd:
        if eol:
            fd.write("%s\n" % mesg)
        else:
            fd.write(mesg)


def compare_some(dict_item, vals, field=None):
    field = field or dict_item["domain"][0]
    if (
        (dict_item["domain"][1] == "=" and vals[field] == dict_item["domain"][2])
        or (
            dict_item["domain"][1] == "=~"
            and vals[field].startswith(dict_item["domain"][2])
        )
        or (dict_item["domain"][1] == "in" and vals[field] in dict_item["domain"][2])
    ):
        return True
    return False


def get_some_default(model, vals, identity, test_vals):
    if model in SOME_DEFAULT:
        for dict_item in SOME_DEFAULT[model]:
            field = dict_item["domain"][0]
            if identity.startswith("vg7"):
                for x in TNL_VG7_DICT[model].items():
                    if x[1] == dict_item["domain"][0]:
                        field = x[0]
                        break
            if compare_some(dict_item, vals, field=field):
                if dict_item["value"][0].startswith(":"):
                    # test_vals[dict_item['value'][0][1:]] = ctx[
                    #     dict_item['value'][1]]
                    test_vals[dict_item["value"][0]] = ctx[dict_item["value"][1]]
                elif identity:
                    if dict_item["value"][1] in ctx:
                        test_vals["%s%s" % (identity, dict_item["value"][0])] = ctx[
                            dict_item["value"][1]
                        ]
                    else:
                        test_vals[
                            "%s%s" % (identity, dict_item["value"][0])
                        ] = dict_item["value"][1]
                else:
                    test_vals[dict_item["value"][0]] = ctx[dict_item["value"][1]]
    return test_vals


def delete_record(
    ctx, model, domains, multi=False, action=None, childs=None, company_id=False
):
    if not ctx["conai"] and "conai" in model:
        return
    print("Delete records %s of model %s ..." % (domains, model))

    excl_list = [
        rec.res_id
        for rec in clodoo.browseL8(
            ctx,
            "ir.model.data",
            clodoo.searchL8(ctx, "ir.model.data", [("model", "=", model)]),
        )
    ]
    if model == "res.partner":
        for rec in clodoo.browseL8(
            ctx, "res.users", clodoo.searchL8(ctx, "res.users", [])
        ):
            if rec.partner_id.id not in excl_list:
                excl_list.append(rec.partner_id.id)
    if not isinstance(domains, (list, tuple)):
        domains = [domains]
    single_query = True
    for domain in domains:
        if isinstance(domain, (basestring, int)):
            single_query = False
            break
        elif isinstance(domain, (list, tuple)):
            break
    if single_query:
        domains = [domains]
    for domain in domains:
        rec_ids = []
        if isinstance(domain, basestring):
            rec_ids = env_ref(ctx, domain)
            rec_ids = [rec_ids] if rec_ids else []
        elif isinstance(domain, int):
            full_domain = []
            for test_prefix in ("vg7:", "oe8:"):
                ext_name = "%s_id" % test_prefix.split(":")[0] if test_prefix else False
                if domain == -1:
                    leaf = [(ext_name, "!=", False), (ext_name, "!=", 0)]
                else:
                    leaf = [(ext_name, "=", domain)]
                if not full_domain:
                    full_domain = leaf
                else:
                    if len(leaf) > 1:
                        leaf.insert(0, "&")
                    if len(full_domain) == 2:
                        full_domain.insert(0, "&")
                    full_domain.insert(0, "|")
                    full_domain.extend(leaf)
            domain = full_domain
        if not rec_ids:
            if company_id:
                domain.append(("company_id", "=", company_id))
            if excl_list:
                domain.append(("id", "not in", excl_list))
            rec_ids = clodoo.searchL8(ctx, model, domain)
        if (not multi and len(rec_ids) == 1) or (multi and len(rec_ids)):
            if action:
                if not isinstance(action, (list, tuple)):
                    action = [action]
                for act in action:
                    if act == "move_name=":
                        clodoo.writeL8(ctx, model, rec_ids, {"move_name": ""})
                    else:
                        try:
                            clodoo.executeL8(ctx, model, act, rec_ids)
                        except BaseException:
                            print("Warning! Cannot execute %s.%s" % (model, act))
            if childs:
                for parent in clodoo.browseL8(ctx, model, rec_ids):
                    for rec in parent[childs]:
                        if rec.id in rec_ids:
                            continue
                        try:
                            clodoo.unlinkL8(ctx, model, rec.id)
                            write_log(
                                ctx, ">>> %s.unlink(%s)" % (model, rec.id), eol=True
                            )
                        except BaseException as e:
                            print("Error %s removing records ..." % e)
            try:
                clodoo.unlinkL8(ctx, model, rec_ids)
                write_log(ctx, ">>> %s.unlink(%s)" % (model, rec_ids), eol=True)
            except BaseException as e:
                print("Error %s removing records ..." % e)
                if ctx["ask"]:
                    input("Press RET to continue")
                else:
                    exit(1)


def write_record(ctx, model, domain, vals, company_id=False, create=None, unique=None):
    if isinstance(domain, basestring):
        ids = env_ref(ctx, domain)
        ids = [ids] if ids else []
    else:
        if company_id:
            domain.append(("company_id", "=", company_id))
        ids = clodoo.searchL8(ctx, model, domain)
    if ids:
        clodoo.writeL8(ctx, model, ids, vals)
        if unique and len(ids) > 1:
            print('Warning: Too many records "%s.%s"' % (model, domain))
            delete_record(ctx, model, [("id", "in", ids[1:])])
    elif create:
        ids = [clodoo.createL8(ctx, model, vals)]
    return ids


def reset_ext_id(model):
    domain = ["|"]
    if model == "res.partner":
        domain.append("|")
    for nm in ("vg7_id", "oe8_id"):
        domain.append((nm, ">", 0))
    if model == "res.partner":
        domain.append(("vg72_id", ">", "0"))
    vals = {"vg7_id": False, "oe8_id": False}
    if model == "res.partner":
        vals["vg72_id"] = False
    ids = clodoo.searchL8(ctx, model, domain)
    for id in ids:
        clodoo.writeL8(ctx, model, id, vals)


def rm_file_2_pull(ext_model, identity):
    fn = os.path.join(get_csv_path(identity), "%s.csv" % ext_model)
    if os.path.isfile(fn):
        os.unlink(fn)


def set_sequence(ctx, domain, next_number, multi=False, company_id=False):
    model = "ir.sequence"
    if company_id:
        domain.append(("company_id", "=", company_id))
    ids = clodoo.searchL8(ctx, model, domain)
    if (not multi and len(ids) == 1) or (multi and len(ids)):
        for rec in clodoo.browseL8(ctx, model, ids):
            clodoo.writeL8(
                ctx,
                model,
                ids,
                {"number_next_actual": next_number, "number_next": next_number},
            )
            for rec1 in rec.date_range_ids:
                if rec1.date_from < date.today() <= rec1.date_to:
                    clodoo.writeL8(
                        ctx,
                        "%s.date_range" % model,
                        rec1.id,
                        {"number_next_actual": next_number, "number_next": next_number},
                    )


def store_vg7id(ctx, model, loc_id, vg7_id):
    if model not in TNL_VG7_DICT:
        TNL_VG7_DICT[model] = {}
    if "EXT" not in TNL_VG7_DICT[model]:
        TNL_VG7_DICT[model]["LOC"] = {}
        TNL_VG7_DICT[model]["EXT"] = {}
    if isinstance(vg7_id, basestring) and vg7_id.isdigit():
        TNL_VG7_DICT[model]["LOC"][loc_id] = eval(vg7_id)
        TNL_VG7_DICT[model]["EXT"][eval(vg7_id)] = loc_id
    else:
        TNL_VG7_DICT[model]["LOC"][loc_id] = vg7_id
        TNL_VG7_DICT[model]["EXT"][vg7_id] = loc_id


def store_oe8id(ctx, model, loc_id, oe8_id):
    if model not in TNL_OE8_DICT:
        TNL_OE8_DICT[model] = {}
    if "EXT" not in TNL_OE8_DICT[model]:
        TNL_OE8_DICT[model]["LOC"] = {}
        TNL_OE8_DICT[model]["EXT"] = {}
    if isinstance(oe8_id, basestring) and oe8_id.isdigit():
        TNL_OE8_DICT[model]["LOC"][loc_id] = eval(oe8_id)
        TNL_OE8_DICT[model]["EXT"][eval(oe8_id)] = loc_id
    else:
        TNL_OE8_DICT[model]["LOC"][loc_id] = oe8_id
        TNL_OE8_DICT[model]["EXT"][oe8_id] = loc_id


def store_ext_id(ctx, model, loc_id, ext_id, identity):
    if loc_id and ext_id:
        if identity.startswith("vg7"):
            store_vg7id(ctx, model, loc_id, ext_id)
        elif identity.startswith("oe8"):
            store_oe8id(ctx, model, loc_id, ext_id)


def write_file_2_pull(ext_model, vals, mode=None, identity=None):
    mode = mode or "w"
    if identity:
        fn = os.path.join(get_csv_path(identity), "%s.csv" % ext_model)
    else:
        fn = os.path.join(get_csv_path(), "%s.csv" % ext_model)
    if mode == "a":
        with open(fn, "r") as fd:
            ln = fd.read().split("\n")[0]
        data = "%s\n" % ",".join([str(vals.get(x, "")) for x in ln.split(",")])
    else:
        data = "%s\n%s\n" % (
            ",".join(vals.keys()),
            ",".join(map(lambda x: str(vals[x]), vals.keys())),
        )
    with open(fn, mode) as fd:
        fd.write(data)


def get_vg7id_from_id(ctx, model, id):
    return clodoo.browseL8(ctx, model, id).vg7_id


def get_id_from_vg7id(ctx, model, vg7_id, name=None):
    name = name or "vg7_id"
    ids = clodoo.searchL8(ctx, model, [(name, "=", vg7_id)])
    if ids:
        return ids[0]
    return -1


def is_untranslable(loc_name, ext_ref, vals):
    if ext_ref in vals and (
        vals[ext_ref] is False
        or (
            (
                isinstance(vals[ext_ref], basestring)
                and " " not in vals[ext_ref]
                and len(vals[ext_ref].split(".")) == 2
            )
        )
    ):
        return True
    return False


def jacket_vals(vals, prefix=None):
    prefix = prefix or "vg7:"
    for nm in vals.copy():
        if is_untranslable(nm, nm, vals):
            continue
        if not nm.startswith("%s" % prefix) and not nm.startswith(":"):
            vals["%s%s" % (prefix, nm)] = vals[nm]
            del vals[nm]
    return vals


def shirt_vals(vals):
    for nm in vals.copy():
        if nm in ("customer_shipping_id", "customer_billing_id"):
            continue
        new_name = nm.replace("billing_", "").replace("shipping_", "")
        if new_name != nm:
            vals[new_name] = vals[nm]
            del vals[nm]
    return vals


def value_by_identity(identity, val_vg7, val_oe8):
    if identity.startswith("vg7"):
        return val_vg7
    elif identity.startswith("oe8"):
        return val_oe8
    return False


def get_id_from_extid(loc_name, loc_value, identity):
    if loc_name in TABLE_OF_REF_FIELD:
        ref_model = TABLE_OF_REF_FIELD[loc_name]
        if identity.startswith("vg7"):
            if ref_model in TNL_VG7_DICT and "LOC" in TNL_VG7_DICT[ref_model]:
                loc_value = TNL_VG7_DICT[ref_model]["LOC"].get(loc_value, loc_value)
        elif identity.startswith("oe8"):
            if ref_model in TNL_OE8_DICT and "LOC" in TNL_OE8_DICT[ref_model]:
                loc_value = TNL_OE8_DICT[ref_model]["LOC"].get(loc_value, loc_value)
    return loc_name


def get_loc_name(model, field, identity):
    mode = False
    loc_name = field
    if field in ("vg7:id", "oe8:id"):
        loc_name = "id"
    elif identity.startswith("vg7"):
        if model and model in TNL_VG7_DICT and field in TNL_VG7_DICT[model]:
            loc_name = TNL_VG7_DICT[model][field]
            if loc_name and isinstance(loc_name, (tuple, list)):
                mode = loc_name[1]
                loc_name = loc_name[0]
        if loc_name == field:
            if field.startswith("shipping_"):
                loc_name = field[9:]
            elif field.startswith("billing_"):
                loc_name = field[8:]
            if model and model in TNL_VG7_DICT and loc_name in TNL_VG7_DICT[model]:
                loc_name = TNL_VG7_DICT[model][loc_name]
    elif identity.startswith("oe8"):
        if model and model in TNL_OE8_DICT and field in TNL_OE8_DICT[model]:
            loc_name = TNL_OE8_DICT[model][field]
            if loc_name and isinstance(loc_name, (tuple, list)):
                mode = loc_name[1]
                loc_name = loc_name[0]
    return loc_name, mode


def get_loc_value(
    ctx, model, loc_rec, ext_ref, ext_name, loc_name, vals, identity, spec
):
    mode = False
    if loc_name.endswith("_id") or loc_name in M2O_FIELDS or loc_name in M2M_FIELDS:
        if loc_name in M2M_FIELDS:
            try:
                loc_value = getattr(loc_rec, loc_name)[0].id
            except BaseException:
                loc_value = getattr(loc_rec, loc_name)
        else:
            try:
                loc_value = getattr(loc_rec, loc_name).id
            except BaseException:
                loc_value = getattr(loc_rec, loc_name)
        if not spec and isinstance(loc_value, int):
            loc_value = loc_value % 100000000
        ckstr = False
        if loc_name in TABLE_OF_REF_FIELD:
            ref_model = TABLE_OF_REF_FIELD[loc_name]
            if identity.startswith("vg7"):
                if (
                    ref_model in TNL_VG7_DICT
                    and "LOC" in TNL_VG7_DICT[ref_model]
                    and loc_name != "tax_id"
                ):
                    loc_value = TNL_VG7_DICT[ref_model]["LOC"].get(loc_value, loc_value)
                    mode = "tnx"
            elif identity.startswith("oe8"):
                if ref_model in TNL_OE8_DICT and "LOC" in TNL_OE8_DICT[ref_model]:
                    loc_value = TNL_OE8_DICT[ref_model]["LOC"].get(loc_value, loc_value)
                    mode = "tnx"
            ckstr = True
        elif loc_name == "parent_id":
            if identity.startswith("vg7"):
                if model in TNL_VG7_DICT:
                    loc_value = TNL_VG7_DICT[model]["LOC"].get(loc_value, loc_value)
            elif identity.startswith("oe8"):
                if model in TNL_OE8_DICT:
                    loc_value = TNL_OE8_DICT[model]["LOC"].get(loc_value, loc_value)
            ckstr = True
        if ckstr and isinstance(vals[ext_ref], basestring):
            ids = clodoo.searchL8(
                ctx,
                ref_model,
                [("name", "ilike", vals[ext_ref])],
                context={"lang": "it_IT"},
            )
            if not ids:
                ids = clodoo.searchL8(
                    ctx, ref_model, [("name", "ilike", vals[ext_ref])]
                )
            if len(ids) >= 1:
                if len(ids) > 1:
                    print(
                        "Warning: "
                        "multiple records %s.%s detected" % (ref_model, vals[ext_ref])
                    )
                if identity.startswith("vg7") and ref_model in TNL_VG7_DICT:
                    vals[ext_ref] = TNL_VG7_DICT[ref_model]["LOC"].get(ids[0], ids[0])
                elif identity.startswith("oe8") and ref_model in TNL_OE8_DICT:
                    vals[ext_ref] = TNL_OE8_DICT[ref_model]["LOC"].get(ids[0], ids[0])
                else:
                    vals[ext_ref] = ids[0]
    else:
        loc_value = getattr(loc_rec, loc_name)
        if isinstance(loc_value, datetime):
            if ext_ref in ("vg7:data_emissione", "vg7:data_ritiro", "vg7:date"):
                loc_value = datetime.strftime(loc_value, "%Y-%m-%d")
            else:
                loc_value = datetime.strftime(loc_value, "%Y-%m-%d %H:%M:%S")
        elif isinstance(loc_value, date):
            loc_value = datetime.strftime(loc_value, "%Y-%m-%d")
        elif model == "product.uom" and loc_value == "Unità":
            loc_value = "Unit(s)"
        elif (
            model == "account.invoice"
            and loc_name == "number"
            and loc_rec.state != "draft"
        ):
            mode = "nounknown"
    return loc_value, mode


def get_ext_value(
    ctx,
    model,
    ext_ref,
    ext_name,
    loc_name,
    vals,
    spec,
    identity=None,
    transcode=None,
    state=None,
):
    transcode = transcode if transcode is not None else True
    mode = False
    field_pfx = False
    if ext_ref.startswith("vg7:") or ext_ref.startswith("oe8:"):
        field_pfx = ext_ref[0:4]
    if is_untranslable(loc_name, ext_ref, vals) and not field_pfx and vals[ext_ref]:
        ext_value = env_ref(ctx, vals[ext_ref])
    elif model == "sale.order" and vals[ext_ref] == -1:
        ext_value = vals[ext_ref] = 12
        ctx["ctr"] += 1
    else:
        ext_value = vals[ext_ref]
    # ext_ref like ":name" are not local translated; translate here
    if ext_ref.startswith(":") and ext_name and transcode:
        if loc_name in TABLE_OF_REF_FIELD:
            ref_model = TABLE_OF_REF_FIELD[loc_name]
            if not identity or identity.startswith("vg7"):
                if (
                    TABLE_OF_REF_FIELD[loc_name] in TNL_VG7_DICT
                    and "LOC" in TNL_VG7_DICT[ref_model]
                ):
                    ext_value = TNL_VG7_DICT[ref_model]["LOC"].get(ext_value, ext_value)
            elif identity.startswith("oe8"):
                if (
                    TABLE_OF_REF_FIELD[loc_name] in TNL_OE8_DICT
                    and "LOC" in TNL_OE8_DICT[ref_model]
                ):
                    ext_value = TNL_OE8_DICT[ref_model]["LOC"].get(ext_value, ext_value)
    elif ext_ref in ("vg7:id", "vg7_id", "oe8:id", "oe8_id") and (
        isinstance(vals[ext_ref], basestring) and vals[ext_ref].isdigit()
    ):
        ext_value = eval(vals[ext_ref])
    elif loc_name == "state":
        ext_value = vals[ext_ref]
        if state:
            ext_value = state
        elif (
            ext_ref in STATUS_VALUE
            and not isinstance(STATUS_VALUE[ext_ref], bool)
            and vals[ext_ref] in STATUS_VALUE[ext_ref]
        ):
            ext_value = STATUS_VALUE[ext_ref][vals[ext_ref]]
    elif (
        loc_name in TNL_TEXT_2_M2
        and isinstance(ext_value, basestring)
        and ext_value in TNL_TEXT_2_M2[loc_name]
    ):
        ext_value = env_ref(ctx, TNL_TEXT_2_M2[loc_name][ext_value])
    elif loc_name in M2M_FIELDS and isinstance(ext_value, (list, tuple)):
        ext_value = ext_value[0]
    elif spec in ("delivery", "invoice") and loc_name in ("name", "firstname"):
        ext_value = False
    elif loc_name == "company_id" and not identity.startswith("oe8"):
        ext_value = env_ref(ctx, "z0bug.mycompany")
    elif (
        loc_name.endswith("_id")
        and isinstance(vals[ext_ref], basestring)
        and vals[ext_ref].isdigit()
    ):
        ext_value = eval(vals[ext_ref])
    elif loc_name == "street" and field_pfx == "vg7:":
        ext_value = "%s, %s" % (
            vals[ext_ref],
            vals.get(
                "vg7:%s_number" % ext_name,
                vals.get(
                    "vg7:%s_number" % ext_name,
                    vals.get(
                        "%s_number" % ext_name, vals.get("%s_number" % ext_name, "")
                    ),
                ),
            ),
        )
        if ext_value == ", " or ext_value == ("%s, %s" % (None, None)):
            ext_value = None
    elif ext_ref == "state" and field_pfx:
        ext_value = "draft"
    elif loc_name == "vat" and (field_pfx == "vg7:" or identity == "vg7:"):
        if vals[ext_ref]:
            ext_value = "IT%s" % vals[ext_ref]
    elif model == "account.tax" and loc_name in ("name", "description"):
        ext_value = vals[ext_ref]
        mode = "nounknown"
    elif (
        model == "res.partner"
        and loc_name == "electronic_invoice_subjected"
        and field_pfx == "vg7:"
    ):
        ext_value = not os0.str2bool(vals[ext_ref], 0)
    elif ext_name == "giorni_fine_mese" and not ext_value:
        ext_value = ""
    if model == "res.partner" and ext_ref == "vg7:name" and vals.get("vg7_id") == 17:
        mode = "individual"
    return ext_value, mode


def reset_cache(ctx):
    lifetime = clodoo.executeL8(
        ctx,
        "ir.model.synchro.cache",
        "clean_cache",
        0,
        None,  # channel_id
        None,  # model
        60,
    )  # cache lifetime
    if lifetime != 60:
        raise IOError("Invalid cache lifetime setup!!!")
    ctx["ctr"] += 1


def test_function_synchro(ctx, model, vals, identity=None, ext_id=None):
    """
    Test function synchro: child record datas are in model values
    """
    if identity:
        vals = jacket_vals(vals, identity)
    write_log(ctx, ">>> synchro(ctx, %s, %s)" % (model, vals))
    rec_id = clodoo.executeL8(ctx, model, "synchro", vals)
    write_log(ctx, " => %s" % rec_id, eol=True)
    if ext_id and rec_id > 0:
        store_ext_id(ctx, model, rec_id, ext_id, identity)
    return rec_id, vals


def test_function_synchro2(
    ctx, model, vals, parent_field, child_field, child_model, identity=None, ext_id=None
):
    """
    Test function synchro: child records are sent after parent record
    Require commit function
    """
    if child_field not in vals:
        raise KeyError("No child field!")
    child_vals = vals[child_field]
    del vals[child_field]
    if identity:
        vals = jacket_vals(vals, identity)
    write_log(ctx, ">>> synchro(ctx, %s, %s)" % (model, vals))
    rec_id = clodoo.executeL8(ctx, model, "synchro", vals)
    write_log(ctx, " => %s" % rec_id, eol=True)
    if ext_id and rec_id > 0:
        store_ext_id(ctx, model, rec_id, ext_id, identity)
    for item in child_vals:
        if identity:
            child_vals = jacket_vals(item, identity)
        child_vals[":%s" % parent_field] = rec_id
        write_log(ctx, ">>> synchro(ctx, %s, %s)" % (child_model, child_vals))
        child_id = clodoo.executeL8(ctx, child_model, "synchro", child_vals)
        write_log(ctx, " => %s" % child_id, eol=True)
    return rec_id, vals


def test_function_trigger(ctx, ext_model, vals, identity, ext_id):
    write_log(
        ctx, ">>> trigger_one_record(ctx, %s, %s, %s)" % (ext_model, ext_id, identity)
    )
    rec_id = clodoo.executeL8(
        ctx, "ir.model.synchro", "trigger_one_record", ext_model, identity, ext_id
    )
    if ext_id and rec_id > 0:
        store_ext_id(ctx, ext_model, rec_id, ext_id, identity)
    vals = jacket_vals(vals, identity)
    write_log(ctx, " => %s, %s" % (rec_id, vals), eol=True)
    return rec_id, vals


def commit(ctx, model, rec_id, vals):
    write_log(ctx, ">>> commit(ctx, %s, %s)" % (model, rec_id))
    ret_id = clodoo.executeL8(ctx, model, "commit", rec_id)
    write_log(ctx, " => %s" % rec_id, eol=True)
    if ret_id != rec_id:
        raise IOError(
            "!!Invalid %s commit status <%s> expected <%s>" % (model, ret_id, rec_id)
        )
    ctx["ctr"] += 1
    state = False
    for nm in vals:
        if nm in STATUS_VALUE:
            if isinstance(STATUS_VALUE[nm], bool):
                state = vals[nm]
                break
            elif vals[nm] in STATUS_VALUE[nm]:
                state = STATUS_VALUE[nm][vals[nm]]
                break
    if state:
        rec_state = clodoo.browseL8(ctx, model, rec_id).state
        if state != rec_state:
            raise IOError(
                "!!Invalid %s record %s status <%s> expected <%s>"
                % (model, rec_id, rec_state, state)
            )
        ctx["ctr"] += 1


def set_wrong_data(vals, mode):
    if (
        mode == "wrong"
        and vals.get("name") == "Mario"
        and vals.get("surename") == "Rossi"
    ):
        vals["name"], vals["surename"] = vals["surename"], vals["name"]
    for nm in WRONG_DATA:
        if nm in vals:
            if mode == "wrong" and vals[nm] == WRONG_DATA[nm][0]:
                vals[nm] = WRONG_DATA[nm][1]
                if nm == "region" in vals and "region_id" in vals:
                    del vals["region_id"]
            elif vals[nm] == "$":
                vals[nm] = ""
    return vals


def load_n_test_model(
    ctx,
    model,
    default,
    mode=None,
    store=None,
    identity=None,
    ext_model=None,
    test_suppl=None,
    fct_test=None,
):
    fct_test = fct_test or "synchro"
    write_log(
        ctx,
        "\n%s: load_n_test_model(ctx, %s, mode=%s, pfx=%s, fct=%s)\n"
        % (
            datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),
            model,
            mode,
            identity,
            fct_test or "trigger",
        ),
    )

    def check_childs(
        ctx, model, rec_id, vals_line, identity, mode=None, spec=None, state=None
    ):
        xmodel = "%s.%s" % (model, spec) if spec else model
        child_model = TABLE_OF_REF_CHILD[xmodel][0]
        childs = TABLE_OF_REF_CHILD[xmodel][1]
        child_ids = clodoo.browseL8(ctx, model, rec_id)[childs]
        parent_field = TABLE_OF_REF_CHILD[xmodel][2]
        multi = TABLE_OF_REF_CHILD[xmodel][6]
        num_details = len(vals_line)
        if model == "account.invoice":
            num_details += 2
        if ctx["conai"]:
            num_details += 1
        if multi and len(child_ids) != num_details:
            raise IOError(
                "!!Wrong len(%s[%d].line_ids)==%d: expected %d!"
                % (model, rec_id, len(child_ids), num_details)
            )
        ctx["ctr"] += 1
        rec_type = TABLE_OF_REF_CHILD[xmodel][5]
        if multi:
            for ix, child_vals in enumerate(vals_line):
                child_vals[":%s" % parent_field] = rec_id
                ext_child_id = child_vals.get("%sid" % identity) or child_vals.get("id")
                child_id = get_id_from_vg7id(
                    ctx,
                    child_model,
                    ext_child_id,
                    name="%s_id" % identity.split(":")[0],
                )
                general_check(
                    ctx,
                    child_model,
                    child_id,
                    jacket_vals(child_vals, identity),
                    mode="child",
                    state=state,
                )
                store_ext_id(ctx, child_model, child_id, ext_child_id, identity)
        else:
            check_child_record(
                ctx,
                rec_id,
                rec_type,
                test_vals,
                vals,
                vals_line,
                identity,
                mode=mode,
                state=state,
            )

    def check_child_record(
        ctx,
        rec_id,
        rec_type,
        test_vals,
        vals,
        child_vals,
        identity,
        mode=None,
        state=None,
    ):
        child_vals = set_wrong_data(child_vals, mode)
        if rec_type == "product":
            model = "product.product"
            child_id = clodoo.browseL8(ctx, model, rec_id).product_tmpl_id
            if not child_id:
                raise IOError("!!Missing product.template ref of rec %d!" % rec_id)
            ctx["ctr"] += 1
            child_id = child_id.id
            child_model = "product.template"
            for field in test_vals.keys():
                del child_vals[field]
            general_check(ctx, child_model, child_id, child_vals, state=state)
            # store_child_vg7id(child_model,
            #     child_id, child_vals['%sid' % identity], identity)
        elif rec_type in ("delivery", "invoice"):
            model = "res.partner"
            ids = clodoo.searchL8(
                ctx, model, [("parent_id", "=", rec_id), ("type", "=", rec_type)]
            )
            if not ids:
                if (
                    child_vals.get("customer_billing_id") not in (11, 12)
                    and child_vals.get("customer_shipping_id") != 102
                ):
                    raise IOError(
                        "!!Missing child record type %s of rec %d!" % (rec_type, rec_id)
                    )
                return
            ctx["ctr"] += 1
            child_id = ids[0]
            child_model = model
            for field in test_vals.keys():
                del child_vals[field]
            if identity.startswith("vg7"):
                if rec_type == "delivery":
                    child_vals["id"] = child_vals["customer_shipping_id"]
                    del child_vals["customer_shipping_id"]
                elif rec_type == "invoice":
                    child_vals["id"] = child_vals["customer_billing_id"]
                    del child_vals["customer_billing_id"]
            general_check(
                ctx,
                child_model,
                child_id,
                jacket_vals(child_vals, identity),
                mode=rec_type,
                state=state,
            )
            if rec_type == "delivery":
                store_ext_id(
                    ctx, child_model, child_id, child_vals["%sid" % identity], identity
                )

    def get_ext_id_from_vals(vals):
        ext_id = False
        if vals.get("id"):
            ext_id = vals["id"]
        elif vals.get("customer_shipping_id"):
            ext_id = vals["customer_shipping_id"]
        elif vals.get("customer_billing_id"):
            ext_id = vals["customer_billing_id"]
        return ext_id

    def apply_4_custom(vals, mode):
        if mode == "upper" and "description" in vals:
            vals["description"] = vals["description"].upper()
        if mode == "only_amount" and "code" in vals:
            del vals["code"]
        return vals

    def get_child_values(ctx, model, identity, mode, vals, join=None):
        def get_shipping_vals(vg7_id, identity, mode):
            for item in RES_PARTNER_SHIPPING:
                if item.get("customer_id") == vg7_id:
                    return set_wrong_data(item, mode)
            return {}

        def get_billing_vals(vg7_id, identity, mode):
            for item in RES_PARTNER_BILLING:
                # TODO: why?
                if item.get("customer_id") == vg7_id:
                    return set_wrong_data(item, mode)
            return {}

        def get_payment_term_line_vals(vg7_id, identity, mode):
            vals = []
            for ix, item in enumerate(
                value_by_identity(
                    identity, PAYMENT_TERM_LINE_VG7, PAYMENT_TERM_LINE_OE8
                )
            ):
                if item["id"] == vg7_id:
                    lines = item.copy()
                    lines["id"] = lines["id"] * 10 + ix
                    vals.append(lines)
            return vals

        def get_move_line_vals(vg7_id, identity, mode):
            vals = []
            for ix, item in enumerate(
                value_by_identity(
                    identity, ACCOUNT_MOVE_LINE_VG7, ACCOUNT_MOVE_LINE_OE8
                )
            ):
                if item["id"] == vg7_id:
                    lines = item.copy()
                    lines["id"] = lines["id"] * 10 + ix
                    vals.append(lines)
            return vals

        def get_sale_order_line_vals(vg7_id, identity, mode):
            vals = []
            for ix, item in enumerate(
                value_by_identity(identity, SALE_ORDER_LINE_VG7, SALE_ORDER_LINE_OE8)
            ):
                if item["id"] == vg7_id:
                    lines = item.copy()
                    lines["id"] = lines["id"] * 10 + ix
                    vals.append(lines)
            return vals

        def get_ddt_line_vals(vg7_id, identity, mode):
            vals = []
            for ix, item in enumerate(
                value_by_identity(
                    identity,
                    STOCK_PICKING_PACKAGE_PREPARATION_LINE_VG7,
                    STOCK_PICKING_PACKAGE_PREPARATION_LINE_OE8,
                )
            ):
                if item["id"] == vg7_id:
                    lines = item.copy()
                    lines["id"] = lines["id"] * 10 + ix
                    vals.append(lines)
            return vals

        def get_invoice_line_vals(vg7_id, identity, mode):
            vals = []
            for ix, item in enumerate(
                value_by_identity(
                    identity, ACCOUNT_INVOICE_LINE_VG7, ACCOUNT_INVOICE_LINE_OE8
                )
            ):
                if item["id"] == vg7_id:
                    lines = item.copy()
                    lines["id"] = lines["id"] * 10 + ix
                    vals.append(lines)
            return vals

        child_model = TABLE_OF_REF_CHILD[model][0]
        parent_field = TABLE_OF_REF_CHILD[model][2]
        ext_child_field = False
        if TABLE_OF_REF_CHILD[model][3]:
            ext_child_field = TABLE_OF_REF_CHILD[model][3].get(identity.split(":")[0])
        fct = TABLE_OF_REF_CHILD[model][4]
        vals_line = locals()[fct](vals.get("id"), identity, mode)
        if ext_child_field and join:
            vals[ext_child_field] = vals_line
        return vals, vals_line, parent_field, ext_child_field, child_model

    if not ext_model:
        if identity.startswith("vg7") and model in TNL_VG7_TABLES:
            ext_model = TNL_VG7_TABLES[model]
        elif identity.startswith("oe8"):
            ext_model = model
        else:
            ext_model = model
            model = False
    vals_shipping = vals_billing = vals_line = {}
    main_ext_id = False
    wa = wal = "w"
    for datas in default:
        vals = datas.copy()
        test_vals = get_some_default(model, vals, identity, {})
        if ext_model in ("customers_shipping_addresses", "customers_billing_addresses"):
            shirt_vals(vals)
        for field in datas:
            if field in vals and vals[field] is None:
                del vals[field]
                continue
            loc_name, dummy = get_loc_name(model, field, identity)
            if not ctx["conai"] and field == "conai_id":
                del vals[field]
                continue
            if (identity and is_untranslable(loc_name, field, vals)) or (
                not identity and not is_untranslable(loc_name, field, vals)
            ):
                del vals[field]
        if identity.startswith("oe8") and model in MODEL_WITH_COMPANY:
            vals["company_id"] = EXT_COMPANY_ID

        parent_field = ext_child_field = child_model = False
        if identity == "vg7:" and model == "res.partner" and mode != "wrong":
            for xmodel in ("res.partner.shipping", "res.partner.invoice"):
                if xmodel == "res.partner.invoice":
                    (
                        vals,
                        vals_billing,
                        parent_field,
                        ext_child_field,
                        child_model,
                    ) = get_child_values(ctx, xmodel, identity, mode, vals, join=True)
                else:
                    (
                        vals,
                        vals_shipping,
                        parent_field,
                        ext_child_field,
                        child_model,
                    ) = get_child_values(ctx, xmodel, identity, mode, vals, join=True)
        elif model in MODEL_WITH_CHILD:
            (
                vals,
                vals_line,
                parent_field,
                ext_child_field,
                child_model,
            ) = get_child_values(ctx, model, identity, mode, vals, join=True)

        if not main_ext_id and vals.get("id"):
            main_ext_id = vals["id"]
        if store:
            if ext_child_field and fct_test == "trigger" and child_model:
                child_ids = []
                for datas in vals[ext_child_field]:
                    child_ids.append(datas["id"])
                    write_file_2_pull(child_model, datas, wal, identity=identity)
                    wal = "a"
            datas = vals.copy()
            if ext_child_field and fct_test != "trigger":
                datas[ext_child_field] = '"%s"' % datas[ext_child_field]
            elif ext_child_field and fct_test == "trigger" and child_model:
                datas[ext_child_field] = '"%s"' % child_ids
                vals[ext_child_field] = child_ids
            write_file_2_pull(ext_model, datas, wa, identity=identity)
            wa = "a"
        vals = apply_4_custom(vals, mode)
        vals = set_wrong_data(vals, mode)
        ext_id = get_ext_id_from_vals(vals)
        if not store and fct_test == "trigger":
            fct_test = "synchro"
        if model:
            if fct_test == "synchro":
                rec_id, vals = test_function_synchro(
                    ctx, model, vals, identity=identity, ext_id=ext_id
                )
            elif fct_test == "synchro2":
                rec_id, vals = test_function_synchro2(
                    ctx,
                    model,
                    vals,
                    parent_field,
                    ext_child_field,
                    child_model,
                    identity=identity,
                    ext_id=ext_id,
                )
            else:
                rec_id, vals = test_function_trigger(
                    ctx, ext_model, vals, identity, ext_id
                )
            hash = "%s%s:%s" % (identity, model, mode)
            if hash in FAILED_TRX and ext_id in FAILED_TRX[hash]:
                if rec_id == FAILED_TRX[hash][ext_id]:
                    ctx["ctr"] += 1
                    continue
                raise IOError(
                    "!!%s.syncro(%d) failed(%d): expected %s!"
                    % (model, ext_id, rec_id, FAILED_TRX[hash][ext_id])
                )
            elif rec_id < 1:
                raise IOError("!!%s.syncro(%d) failed(%d)!" % (model, ext_id, rec_id))
            if test_vals:
                vals.update(test_vals)
            if fct_test == "synchro2" and model in MODEL_TO_COMMIT:
                if "state" in vals:
                    vals["state"] = "draft"
                general_check(ctx, model, rec_id, vals, mode=mode, state="draft")
            else:
                general_check(ctx, model, rec_id, vals, mode=mode)
            if identity == "vg7:" and model == "product.product":
                check_childs(ctx, model, rec_id, vals, identity, mode=mode)
            elif model == "res.partner":
                if vals_shipping:
                    check_childs(
                        ctx,
                        model,
                        rec_id,
                        vals_shipping,
                        identity,
                        mode=mode,
                        spec="shipping",
                    )
                if vals_billing:
                    check_childs(
                        ctx,
                        model,
                        rec_id,
                        vals_billing,
                        identity,
                        mode=mode,
                        spec="invoice",
                    )
            elif model in MODEL_WITH_CHILD:
                if vals_line:
                    if fct_test == "synchro2" and model in MODEL_TO_COMMIT:
                        check_childs(
                            ctx,
                            model,
                            rec_id,
                            vals_line,
                            identity,
                            mode=mode,
                            state="draft",
                        )
                    else:
                        check_childs(ctx, model, rec_id, vals_line, identity, mode=mode)
            if fct_test == "synchro2" and model in MODEL_TO_COMMIT:
                if test_vals:
                    vals.update(test_vals)
                commit(ctx, model, rec_id, vals)
    return main_ext_id


def reset_model(
    ctx, model, default, company_id=None, identity=None, tnl=None, only_def=None
):
    if not ctx["conai"] and "conai" in model:
        return
    print("Reset model %s (%s) ..." % (model, identity))

    ext_id = False
    loc_id = False
    if identity:
        ext_name = "%s_id" % identity.split(":")[0]
    rec_ids = []
    for datas in default:
        vals = {}
        for field in datas:
            if datas[field] is None:
                continue
            if identity:
                loc_name, dummy = get_loc_name(model, field, identity)
            else:
                loc_name = field
            if loc_name == "id":
                if not identity:
                    loc_id, dummy = get_ext_value(
                        ctx, model, field, field, "id", datas, "", identity=identity
                    )
                elif identity and ext_name:
                    ext_id, dummy = get_ext_value(
                        ctx, model, field, field, "id", datas, "", identity=identity
                    )
                continue
            if not ctx["conai"] and field == "conai_id":
                loc_name = False
            if loc_name:
                vals[loc_name], dummy = get_ext_value(
                    ctx, model, field, field, loc_name, datas, "", identity=identity
                )
        if not vals:
            continue
        if model in SOME_DEFAULT:
            for item in SOME_DEFAULT[model]:
                if compare_some(item, vals):
                    if item["value"][1] in ctx:
                        vals[item["value"][0]] = ctx[item["value"][1]]
                    else:
                        vals[item["value"][0]] = item["value"][1]
        domain = ids = []
        if loc_id:
            ids = [loc_id]
        elif ext_id:
            domain = [(ext_name, "=", ext_id)]
            ids = clodoo.searchL8(ctx, model, domain)
        if not ids:
            for kk in CANDIDATE_KEYS:
                if kk in vals:
                    if kk in ("default_code", "name"):
                        domain = [(kk, "like", vals[kk])]
                    else:
                        domain = [(kk, "=", vals[kk])]
                    break
            if domain:
                if model == "res.country.state":
                    domain.append(("country_id", "=", ctx["res.country.IT"]))
        if domain:
            if company_id:
                domain.append(("company_id", "=", company_id))
        if domain:
            ids = clodoo.searchL8(ctx, model, domain)
        if ids:
            rec_ids += ids
            if len(ids) > 1:
                print('Warning: Too many records "%s.%s"' % (model, domain))
            if tnl:
                clodoo.writeL8(ctx, model, ids, vals)
                write_log(
                    ctx,
                    '>>> %s.write(%s, %s, ctx="en_US")' % (model, ids, vals),
                    eol=True,
                )
                if model in NAME_REFS:
                    done_tnl = False
                    for item in NAME_REFS[model]:
                        if compare_some(item, vals):
                            done_tnl = True
                            vals[item["value"][0]] = item["value"][1]
                    if done_tnl:
                        clodoo.writeL8(ctx, model, ids, vals, context={"lang": tnl})
                        write_log(
                            ctx,
                            '>>> %s.write(%s, %s, ctx="%s")' % (model, ids, vals, tnl),
                            eol=True,
                        )
            else:
                clodoo.writeL8(ctx, model, ids, vals)
                write_log(ctx, ">>> %s.write(%s, %s)" % (model, ids, vals), eol=True)
            if model in SET_DEFAULT_FROM_CTX:
                for item in SET_DEFAULT_FROM_CTX[model]:
                    if compare_some(item, vals):
                        ctx[item["value"]] = ids[0]
        else:
            print('Warning: No records found "%s.%s"' % (model, domain))
    if identity:
        if identity.startswith("vg7"):
            ext_model = TNL_VG7_TABLES[model]
        else:
            ext_model = TNL_OE8_TABLES.get(model, model)
        rm_file_2_pull(ext_model, identity)
    reset_ext_id(model)
    if only_def and rec_ids:
        delete_record(
            ctx, model, [("id", "not in", rec_ids)], multi=True, company_id=company_id
        )


def get_invalid_partners(ctx):
    return clodoo.searchL8(
        ctx,
        "res.partner",
        [
            ("parent_id", "=", False),
            "|",
            ("name", "=", False),
            "|",
            ("name", "=", ""),
            ("name", "=", " "),
        ],
    )


def get_unknown_partners(ctx):
    return clodoo.searchL8(ctx, "res.partner", [("name", "ilike", "Unknown")])


def get_duplicate_partners(ctx):
    return clodoo.searchL8(ctx, "res.partner", [("name", "like", "Rossi")]) == 1


def init_test(ctx):
    write_log(
        ctx,
        "\n%s: init_test(ctx)" % datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),
        eol=True,
    )
    print("This test requires following modules installed:")
    line = ""
    ctr = 0
    for module in MODULE_LIST:
        if module in ("connector_vg7_conai", "l10n_it_conai") and not ctx["conai"]:
            continue
        if len(line) > 40:
            print(line)
            line = ""
        if not line:
            ctr += 1
            line = "%d. " % ctr
        else:
            line += ", "
        line += module
    if ctx["ask"]:
        input("Requirements are satisfied?")
    # Log level debug
    clodoo.executeL8(ctx, "ir.model.synchro.cache", "set_loglevel", 0, "debug")
    reset_cache(ctx)

    model = "ir.module.module"
    if ctx["chk_module"]:
        for modname in MODULE_LIST:
            vals = {"name": modname}
            clodoo.executeL8(ctx, model, "synchro", vals)
        time.sleep(4)
    for modname in MODULE_LIST:
        print("checking module %s ..." % modname)
        module_ids = clodoo.searchL8(ctx, model, [("name", "=", modname)])
        if not module_ids:
            raise IOError("Module %s does not exist!!!" % modname)
        module = clodoo.browseL8(ctx, model, module_ids[0])
        if modname in ("connector_vg7_conai", "l10n_it_conai"):
            if ctx["conai"] and module.state != "installed":
                raise IOError("Module %s not installed!!!" % modname)
            elif not ctx["conai"] and module.state == "installed":
                raise IOError(
                    "Module %s installed! Please use --conai option" % modname
                )
        elif module.state != "installed":
            raise IOError("Module %s not installed!!!" % modname)

    model = "res.lang"
    if ctx["lang"] not in ("en_US", "."):
        vals = {"code": ctx["lang"]}
        print("Installing language %s ..." % vals["code"])
        clodoo.executeL8(ctx, model, "synchro", vals)

    ctx["company_id"] = env_ref(ctx, "z0bug.mycompany")
    if not ctx["company_id"]:
        raise IOError("!!Internal error: no company to test found!")

    print("Initializing environment ...")
    model = "res.company"
    company = clodoo.browseL8(ctx, model, ctx["company_id"])
    if not company.country_id or company.name != "Test Company":
        clodoo.writeL8(
            ctx,
            model,
            ctx["company_id"],
            {"country_id": env_ref(ctx, "base.it"), "name": "Test Company"},
        )

    # Default values for current user
    model = "res.users"
    user_id = env_ref(ctx, "base.user_root")
    if user_id != ctx["user_id"]:
        raise IOError(
            "!!Invalid current user id %s; set %s!" % (ctx["user_id"], user_id)
        )
    user = clodoo.browseL8(ctx, model, ctx["user_id"])
    if user.login != ctx["lgi_user"]:
        raise IOError(
            "!!Invalid current user login %s; set %s!" % (user.login, ctx["lgi_user"])
        )
    vals = {}
    if user.company_id.id != ctx["company_id"]:
        vals["company_id"] = ctx["company_id"]
    if ctx["lang"] != "." and user.lang != ctx["lang"]:
        vals["lang"] = ctx["lang"]
    if vals:
        clodoo.writeL8(ctx, "res.users", ctx["user_id"], vals)
        write_log(ctx, ">>> res.users.write(%s, %s)" % (ctx["user_id"], vals), eol=True)
        ctx["lang"] = clodoo.browseL8(ctx, model, ctx["user_id"]).lang
    # Set message note
    ctx["company_note"] = "Si prega di controllate i dati entro le 24h."
    vals = {"sale_note": ctx["company_note"]}
    clodoo.writeL8(ctx, "res.company", ctx["company_id"], vals)
    write_log(
        ctx, ">>> res.company.write(%s, %s)" % (ctx["company_id"], vals), eol=True
    )
    # Configure VG7 channel
    # Wrong method. Will be set forward, in order to test cache too
    model = "synchro.channel"
    write_record(
        ctx,
        model,
        [],
        {"method": "JSON", "exchange_path": get_csv_path("vg7:"), "tracelevel": "4"},
    )
    if not ctx.get("_cr"):
        print("No sql support found!")
        if ctx["ask"]:
            input("Press RET to continue")
    else:
        for query in (
            "delete from procurement_order",
            "delete from stock_pack_operation",
            # 'delete from stock_picking',
            "delete from stock_move",
            "stock_quant",
            "stock_inventory",
        ):
            try:
                clodoo.exec_sql(ctx, query)
            except BaseException:
                pass

    write_log(
        ctx,
        "\n%s: *** Write initial records ***"
        % (datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")),
        eol=True,
    )
    for model, domain, ctx["company_id"], vals in (
        ("account.journal", [], ctx["company_id"], {"update_posted": True}),
    ):
        write_record(ctx, model, domain, vals, company_id=ctx["company_id"])

    write_log(
        ctx,
        "\n%s: *** Delete records ***"
        % (datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")),
        eol=True,
    )
    for model, domains, company_id, multi, childs, action in (
        (
            "account.invoice",
            -1,
            ctx["company_id"],
            True,
            None,
            ["move_name=", "action_invoice_cancel"],
        ),
        (
            "stock.picking.package.preparation",
            -1,
            ctx["company_id"],
            True,
            None,
            ["set_draft", "action_cancel"],
        ),
        ("sale.order", -1, ctx["company_id"], True, None, "action_cancel"),
        ("purchase.order", -1, ctx["company_id"], True, None, "button_cancel"),
        ("account.move", -1, ctx["company_id"], True, None, "button_cancel"),
        ("account.payment.term", -1, ctx["company_id"], True, None, None),
        ("res.partner.bank", [], False, True, None, None),
        ("res.partner", -1, False, True, "child_ids", None),
        (
            "res.partner",
            [("name", "like", "Partner A%"), ("type", "=", "contact")],
            False,
            True,
            "child_ids",
            None,
        ),
        (
            "res.partner",
            [("name", "=", "La Romagnola srl"), ("type", "=", "contact")],
            False,
            True,
            "child_ids",
            None,
        ),
        (
            "res.partner",
            [("fiscalcode", "=", "RSSMRA60T45L219M")],
            False,
            True,
            "child_ids",
            None,
        ),
        ("res.partner", [("name", "=like", "Unknown %")], False, True, False, None),
        (
            "product.template",
            [("default_code", "in", ["AA", "AAA", "BB", "BBB", "CC", "CCC"])],
            False,
            True,
            False,
            False,
        ),
        (
            "product.product",
            [("default_code", "in", ["AA", "AAA", "BB", "BBB", "CC", "CCC"])],
            False,
            True,
            False,
            False,
        ),
        ("product.uom", [("name", "in", ["NR", "KG"])], False, False, False, False),
        ("account.payment.term", -1, ctx["company_id"], True, None, None),
        ("account.tax", -1, ctx["company_id"], True, None, None),
        ("res.country.state", -1, False, True, None, None),
        ("stock.picking.goods_description", -1, False, True, None, None),
        ("crm.team", [("name", "=", "Sale Example Team")], False, False, None, None),
        (
            "account.account",
            [("code", "=", "180111")],
            ctx["company_id"],
            False,
            None,
            None,
        ),
        ("ir.model.synchro.data", [], False, True, None, None),
        ("res.users", [("login", "=", "admbot")], False, False, None, None),
        ("res.partner", [("name", "=", "admbot")], False, False, None, None),
        (
            "res.partner.bank",
            [("acc_number", "=", TEST_IBAN)],
            ctx["company_id"],
            False,
            None,
            None,
        ),
    ):
        delete_record(
            ctx,
            model,
            domains,
            multi=multi,
            action=action,
            childs=childs,
            company_id=company_id,
        )

    write_log(
        ctx,
        "\n%s: *** Reset model ***"
        % (datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")),
        eol=True,
    )
    for model, datas, identity, company_id, tnl, only_def in (
        (
            "account.account.type",
            ACCOUNT_ACCOUNT_TYPE_DEF,
            "oe8:",
            False,
            "it_IT",
            True,
        ),
        (
            "account.account",
            ACCOUNT_ACCOUNT_DEF,
            "oe8:",
            ctx["company_id"],
            False,
            False,
        ),
        ("res.country", RES_COUNTRY_VG7, "vg7:", False, False, False),
        ("res.country", RES_COUNTRY_OE8, "oe8:", False, False, False),
        # ('res.country.state',
        #  RES_COUNTRY_STATE_VG7, 'vg7:', False, False, False),
        ("res.country.state", RES_COUNTRY_STATE_OE8, "oe8:", False, False, False),
        ("res.partner", RES_PARTNER_DEF, False, False, False, False),
        ("res.company", [], "oe8:", False, False, False),
        ("res.users", [], "oe8:", False, False, False),
        ("italy.conai.product.category", CONAI_PROD_DEF, False, False, False, False),
        ("product.uom", PRODUCT_UOM_DEF, False, False, False, False),
        ("product.template", PRODUCT_TEMPLATE_DEF, False, False, "it_IT", False),
        ("product.product", PRODUCT_PRODUCT_DEF, False, False, False, False),
        (
            "account.payment.term",
            PAYMENT_TERM_DEF,
            False,
            ctx["company_id"],
            False,
            False,
        ),
        ("account.tax", ACCOUNT_TAX_DEF, False, ctx["company_id"], False, False),
        (
            "stock.picking.transportation_reason",
            STOCK_PICKING_TRANSPORTATION_REASON_VG7,
            False,
            False,
            False,
            False,
        ),
    ):
        reset_model(
            ctx,
            model,
            datas,
            company_id=company_id,
            identity=identity,
            tnl=tnl,
            only_def=only_def,
        )

    channel_ids = clodoo.searchL8(ctx, "synchro.channel", [("identity", "!=", "odoo")])
    if channel_ids:
        model = "synchro.channel.model"
        delete_record(
            ctx, model, [("synchro_channel_id", "!=", channel_ids[0])], multi=True
        )
    if not company.due_cost_service_id:
        raise IOError("!!Missed bank cost in company!!")
    return ctx


def compare(ctx, rec_value, ext_value, mode):
    if mode == "nounknown":
        return not rec_value.startswith("Unknown")
    elif mode == "unknown":
        return rec_value.startswith("Unknown")
    elif mode == "individual":
        return rec_value in ctx["partner_MR_ids"]
    elif mode == "nocase":
        return rec_value.lower() == ext_value.lower()
    elif mode and mode == ext_value:
        if mode == "supplier":
            return rec_value == "contact"
        return rec_value == ext_value
    elif mode == "delivery":
        return rec_value == ext_value + 100000000
    elif mode == "invoice":
        return rec_value == ext_value + 200000000
    elif isinstance(rec_value, basestring) and isinstance(ext_value, int):
        return rec_value == str(ext_value)
    elif ext_value is None:
        return True
    elif rec_value or ext_value:
        return rec_value == ext_value
    return True


def general_check(ctx, model, loc_id, vals, mode=None, state=None):
    write_log(ctx, ">>> %s.general_check(%s, %s)" % (model, loc_id, vals), eol=True)
    if not loc_id or loc_id < 1:
        raise IOError("!!%s.syncro(%d) failed!" % (model, loc_id))
    spec = False
    if model.startswith("res.partner.") and model != "res.partner.bank":
        spec = {
            "shipping": "delivery",
            "billing": "invoice",
            "supplier": "supplier",
            "company": "company",
        }[model.split(".")[-1]]
        model = "res.partner"
    elif model == "res.partner" and mode in ("delivery", "invoice"):
        spec = mode
    loc_rec = clodoo.browseL8(ctx, model, loc_id)
    if spec:
        if not compare(ctx, loc_rec.type, spec, spec):
            raise IOError(
                "!!Field %s[%s].%s: invalid value <%s> expected <%s>"
                % (model, loc_id, "type", loc_rec.type, spec)
            )
        ctx["ctr"] += 1
    if model == "res.partner" and "vg7:billing" in vals:
        for nm in (
            "piva",
            "cf",
            "esonerato_fe",
            "codice_univoco",
            "bank_id",
            "payment_id",
            "pec",
            "street",
            "street_number",
        ):
            if "billing_%s" % nm in vals["vg7:billing"]:
                vals["vg7:%s" % nm] = vals["vg7:billing"]["billing_%s" % nm]
    identity = False
    for ext_ref in vals:
        if ext_ref.startswith("vg7:") or ext_ref.startswith("oe8:"):
            identity = ext_ref[0:4]
            break
    for ext_ref in vals:
        if ext_ref in UNCHECK_FIELDS:
            continue
        if model in UNCHECK_MODEL_FIELDS and ext_ref in UNCHECK_MODEL_FIELDS[model]:
            continue
        # Odoo BUG !?
        if (
            model == "res.partner"
            and ext_ref == "vg7:piva"
            and loc_rec.type != "contact"
        ):
            continue
        loc_name = ext_name = ext_ref
        mode2 = False
        if ext_ref in ("vg7:id", "oe8:id"):
            loc_name = ext_ref.replace(":", "_")
            ext_name = "id"
            if model == "res.partner" and spec == "supplier":
                loc_name = "vg72_id"
        elif ext_ref.startswith("vg7:") or ext_ref.startswith("oe8:"):
            identity = ext_ref[0:4]
            ext_name = ext_ref[4:]
            loc_name, mode2 = get_loc_name(model, ext_ref, identity)
            if loc_name == ext_ref:
                loc_name, mode2 = get_loc_name(model, ext_name, identity)
        elif ext_ref.startswith(":"):
            identity = ""
            ext_name = ""
            loc_name = ext_ref[1:]
        if not loc_name:
            continue
        if not ctx["conai"] and "conai" in loc_name:
            continue
        if loc_name in ("vg7_id", "oe8_id") and mode == "child":
            continue
        if (
            model in UNCHECK_DRAFT_FIELDS
            and loc_name in UNCHECK_DRAFT_FIELDS[model]
            and state == "draft"
        ):
            continue
        mode_compare = False
        if mode == "upper" and mode2 == "nocase":
            mode_compare = mode2
        elif mode == "only_amount" and mode2 == "nounknown":
            mode_compare = mode2

        loc_value, mode2 = get_loc_value(
            ctx, model, loc_rec, ext_ref, ext_name, loc_name, vals, identity, spec
        )
        transcode = True
        if mode == "tnx":
            transcode = False
        else:
            mode_compare = mode_compare or mode2
        ext_value, mode2 = get_ext_value(
            ctx,
            model,
            ext_ref,
            ext_name,
            loc_name,
            vals,
            spec,
            identity=identity,
            transcode=transcode,
            state=state,
        )
        mode_compare = mode_compare or mode2
        if loc_name == "vg7_id":
            mode_compare = spec
        if vals[ext_ref] == "" and not mode:
            continue
        if not compare(ctx, loc_value, ext_value, mode_compare):
            raise IOError(
                "!!Field %s[%s].%s: invalid value <%s> expected <%s> # %s"
                % (model, loc_id, loc_name, loc_value, ext_value, mode)
            )
        ctx["ctr"] += 1
        if model == "account.account.type" and loc_name == "name":
            for item in ACCOUNT_ACCOUNT_TYPE_DEF:
                if loc_rec.name == item["name"]:
                    xref = item["id"]
                    id = env_ref(ctx, xref)
                    if loc_id != id:
                        raise IOError(
                            "!!Field %s[%s].%s: invalid value <%s> expected <%s> # %s"
                            % (model, loc_id, loc_name, loc_id, id, loc_rec.name)
                        )
                    ctx["ctr"] += 1
        if mode == "individual":
            if not compare(ctx, loc_rec.name, "Rossi Mario", False):
                raise IOError(
                    "!!Field %s[%s].%s: invalid value <%s> expected <%s>"
                    % (model, loc_id, "name", loc_rec.name, "Rossi Mario")
                )
            ctx["ctr"] += 1
            if not compare(ctx, loc_rec.individual, True, False):
                raise IOError(
                    "!!Field %s[%s].%s: invalid value <%s> expected <%s>"
                    % (model, loc_id, "individual", loc_rec.individual, False)
                )
            ctx["ctr"] += 1
    if model == "res.partner" and loc_rec.type == "contact":
        if not compare(ctx, loc_rec.is_company, True, False):
            raise IOError(
                "!!Field %s[%s].%s: invalid value <%s> expected <%s>"
                % (model, loc_id, "is_company", loc_rec.is_company, True)
            )
        ctx["ctr"] += 1
    if model == "res.partner" and loc_rec.type != "contact":
        if not compare(ctx, loc_rec.is_company, bool(loc_rec.name), False):
            raise IOError(
                "!!Field %s[%s].%s: invalid value <%s> expected <%s>"
                % (model, loc_id, "is_company", loc_rec.is_company, bool(loc_rec.name))
            )
        ctx["ctr"] += 1


def test_synchro_vg7(ctx):
    print("Test synchronization VG7 module")
    ctx["ctr"] = 0

    def test_company(ctx, mode=None, identity=None, fct_test=None):
        identity = identity or "oe8:"
        model = "res.company"
        print("Write %s (%s) ..." % (model, identity))
        load_n_test_model(
            ctx,
            model,
            RES_COMPANY_VG7 if identity == "vg7:" else RES_COMPANY_OE8,
            mode=mode,
            store=not mode,
            identity=identity,
        )

    def test_user(ctx, mode=None, identity=None, fct_test=None):
        identity = identity or "oe8:"
        model = "res.users"
        print("Write %s (%s) ..." % (model, identity))
        load_n_test_model(
            ctx,
            model,
            RES_USERS_VG7 if identity == "vg7:" else RES_USERS_OE8,
            mode=mode,
            store=not mode,
            identity=identity,
        )

    def test_country(ctx, mode=None, identity=None, fct_test=None):
        identity = identity or "vg7:"
        model = "res.country"
        print("Write %s (%s) ..." % (model, identity))
        vg7_id = load_n_test_model(
            ctx,
            model,
            RES_COUNTRY_VG7 if identity == "vg7:" else RES_COUNTRY_OE8,
            mode=mode,
            store=not mode,
            identity=identity,
            fct_test=fct_test,
        )
        if identity == "vg7:":
            ctx["res.country.IT"] = vg7_id

        model = "res.country.state"
        print("Write %s (%s) ..." % (model, identity))
        vg7_id = load_n_test_model(
            ctx,
            model,
            RES_COUNTRY_STATE_VG7 if identity == "vg7:" else RES_COUNTRY_STATE_OE8,
            mode=mode,
            store=not mode,
            identity=identity,
            fct_test=fct_test,
            test_suppl="country_id",
        )
        if identity == "vg7:":
            ctx["res.country.state.MI"] = vg7_id

    def test_tax(ctx, mode=None, identity=None, fct_test=None):
        identity = identity or "vg7:"
        model = "account.tax"
        print("Write %s (%s) ..." % (model, identity))
        vg7_id = load_n_test_model(
            ctx,
            model,
            ACCOUNT_TAX_VG7 if identity == "vg7:" else ACCOUNT_TAX_OE8,
            mode=mode,
            store=not mode,
            identity=identity,
            fct_test=fct_test,
        )
        if identity == "vg7:":
            ctx["account.tax.22v"] = vg7_id

    def test_payment(ctx, mode=None, identity=None, fct_test=None):
        identity = identity or "vg7:"
        model = "account.payment.term"
        print("Write %s (%s) ..." % (model, identity))
        if identity.startswith("oe8"):
            store_oe8id(ctx, "account.payment.term.line", "percent", "procent")
        vg7_id = load_n_test_model(
            ctx,
            model,
            PAYMENT_TERM_VG7 if identity == "vg7:" else PAYMENT_TERM_OE8,
            mode=mode,
            store=not mode,
            identity=identity,
            fct_test=fct_test,
        )
        if identity == "vg7:":
            ctx["account.payment.term.30GG"] = vg7_id

    def test_conai(ctx, mode=None, identity=None, fct_test=None):
        identity = identity or "vg7:"
        model = "italy.conai.product.category"
        print("Write %s (%s) ..." % (model, identity))
        vg7_id = load_n_test_model(
            ctx, model, CONAI_PROD_VG7, mode=mode, store=not mode, identity="vg7:"
        )
        if identity == "vg7:":
            ctx["italy.conai.product.category.CA"] = vg7_id

    def test_uom(ctx, mode=None, identity=None, fct_test=None):
        identity = identity or "vg7:"
        model = "product.uom"
        print("Write %s (%s) ..." % (model, identity))
        vg7_id = load_n_test_model(
            ctx,
            model,
            PRODUCT_UOM_VG7 if identity == "vg7:" else PRODUCT_UOM_OE8,
            mode=mode,
            store=not mode,
            identity=identity,
            fct_test=fct_test,
        )
        if identity == "vg7:":
            ctx["product.uom.NR"] = vg7_id

    def test_product(ctx, mode=None, identity=None, fct_test=None):
        identity = identity or "vg7:"
        if identity == "oe8:":
            model = "product.template"
            print("Write %s (%s) ..." % (model, identity))
            load_n_test_model(
                ctx,
                model,
                PRODUCT_TEMPLATE_OE8,
                mode=mode,
                store=not mode,
                identity=identity,
                fct_test=fct_test,
            )
        model = "product.product"
        print("Write %s (%s) ..." % (model, identity))
        vg7_id = load_n_test_model(
            ctx,
            model,
            PRODUCT_PRODUCT_VG7 if identity == "vg7:" else PRODUCT_PRODUCT_OE8,
            mode=mode,
            store=not mode,
            identity=identity,
            fct_test=fct_test,
        )
        if identity == "vg7:":
            ctx["product.product.A"] = vg7_id

    def test_partner(ctx, mode=None, identity=None, fct_test=None):
        identity = identity or "vg7:"
        model = "res.partner"
        print("Write %s (%s) ..." % (model, identity))
        if not mode and identity == "vg7:":
            load_n_test_model(
                ctx,
                "res.partner.shipping",
                RES_PARTNER_SHIPPING,
                mode=mode,
                store=not mode,
                identity=identity,
            )
            load_n_test_model(
                ctx,
                "customers_billing_addresses",
                RES_PARTNER_BILLING,
                mode=mode,
                store=not mode,
                identity=identity,
            )
        vg7_id = load_n_test_model(
            ctx,
            model,
            RES_PARTNER_VG7 if identity == "vg7:" else RES_PARTNER_OE8,
            mode=mode,
            store=not mode,
            identity=identity,
        )
        if mode and identity == "vg7:":
            bank_id = load_n_test_model(
                ctx,
                "res.partner.bank",
                RES_PARTNER_BANK_VG7,
                mode=True,
                store=True,
                identity=identity,
            )
            ctx["res.partner.bank.BPop"] = bank_id

        if identity == "vg7:":
            ctx["res.partner.A"] = vg7_id
            model = "res.partner.supplier"
            print("Write %s (%s) ..." % (model, identity))
            vg7_id = load_n_test_model(
                ctx,
                model,
                RES_PARTNER_SUPPLIER_VG7,
                mode=mode,
                store=not mode,
                identity=identity,
            )

        if identity == "vg7:":
            # Special error test
            model = "res.partner"
            vals = {"vg7:piva": "02345670019", "vg7:id": 12}
            rec_id, vals = test_function_synchro(ctx, model, vals, identity=identity)
            if rec_id >= 0:
                raise IOError(
                    "!!Test failed: expected error, received %s record ID" % rec_id
                )
            ctx["ctr"] += 1
            partner = clodoo.browseL8(
                ctx,
                model,
                clodoo.browseL8(
                    ctx,
                    "ir.model.synchro.log",
                    clodoo.searchL8(
                        ctx,
                        "ir.model.synchro.log",
                        [("timestamp", ">=", datetime.today().strftime("%Y-%m-%d"))],
                        order="id desc",
                    )[0],
                ).res_id,
            )
            if ("%s" % rec_id) not in partner.errmsg:
                raise IOError("!!Test failed: partner w/o errr message")
            ctx["ctr"] += 1

            clodoo.writeL8(ctx, model, partner.id, {"active": False})
            partner = clodoo.browseL8(ctx, model, partner.id)
            if partner.active:
                raise IOError("!!Internal error: partner active")
            vals = {"vg7:company": partner.name, "vg7:piva": partner.vat, "vg7:id": 12}
            rec_id, vals = test_function_synchro(ctx, model, vals, identity=identity)
            if rec_id != partner.id:
                raise IOError("!!Test failed: wrong partner ID")
            ctx["ctr"] += 1
            partner = clodoo.browseL8(ctx, model, partner.id)
            if not partner.active:
                raise IOError("!!Test failes: partner not active")
            ctx["ctr"] += 1

    def test_account_type(ctx, mode=None, identity=None, fct_test=None):
        identity = identity or "oe8:"
        model = "account.account.type"
        print("Write %s (%s) ..." % (model, identity))
        load_n_test_model(
            ctx,
            model,
            ACCOUNT_ACCOUNT_TYPE_OE8,
            mode=mode,
            store=not mode,
            identity="oe8:",
            fct_test="trigger",
        )

    def test_account(ctx, mode=None, identity=None, fct_test=None):
        identity = identity or "oe8:"
        model = "account.account"
        print("Write %s (%s) ..." % (model, identity))
        load_n_test_model(
            ctx,
            model,
            ACCOUNT_ACCOUNT_OE8,
            mode=mode,
            store=not mode,
            identity=identity,
            fct_test=fct_test,
        )

    def test_journal(ctx, mode=None, identity=None, fct_test=None):
        identity = identity or "oe8:"
        model = "account.journal"
        print("Write %s (%s) ..." % (model, identity))
        load_n_test_model(
            ctx,
            model,
            ACCOUNT_JOURNAL_VG7 if identity == "vg7:" else ACCOUNT_JOURNAL_OE8,
            mode=mode,
            store=not mode,
            identity=identity,
            fct_test=fct_test,
        )

    def test_sale_order(ctx, mode=None, identity=None, fct_test=None):
        identity = identity or "vg7:"
        model = "sale.order"
        print("Write %s (%s) ..." % (model, identity))
        vg7_id = load_n_test_model(
            ctx,
            model,
            SALE_ORDER_VG7 if identity == "vg7:" else SALE_ORDER_OE8,
            mode=mode,
            store=not mode,
            identity=identity,
            fct_test=fct_test,
        )
        if identity == "vg7:":
            ctx["sale.order.210123"] = vg7_id

    def test_invoice(ctx, mode=None, identity=None, fct_test=None):
        identity = identity or "vg7:"
        model = "account.invoice"
        print("Write %s (%s) ..." % (model, identity))
        vg7_id = load_n_test_model(
            ctx,
            model,
            ACCOUNT_INVOICE_OE8 if identity == "vg7:" else ACCOUNT_INVOICE_OE8,
            mode=mode,
            store=not mode,
            identity=identity,
            fct_test=fct_test,
        )
        if identity == "vg7:":
            ctx["account.invoice.210123"] = vg7_id

    def test_purchase_order(ctx, mode=None, identity=None, fct_test=None):
        identity = identity or "vg7:"
        model = "purchase.order"
        print("Write %s (%s) ..." % (model, identity))
        load_n_test_model(
            ctx,
            model,
            PURCHASE_ORDER_VG7 if identity == "vg7:" else PURCHASE_ORDER_OE8,
            mode=mode,
            store=not mode,
            identity=identity,
            fct_test=fct_test,
        )
        # ctx['purchase.order.210123'] = vg7_id

    def test_causale_trasporto(ctx, mode=None, identity=None, fct_test=None):
        identity = identity or "vg7:"
        model = "stock.picking.transportation_reason"
        print("Write %s (%s) ..." % (model, identity))
        vg7_id = load_n_test_model(
            ctx,
            model,
            STOCK_PICKING_TRANSPORTATION_REASON_VG7
            if identity == "vg7:"
            else STOCK_PICKING_TRANSPORTATION_REASON_OE8,
            mode=mode,
            store=not mode,
            identity=identity,
            fct_test=fct_test,
        )
        if identity == "vg7:":
            ctx["stock.picking.transportation_reason.V"] = vg7_id

    def test_ddt(ctx, mode=None, identity=None, fct_test=None):
        identity = identity or "vg7:"
        model = "stock.picking.package.preparation"
        print("Write %s (%s) ..." % (model, identity))
        vg7_id = load_n_test_model(
            ctx,
            model,
            STOCK_PICKING_PACKAGE_PREPARATION_VG7
            if identity == "vg7:"
            else STOCK_PICKING_PACKAGE_PREPARATION_OE8,
            mode=mode,
            store=not mode,
            identity=identity,
            fct_test=fct_test,
        )
        if identity == "vg7:":
            ctx["stock.picking.package.preparation.1234"] = vg7_id

    def test_account_move(ctx, mode=None, identity=None, fct_test=None):
        identity = identity or "oe8:"
        model = "account.move"
        print("Write %s (%s) ..." % (model, identity))
        load_n_test_model(
            ctx,
            model,
            ACCOUNT_MOVE_VG7 if identity == "vg7:" else ACCOUNT_MOVE_OE8,
            mode=mode,
            store=not mode,
            identity=identity,
            fct_test=fct_test,
        )

    ctx = init_test(ctx)
    # company_id = ctx['company_id']
    #
    # Repeat tests 2 times to check correct synchronization
    #
    print("*** Starting VG7 test ***")
    write_log(
        ctx,
        "\n%s: *** Starting VG7 test ***"
        % datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),
        eol=True,
    )

    test_country(ctx, identity="vg7:")
    test_country(ctx, mode="upper", identity="vg7:")

    test_tax(ctx, mode="only_amount", identity="vg7:")
    test_tax(ctx, identity="vg7:")

    test_payment(ctx, mode="wrong", identity="vg7:")
    test_payment(ctx, identity="vg7:")
    test_payment(ctx, mode=True, identity="vg7:")

    if ctx["conai"]:
        test_conai(ctx)
        test_conai(ctx, mode=True)

    test_uom(ctx, identity="vg7:")
    test_uom(ctx, mode=True)

    test_product(ctx)
    test_product(ctx, mode=True)

    test_partner(ctx, mode="wrong")
    test_partner(ctx)

    test_causale_trasporto(ctx, identity="vg7:")
    test_causale_trasporto(ctx, mode=True, identity="vg7:")

    test_sale_order(ctx, identity="vg7:", fct_test="synchro2")
    test_sale_order(ctx, mode="wrong", identity="vg7:", fct_test="synchro2")
    test_sale_order(ctx, identity="vg7:")
    test_sale_order(ctx, mode=True, identity="vg7:")

    test_ddt(ctx, identity="vg7:", fct_test="synchro2")
    test_ddt(ctx, identity="vg7:")
    test_ddt(ctx, mode=True, identity="vg7:")

    test_purchase_order(ctx, identity="vg7:", fct_test="synchro2")
    test_purchase_order(ctx, mode="wrong", identity="vg7:", fct_test="synchro2")
    test_purchase_order(ctx, identity="vg7:")
    test_purchase_order(ctx, mode=True, identity="vg7:")

    print("*** Starting OE8 test ***")
    write_log(
        ctx,
        "\n%s: *** Starting OE8 test ***"
        % datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),
        eol=True,
    )

    # Set method CSV and reset cache
    model = "synchro.channel"
    clodoo.writeL8(
        ctx,
        model,
        clodoo.searchL8(ctx, model, []),
        {"method": "CSV", "exchange_path": get_csv_path("oe8:"), "tracelevel": "4"},
    )
    reset_cache(ctx)

    test_partner(ctx, identity="oe8:", fct_test="trigger")
    test_company(ctx, identity="oe8:", fct_test="trigger")
    test_user(ctx, identity="oe8:", fct_test="trigger")
    test_country(ctx, identity="oe8:", fct_test="trigger")
    test_account_type(ctx, identity="oe8:", fct_test="trigger")
    test_account(ctx, identity="oe8:", mode="wrong", fct_test="trigger")
    test_account(ctx, identity="oe8:", fct_test="trigger")
    test_tax(ctx, identity="oe8:", fct_test="trigger")
    test_payment(ctx, identity="oe8:", fct_test="trigger")
    test_journal(ctx, identity="oe8:", mode="wrong", fct_test="trigger")
    test_journal(ctx, identity="oe8:", fct_test="trigger")
    test_causale_trasporto(ctx, identity="oe8:", fct_test="trigger")
    test_uom(ctx, identity="oe8:", fct_test="trigger")
    test_product(ctx, identity="oe8:", fct_test="trigger")
    test_sale_order(ctx, identity="oe8:", fct_test="trigger")
    test_invoice(ctx, identity="oe8:", fct_test="trigger")
    test_account_move(ctx, identity="oe8:", fct_test="trigger")

    # Final checks
    ids = get_invalid_partners(ctx)
    ids += get_unknown_partners(ctx)
    if ids:
        raise IOError("!!Found invalid or unknown res.partner records %s!" % ids)
    ctx["ctr"] += 2
    if get_duplicate_partners(ctx):
        raise IOError("!!Found duplicate res.partner records ROSSI!")
    ctx["ctr"] += 1

    print("%d tests universal_connector successfully ended" % ctx["ctr"])
    try:
        clodoo.executeL8(
            ctx,
            "ir.model.synchro.cache",
            "die",
            True
        )
    except BaseException:
        pass
    return


parser = z0lib.parseoptargs(
    "Odoo test environment", "© 2020-2022 by SHS-AV s.r.l.", version=__version__
)
parser.add_argument("-h")
parser.add_argument(
    "-c",
    "--config",
    help="configuration command file",
    dest="conf_fn",
    metavar="file",
    default="./inv2draft_n_restore.conf",
)
parser.add_argument(
    "-d",
    "--dbname",
    help="DB name to connect",
    dest="db_name",
    metavar="file",
    default="",
)
parser.add_argument(
    "-L",
    "--logfile",
    help="test logfile",
    dest="logfn",
    metavar="file",
    default="./test_synchro.log",
)
parser.add_argument(
    "-l",
    "--lang",
    help="language translation",
    metavar="iso-3166 or '.'",
    dest="lang",
    default=".",
)
parser.add_argument("-n")
parser.add_argument("-q")
parser.add_argument(
    "-U", "--login-user", help="login user to test", dest="lgi_user", default="admin"
)
parser.add_argument("-V")
parser.add_argument("-v")
parser.add_argument(
    "-1",
    "--conai",
    action="store_true",
    help="enable test conai module",
    dest="conai",
    default=False,
)
parser.add_argument(
    "-2",
    "--no-conai",
    action="store_false",
    help="disable test conai module",
    dest="conai",
)
parser.add_argument(
    "-3",
    "--no-ask",
    action="store_false",
    help="ask for some tests",
    dest="ask",
    default=True,
)
parser.add_argument(
    "-4", "--ask", action="store_true", help="execute tests w/o ask", dest="ask"
)
parser.add_argument(
    "-5",
    "--no-module",
    action="store_false",
    help="do not check for modules",
    dest="chk_module",
    default=True,
)
parser.add_argument(
    "-6", "--module", action="store_true", help="check for modules", dest="chk_module"
)

ctx = parser.parseoptargs(sys.argv[1:], apply_conf=False)
uid, ctx = clodoo.oerp_set_env(confn=ctx["conf_fn"], db=ctx["db_name"], ctx=ctx)
msg_time = time.time()
os0.set_tlog_file("./odoo_shell.log", echo=True)
if os.path.isfile(ctx["logfn"]):
    os.unlink(ctx["logfn"])
test_synchro_vg7(ctx)
exit(0)
