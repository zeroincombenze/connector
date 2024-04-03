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
import os.path as pth
import sys
import argparse
from datetime import date, datetime, timedelta
from time import sleep
import re
import csv

try:
    from python_plus.python_plus import _u
except ImportError:
    from python_plus import _u
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

EXT_COMPANY_ID = 1
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
    "account.journal": "",
    "account.move": "",
    "account.move.line": "",
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
    "purchase.order": "",
    "purchase.order.line": "",
    "res.company": "",
    "res.country": "countries",
    "res.country.state": "regions",
    "res.currency": "",
    "res.partner": "customers",
    "res.partner.bank": "banks",
    "res.partner.bank.company": "bank_accounts",
    "res.partner.billing": "",
    "res.partner.shipping": "customers_shipping_addresses",
    "res.partner.supplier": "suppliers",
    "res.users": "",
    "sale.order": "orders",
    "sale.order.line": "",
    "stock.picking.package.preparation": "ddt",
    "stock.picking.package.preparation.line": "",
    "stock.picking.transportation_reason": "causals",
}
TNL_OE8_TABLES = {}
MODEL_LIST = list(TNL_VG7_TABLES.keys())
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
THIS_MODULE = "universal_connector"
MODULE_LIST = [
    "mk_test_env",
    THIS_MODULE,
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
    "partner_bank",
    "l10n_it_conai",
    "connector_vg7_conai",
]
IDENTITY_LIST = ["vg7:", "oe8:"]


class ExtTestEnv(object):

    def __init__(self, *args):
        self.parseoptargs(args)
        for item in ("confn", "db_name", "lang"):
            setattr(self, item, getattr(self.opt_args, item))
        self.confn = self.confn or os.environ["TEST_CONFN"]
        self.db_name = self.db_name or "connect10"
        self.lang = self.lang or "it_IT"
        self.logfn = __file__.replace(".py", ".log")
        self.conai = False
        self.ask = False
        self.module = False
        self.ctr = 0
        if pth.isfile(self.logfn):
            os.unlink(self.logfn)
        self.fqn_to_remove = []

    def parseoptargs(self, args):
        parser = argparse.ArgumentParser(
            # formatter_class=argparse.RawDescriptionHelpFormatter,
            description="Odoo test environment - © 2020-2024 by SHS-AV s.r.l.",
        )
        parser.add_argument(
            "-c",
            "--config",
            help="Odoo configuration file",
            dest="confn",
            metavar="FILE",
        )
        parser.add_argument(
            "-d",
            "--database",
            help="DB name to test",
            dest="db_name",
            metavar="FILE",
        )
        parser.add_argument(
            "-l",
            "--lang",
            help="Language to test",
            metavar="ISO3166",
        )
        self.opt_args = parser.parse_args(*args)

    def write_log(self, mesg, eol=True, echo=True, no_ts=False):
        if echo:
            print(mesg)
        with open(self.logfn, "a") as fd:
            if no_ts:
                fd.write(u" - ")
            else:
                fd.write(_u(datetime.strftime(datetime.now(), u"%Y-%m-%d %H:%M:%S ")))
            fd.write(mesg)
            if eol:
                fd.write("\n")

    def env_ref(self, xref, retxref_id=None):
        def simulate_xref(name, model, by=None):
            by = by or "name"
            tok = name.split("_")[-1]
            domain = [(by, "=", tok)]
            domain.append(("company_id", "=", self.company_id))
            recs = clodoo.searchL8(self.ctx, model, domain)
            if len(recs) == 1:
                return recs[0]
            return False

        if " " in xref:
            return xref
        module, name = xref.split(".", 2)
        model = "ir.model.data"
        ids = clodoo.searchL8(
            self.ctx, model, [("module", "=", module), ("name", "=", name)]
        )
        if ids:
            if retxref_id:
                return ids[0]
            return clodoo.browseL8(self.ctx, model, ids[0]).res_id
        elif xref.startswith("z0bug.tax_"):
            return simulate_xref(name, "account.tax", by="description")
        return False

    @staticmethod
    def store_vg7id(model, loc_id, vg7_id):
        if model not in TNL_VG7_DICT:
            TNL_VG7_DICT[model] = {}
        if "EXT" not in TNL_VG7_DICT[model]:
            TNL_VG7_DICT[model]["LOC"] = {}
            TNL_VG7_DICT[model]["EXT"] = {}
        if isinstance(vg7_id, basestring) and vg7_id.isdigit():
            vg7_id = int(vg7_id)
        TNL_VG7_DICT[model]["LOC"][loc_id] = vg7_id
        TNL_VG7_DICT[model]["EXT"][vg7_id] = loc_id

    @staticmethod
    def store_oe8id(model, loc_id, oe8_id):
        if model not in TNL_OE8_DICT:
            TNL_OE8_DICT[model] = {}
        if "EXT" not in TNL_OE8_DICT[model]:
            TNL_OE8_DICT[model]["LOC"] = {}
            TNL_OE8_DICT[model]["EXT"] = {}
        if isinstance(oe8_id, basestring) and oe8_id.isdigit():
            oe8_id = int(oe8_id)
        TNL_OE8_DICT[model]["LOC"][loc_id] = oe8_id
        TNL_OE8_DICT[model]["EXT"][oe8_id] = loc_id

    def store_ext_id(self, model, loc_id, ext_id, identity):
        if loc_id and ext_id:
            if identity.startswith("vg7"):
                self.store_vg7id(model, loc_id, ext_id)
            elif identity.startswith("oe8"):
                self.store_oe8id(model, loc_id, ext_id)

    @staticmethod
    def get_ext_id_field(identity):
        return identity.split(":")[0] + "_id"

    @staticmethod
    def get_csv_path(identity="match"):
        testdir = pth.join(pth.dirname(pth.dirname(__file__)))
        root = pth.join(testdir, "data", (identity.split(":")[0]))
        if not pth.isdir(root):
            raise IOError("Directory %s not found!!!" % root)
        return root

    @staticmethod
    def get_exchange_path(identity):
        testdir = pth.join(pth.dirname(pth.dirname(__file__)))
        root = pth.join(testdir, "res", (identity.split(":")[0]))
        if not pth.isdir(root):
            os.makedirs(root)
        return root

    @staticmethod
    def get_ext_model(model, identity):
        if identity.startswith("vg7") and model in TNL_VG7_TABLES:
            ext_model = TNL_VG7_TABLES[model]
        else:
            ext_model = model
        return ext_model

    @staticmethod
    def is_untranslable(ext_ref, vals):
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

    @staticmethod
    def get_actual_model(model):
        if model in (
                "res.partner.billing",
                "res.partner.shipping",
                "res.partner.supplier"):
            return "res.partner"
        return model

    def jacket_vals(self, vals, prefix="vg7:"):
        for ext_ref in vals.copy():
            if self.is_untranslable(ext_ref, vals):
                continue
            if not ext_ref.startswith((prefix, ":")):
                ref = "%s%s" % (prefix, ext_ref)
                if vals[ext_ref] in (r"\N", "None"):
                    vals[ref] = ""
                else:
                    vals[ref] = vals[ext_ref]
                del vals[ext_ref]
        return vals

    def cast_value(self, vals):
        res = {}
        for k, v in vals.items():
            if k == "company_id" and not v:
                res[k] = self.user.company_id.id
            elif isinstance(v, basestring) and re.match(r"[0-9]*\.[0-9]+$", v):
                res[k] = eval(v)
            elif isinstance(v, basestring) and "." in v and " " not in v:
                res[k] = self.env_ref(v)
            elif k in ("id", "vg7_id", "oe8_id") and isinstance(v, basestring):
                res[k] = int(v) if v else False
            elif v in (r"\N", "None"):
                continue
            else:
                res[k] = v
        return res

    @staticmethod
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

    def load_csv_file(self, fqn):
        datas = []
        if not pth.isfile(fqn):
            raise IOError("File %s not found!" % fqn)
        with open(fqn, "r") as fd:
            header = False
            reader = csv.reader(fd)
            for row in reader:
                if not header:
                    header = row
                    continue
                datas.append(self.cast_value(dict(zip(header, row))))
        return datas

    def reset_cache(self):
        lifetime = clodoo.executeL8(
            self.ctx,
            "ir.model.synchro.cache",
            "clean_cache",
            0,
            None,  # channel_id
            None,  # model
            60,
        )  # cache lifetime
        if lifetime != 60:
            raise IOError("Invalid cache lifetime setup!!!")
        self.ctr += 1

    def delete_record(
        self, model, domains, multi=False, action=None, childs=None, company_id=False
    ):
        self.write_log(
            "delete_record(%s, %s)" % (
                model,
                domains if domains != -1 and domains != [] else "all",
                ))
        excl_list = [
            rec.res_id
            for rec in clodoo.browseL8(
                self.ctx,
                "ir.model.data",
                clodoo.searchL8(self.ctx, "ir.model.data", [("model", "=", model)]),
            )
        ]
        if model == "res.partner":
            for rec in clodoo.browseL8(
                self.ctx, "res.users",
                    clodoo.searchL8(self.ctx, "res.users", [])
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
                rec_ids = self.env_ref(domain)
                rec_ids = [rec_ids] if rec_ids else []
            elif isinstance(domain, int):
                full_domain = []
                for test_prefix in ("vg7:", "oe8:"):
                    ext_name = ("%s_id" % test_prefix.split(":")[0]
                                if test_prefix else False)
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
                rec_ids = clodoo.searchL8(self.ctx, model, domain)
            if (not multi and len(rec_ids) == 1) or (multi and len(rec_ids)):
                if action:
                    if not isinstance(action, (list, tuple)):
                        action = [action]
                    for act in action:
                        if act == "move_name=":
                            clodoo.writeL8(
                                self.ctx, model, rec_ids, {"move_name": ""})
                        else:
                            try:
                                clodoo.executeL8(self.ctx, model, act, rec_ids)
                            except BaseException:
                                print("Warning! Cannot execute %s.%s" % (model, act))
                if childs:
                    for parent in clodoo.browseL8(self.ctx, model, rec_ids):
                        for rec in parent[childs]:
                            if rec.id in rec_ids:
                                continue
                            try:
                                clodoo.unlinkL8(self.ctx, model, rec.id)
                                self.write_log("%s.unlink(%s)" % (model, rec.id))
                            except BaseException as e:
                                print("Error %s removing records ..." % e)
                try:
                    clodoo.unlinkL8(self.ctx, model, rec_ids)
                    self.write_log("%s.unlink(%s)" % (model, rec_ids))
                except BaseException as e:
                    print("Error %s removing records ..." % e)
                    if self.ask:
                        input("Press RET to continue")
                    else:
                        exit(1)

    def write_record(
            self, model, domain, vals, company_id=False, create=None, unique=None):
        self.write_log(
            "write_record(%s, %s)" % (model, domain))
        if isinstance(domain, basestring):
            ids = self.env_ref(domain)
            ids = [ids] if ids else []
        else:
            if company_id:
                domain.append(("company_id", "=", company_id))
            ids = clodoo.searchL8(self.ctx, model, domain)
        if ids:
            clodoo.writeL8(self.ctx, model, ids, vals)
            if unique and len(ids) > 1:
                self.write_log(
                    "Warning: Too many records '%s(%s)'" % (model, domain),
                    no_ts=True)
                self.delete_record(model, [("id", "in", ids[1:])])
        elif create:
            ids = [clodoo.createL8(self.ctx, model, vals)]
        return ids

    def init_new_db(self):
        # Temporary solution
        print("Be patient, the universal connector full test takes a few time ...")
        print("Please drop DB %s" % self.db_name)
        input("Press RET to continue ...")
        print("Now recreate DB %s (w/o demo data)" % self.db_name)
        input("Press RET to continue ...")
        with open(self.confn, "r") as fd:
            contents = fd.read()
        if "psycopg2 = 1" not in contents:
            with open(self.confn, "a") as fd:
                fd.write("psycopg2 = 1\n")
        uid, self.ctx = clodoo.oerp_set_env(confn=self.confn, db=self.db_name)
        if not uid:
            raise IOError("DB %s not connected via json/xmlrpc!" % self.db_name)
        self.user = self.ctx["user"]

    def set_new_db(self):
        company_id = self.env_ref("z0bug.mycompany")
        while not company_id:
            print("Activate Developer Mode and create full test environment")
            print("lang=it_IT, no new company, CoA=Zero,%s CONAI ..."
                  % " not" if self.conai else " ")
            print("You need to create only chart of account, partners and products ...")
            input("Press RET to continue ...")
            company_id = self.env_ref("z0bug.mycompany")

    def check_if_module_installed(self, modname, ctr=-1, maxctr=-1):
        if ctr >= 0 and maxctr >= 0:
            self.write_log(
                "check_if_module_installed(%s, %d/%d)" % (modname, ctr + 1, maxctr),
            )
        else:
            self.write_log("check_if_module_installed(%s)" % modname)
        model = "ir.module.module"
        module_ids = clodoo.searchL8(self.ctx, model, [("name", "=", modname)])
        if not module_ids:
            raise IOError("Module %s does not exist!!!" % modname)
        state = "uninstalled"
        if len(module_ids) == 1:
            state = clodoo.browseL8(self.ctx, model, module_ids[0]).state
        return state == "installed"

    def wait_4_module_uninstalled(self, modname):
        installed = self.check_if_module_installed(modname)
        while installed:
            print("Module %s installed!" % modname)
            print("Please uninstall %s" % modname)
            input("Press RET to continue ...")
            installed = self.check_if_module_installed(modname)
        sleep(1)

    def wait_4_module_installed(self, modname, ctr, maxctr):
        installed = False
        while not installed:
            print("Module %s not installed!" % modname)
            print("Please install %s" % modname)
            input("Press RET to continue ...")
            installed = self.check_if_module_installed(modname, ctr=ctr, maxctr=maxctr)
        sleep(1)

    def assure_company(self):
        self.company_id = self.env_ref("z0bug.mycompany")
        if not self.company_id:
            raise IOError("!!Internal error: no company to test found!")
        model = "res.company"
        company = clodoo.browseL8(self.ctx, model, self.company_id)
        if not company.country_id or company.name != "Test Company":
            clodoo.writeL8(
                self.ctx,
                model,
                self.company_id,
                {"country_id": self.env_ref("base.it"), "name": "Test Company"},
            )
        self.company_note = "Si prega di controllate i dati entro le 24h."
        vals = {"sale_note": self.company_note}
        clodoo.writeL8(self.ctx, "res.company", self.company_id, vals)
        self.write_log(
            "res.company.write(%s, %s)" % (self.company_id, vals),
        )

    def assure_cache(self):
        clodoo.executeL8(self.ctx,
                         "ir.model.synchro.cache",
                         "set_loglevel",
                         0,
                         "debug")
        self.reset_cache()

    def assure_all_backends(self):
        model = "synchro.channel"
        for backend in clodoo.browseL8(
                self.ctx, model, clodoo.searchL8(
                    self.ctx, model, [])):
            if backend.state != "draft":
                clodoo.executeL8(
                    self.ctx, model, "button_reset_to_draft", backend.id)
            if backend.prefix == "oe10":
                clodoo.writeL8(
                    self.ctx,
                    model,
                    backend.id,
                    {
                        "method": "JSON",
                        "client_key": "oca10",
                        "password": "admin",
                        "counterpart_url": "admin@localhost:8270",
                        "sequence": 20,
                        "tracelevel": "4"
                    },
                )
            else:
                clodoo.writeL8(
                    self.ctx,
                    model,
                    backend.id,
                    {
                        "method": "CSV",
                        "exchange_path": self.get_exchange_path(backend.prefix),
                        "tracelevel": "4"
                    },
                )
            clodoo.executeL8(
                self.ctx, model, "button_check_connection", backend.id)
            backend = clodoo.browseL8(self.ctx, model, backend.id)
            if backend.state != "checked":
                raise IOError(
                    "!!Backend %s[%s] not checked!" % (backend.name, backend.id))

    def assure_lang(self):
        model = "res.lang"
        if not clodoo.searchL8(self.ctx, model, [("code", "=", self.lang)]):
            vals = {"code": self.lang}
            print("Installing language %s ..." % vals["code"])
            clodoo.executeL8(self.ctx, model, "synchro", vals)

    def assure_user(self, lang=None):
        model = "res.users"
        user_id = self.env_ref("base.user_root")
        if user_id != self.user.id:
            raise IOError(
                "!!Invalid current user id %s; set %s!" % (self.user.id, user_id)
            )
        user = clodoo.browseL8(self.ctx, model, self.user.id)
        vals = {}
        if user.company_id.id != self.company_id:
            vals["company_id"] = self.company_id
        lang = lang or self.lang
        if user.lang != lang:
            vals["lang"] = lang
        if vals:
            clodoo.writeL8(self.ctx, "res.users", self.user.id, vals)
            self.write_log("res.users.write(%s, %s)" % (self.user.id, vals))
            self.lang = clodoo.browseL8(self.ctx, model, self.user.id).lang

    def assure_journals(self):
        for model, domain, self.company_id, vals in (
            ("account.journal", [], self.company_id, {"update_posted": True}),
        ):
            self.write_record(model, domain, vals)

    def action_after_installed(self, modname, connector_installed):
        if modname == "mk_test_env":
            self.set_new_db()
            self.assure_company()
            tax_id = self.env_ref("z0bug.tax_22v")
            while not tax_id:
                print("Activate Developer Mode and Load Account records ...")
                input("Press RET to continue ...")
                tax_id = self.env_ref("z0bug.tax_22v")
            partner_id = self.env_ref("z0bug.res_partner_1")
            while not partner_id:
                print("Activate Developer Mode and Load Partner records ...")
                input("Press RET to continue ...")
                partner_id = self.env_ref("z0bug.res_partner_1")
            product_id = self.env_ref("z0bug.product_product_1")
            while not product_id:
                print("Activate Developer Mode and Load Products records ...")
                input("Press RET to continue ...")
                product_id = self.env_ref("z0bug.product_product_1")
        elif modname == THIS_MODULE:
            connector_installed = True
            self.assure_cache()
            self.assure_all_backends()
            self.assure_lang()
            self.assure_user()
        return connector_installed

    def delete_all_records(self):
        self.write_log("delete_all_records()")
        for model, domains, company_id, multi, childs, action in (
            ("account.tax", [("description", "=", "a15")], self.company_id, True, None, None),
        ):
            self.delete_record(
                model,
                domains,
                multi=multi,
                action=action,
                childs=childs,
                company_id=company_id,
            )

        if not self.ctx.get("_cr"):
            print("No sql support found!")
            if self.ask:
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
                    clodoo.exec_sql(self.ctx, query)
                except BaseException:
                    pass

    def setup(self):
        self.write_log("self.setup()")
        self.init_new_db()
        model = "ir.module.module"
        maxctr = len(MODULE_LIST)
        connector_installed = False
        for ctr, modname in enumerate(MODULE_LIST):
            installed = self.check_if_module_installed(modname, ctr=ctr, maxctr=maxctr)
            if "conai" in modname and not self.conai:
                if installed:
                    self.wait_4_module_uninstalled(modname)
                continue
            if connector_installed and not installed:
                vals = {"name": modname}
                res_id = clodoo.executeL8(self.ctx, model, "synchro", vals)
                if res_id < 0:
                    raise IOError("!!Error %s installing %s!" % (res_id, modname))
                module = clodoo.browseL8(self.ctx, model, res_id)
                if module.state != "installed":
                    raise IOError("Module %s not installed!!!" % modname)
            if not installed:
                self.wait_4_module_installed(modname, ctr, maxctr)
            connector_installed = self.action_after_installed(
                modname, connector_installed)
        self.assure_journals()
        if not clodoo.browseL8(self.ctx,
                               "res.company",
                               self.company_id).due_cost_service_id:
            raise IOError("!!Missed bank cost in company!!")
        self.delete_all_records()

    def teardown(self):
        for fqn in self.fqn_to_remove:
            if pth.isfile(fqn):
                os.unlink(fqn)
        self.write_log("%d tests %s SUCCESSFULLY ENDED" % (self.ctr, THIS_MODULE))
        # try:
        #     clodoo.executeL8(
        #         ctx,
        #         "ir.model.synchro.cache",
        #         "die",
        #         True
        #     )
        # except BaseException:
        #     pass

    def init_any_model(
            self, identity, model, code="code", name="name", domain=(), reset_id=False):
        if reset_id:
            ext_id_field = self.get_ext_id_field(identity)
        fqn = pth.join(self.get_csv_path(), model + ".en_US.csv")
        if not pth.isfile(fqn):
            fqn = pth.join(self.get_csv_path(), model + ".csv")
        test_recs = self.load_csv_file(fqn)
        for rec in test_recs:
            if domain and domain != ():
                ids = clodoo.searchL8(
                    self.ctx, model, [(code, "=", rec[code]), domain])
            else:
                ids = clodoo.searchL8(self.ctx, model, [(code, "=", rec[code])])
            vals = {"name": rec[name]}
            if reset_id:
                vals[ext_id_field] = False
                if model == "res.partner" and identity.startswith("vg7"):
                    vals["vg72_id"] = False
            clodoo.writeL8(self.ctx, model, ids, vals, context={"lang": "en_US"})

    def init_res_country(self, identity, reset_id=False):
        model = "res.country"
        if self.ctx.get("_cr"):
            query = (
                "UPDATE ir_translation SET value='%s'"
                " WHERE name='res.country,name' AND src='%s' AND lang='it_IT'")
            for (value, src) in (
                    ("Germania", "Germany"),
                    ("Italia", "Italy"),
                    ("Regno Unito", "United Kingdom"),
            ):
                try:
                    clodoo.exec_sql(self.ctx, query % (value, src))
                except BaseException:
                    self.write_log("Cannot reset res.country", no_ts=True)
        self.init_any_model(identity, model, reset_id=reset_id)

    def reset_account_tax(self, identity, reset_id=False):
        model = "account.tax"
        self.init_any_model(identity, model, code="description", reset_id=reset_id)

    def dirty_account_tax(self):
        model = "account.tax"
        for (code, name) in (
                ("22v", "Iva debito 22%"),
                ("10v", "Iva debito 10%"),
                ("22a", "Iva credito 22%"),
        ):
            ids = clodoo.searchL8(
                self.ctx, model, [("description", "=", code)])
            clodoo.writeL8(self.ctx, model, ids, {"name": name})

    def reset_res_partner(self, identity, reset_id=False):
        model = "res.partner"
        self.init_any_model(identity, model, code="vat", reset_id=reset_id)

    def dirty_res_partner(self):
        for (vat, name) in (
                ("IT00115719999", "Partner 1"),
        ):
            ids = clodoo.searchL8(
                self.ctx, "res.partner", [("vat", "=", vat),
                                          ("type", "=", "contact")])
            clodoo.writeL8(self.ctx, "res.partner", ids, {"name": name})

    def reset_ext_id(self, identity, model):
        ext_id_field = self.get_ext_id_field(identity)
        domain = [(ext_id_field, ">", 0)]
        vals = {ext_id_field: False}
        ids = clodoo.searchL8(self.ctx, model, domain)
        for id in ids:
            clodoo.writeL8(self.ctx, model, id, vals)

    def init_model(self, identity, model, reset_id=False):
        if not self.conai and "conai" in model:
            return
        actual_model = self.get_actual_model(model)
        if actual_model == "res.country":
            self.init_res_country(identity, reset_id=reset_id)
        elif actual_model == "account.tax":
            self.reset_account_tax(identity, reset_id=reset_id)
        elif actual_model == "res.partner":
            self.reset_res_partner(identity, reset_id=reset_id)
        elif actual_model == model and reset_id:
            self.reset_ext_id(identity, model)

    def prepare_rec(self, rec, main_ext_id):
        ext_id = False
        for field in rec:
            if field in rec and rec[field] is None:
                del rec[field]
                continue
            if field == "id":
                ext_id = rec[field]
                if not main_ext_id:
                    main_ext_id = rec[field]
            elif field == "company_id" and not rec[field]:
                rec[field] = self.company_id
        return rec, ext_id, main_ext_id

    def write_file_2_pull(self, identity, ext_model, vals, mode="w"):
        fqn = pth.join(self.get_exchange_path(identity), "%s.csv" % ext_model)
        if mode == "a":
            with open(fqn, "r") as fd:
                ln = fd.read().split("\n")[0]
            data = "%s\n" % ",".join([str(vals.get(x, "")) for x in ln.split(",")])
        else:
            data = "%s\n%s\n" % (
                ",".join(vals.keys()),
                ",".join(map(lambda x: str(vals[x]), vals.keys())),
            )
        with open(fqn, mode) as fd:
            fd.write(data)
        self.fqn_to_remove.append(fqn)

    def compare(self, loc_value, test_value, mode=None):
        if hasattr(loc_value, "id"):
            loc_value = loc_value.id
        if mode == "nounknown":
            return not loc_value.startswith("Unknown")
        elif mode == "unknown":
            return loc_value.startswith("Unknown")
        elif mode == "individual":
            return loc_value in self.partner_MR_ids
        elif mode == "nocase":
            return loc_value.lower() == test_value.lower()
        elif mode and mode == test_value:
            if mode == "supplier":
                return loc_value == "contact"
            return loc_value == test_value
        elif mode == "delivery":
            return loc_value == test_value + 100000000
        elif mode == "invoice":
            return loc_value == test_value + 200000000
        elif isinstance(loc_value, basestring) and isinstance(test_value, (int, long)):
            if loc_value.isdigit():
                return int(loc_value) == test_value
            return loc_value == str(test_value)
        elif isinstance(loc_value, (int, long)) and isinstance(test_value, basestring):
            if test_value.isdigit():
                return loc_value == int(test_value)
            return str(loc_value) == test_value
        elif test_value is None:
            return True
        elif loc_value or test_value:
            return loc_value == test_value
        return True

    def check_records(self, identity, model, loc_id, test_rec, mode=None, state=None):
        self.write_log(
            "check_record(%s, %s, %s, %s)" % (identity, model, loc_id, test_rec),
            echo=False)
        spec = False
        if model.startswith("res.partner.") and model != "res.partner.bank":
            spec = {
                "shipping": "delivery",
                "billing": "invoice",
                "supplier": "supplier",
                "company": "company",
            }[model.split(".")[-1]]
            model = "res.partner"
        fields_2_ignore = []
        for ident in IDENTITY_LIST:
            if ident != identity:
                fields_2_ignore.append(self.get_ext_id_field(ident))
        loc_rec = clodoo.browseL8(self.ctx, model, loc_id)
        for field in [x for x in dir(loc_rec) if not x.startswith("_")]:
            loc_name = self.get_loc_name(model, field, identity)[0]
            if loc_name in fields_2_ignore:
                continue
            if loc_name in test_rec:
                if not self.compare(
                        getattr(loc_rec, loc_name),
                        test_rec[loc_name],
                        spec):
                    raise IOError(
                        "!!Field %s[%s].%s: invalid value <%s> expected <%s>"
                        % (model, loc_id,
                           field,
                           getattr(loc_rec, loc_name),
                           test_rec[loc_name])
                    )
                self.ctr += 1

    def test_function_synchro(self, model, vals, identity=None, ext_id=None):
        """
        Test function synchro: child record datas are in model values
        """
        if identity:
            vals = self.jacket_vals(vals, identity)
        self.write_log("synchro(%s, %s)" % (model, vals), eol=False)
        rec_id = clodoo.executeL8(self.ctx, model, "synchro", vals)
        self.write_log(str(rec_id), no_ts=True)
        if ext_id and rec_id > 0:
            self.store_ext_id(model, rec_id, ext_id, identity)
        return rec_id

    def test_function_trigger(self, ext_model, identity, ext_id):
        self.write_log(
            "trigger_one_record(%s, %s, %s)" % (ext_model, ext_id, identity), eol=False
        )
        rec_id = clodoo.executeL8(
            self.ctx,
            "ir.model.synchro",
            "trigger_one_record",
            ext_model, identity, ext_id
        )
        self.write_log(str(rec_id), no_ts=True)
        if ext_id and rec_id > 0:
            self.store_ext_id(ext_model, rec_id, ext_id, identity)
        return rec_id

    def load_n_test_model(
        self,
        identity,
        model,
        mode=None,
        ext_model=None,
        fct_test="synchro",
        lang=None
    ):
        self.write_log(
            "load_n_test_model(%s, %s, mode=%s, fct=%s)"
            % (identity, model, mode, fct_test),
        )

        ext_model = ext_model or self.get_ext_model(model, identity)
        if lang:
            fqn = pth.join(self.get_csv_path(identity), ext_model + "." + lang + ".csv")
        else:
            fqn = pth.join(self.get_csv_path(identity), ext_model + ".csv")
        ext_recs_image = self.load_csv_file(fqn)
        if lang:
            fqn = pth.join(self.get_csv_path(), model + "." + lang + ".csv")
        else:
            fqn = pth.join(self.get_csv_path(), model + ".csv")
        test_recs = self.load_csv_file(fqn)

        main_ext_id = False
        wa = "w"
        ext_id_field = self.get_ext_id_field(identity)
        if not ext_id_field:
            raise IOError("No match external id name for %s" % identity)
        if fct_test == "trigger":
            for ext_rec in ext_recs_image:
                ext_rec, ext_id, main_ext_id = self.prepare_rec(ext_rec, main_ext_id)
                self.write_file_2_pull(identity, ext_model, ext_rec, wa)
                wa = "a"

        for ext_rec in ext_recs_image:
            loc_id = ext_id = -127
            if fct_test == "synchro":
                ext_rec, ext_id, main_ext_id = self.prepare_rec(ext_rec, main_ext_id)
                loc_id = self.test_function_synchro(
                    model, ext_rec, identity=identity, ext_id=ext_id
                )
            elif fct_test == "trigger":
                ext_id = ext_rec["id"]
                loc_id = self.test_function_trigger(
                    ext_model, identity=identity, ext_id=ext_id
                )
            if loc_id < 0:
                raise IOError(
                    "Error %d processing %s=%s" % (loc_id, ext_id_field, ext_id))
            checked = False
            for test_rec in test_recs:
                if ext_id == test_rec[ext_id_field]:
                    self.check_records(identity, model, loc_id, test_rec)
                    checked = True
                    break
            if not checked:
                raise IOError(
                    "No match record found for %s=%s" % (ext_id_field, ext_id))
        return

    def test_country(
            self, mode=None, identity="vg7:", fct_test="synchro", reset_id=False):
        model = "res.country"
        self.init_model(identity, model, reset_id=reset_id)
        self.load_n_test_model(
            identity,
            model,
            fct_test=fct_test,
        )

        model = "res.country.state"
        self.init_model(identity, model, reset_id=reset_id)
        self.load_n_test_model(
            identity,
            model,
            fct_test=fct_test,
        )

    def test_partner(
            self, mode=None, identity="vg7:", fct_test="synchro", reset_id=False):
        model = "res.partner"
        self.init_model(identity, model, reset_id=reset_id)
        if reset_id:
            self.dirty_res_partner()
        self.load_n_test_model(
            identity,
            model,
            fct_test=fct_test,
        )

    def test_tax(
            self, mode=None, identity="vg7:", fct_test="synchro", reset_id=False):
        model = "account.tax"
        self.init_model(identity, model, reset_id=reset_id)
        if reset_id:
            self.dirty_account_tax()
        self.load_n_test_model(
            identity,
            model,
            fct_test=fct_test,
        )


def main(cli_args=[]):
    if not cli_args:
        cli_args = sys.argv[1:]
    ext_test_env = ExtTestEnv(cli_args)
    ext_test_env.setup()

    ext_test_env.write_log("*** Starting VG7 test ***", echo=True)
    ext_test_env.test_country(identity="vg7:", reset_id=True)
    ext_test_env.test_country(identity="vg7:", fct_test="trigger")
    ext_test_env.test_partner(identity="vg7:", reset_id=True)
    ext_test_env.test_partner(identity="vg7:", fct_test="trigger")
    # In order to increase test coverage, from here trigger run before synchro test
    ext_test_env.test_tax(identity="vg7:", reset_id=True, fct_test="trigger")
    ext_test_env.test_tax(identity="vg7:")


    ext_test_env.write_log("*** Starting OE8 test ***", echo=True)
    ext_test_env.test_country(identity="oe8:", reset_id=True)
    ext_test_env.test_country(identity="oe8:", fct_test="trigger")
    ext_test_env.test_partner(identity="oe8:", reset_id=True)
    ext_test_env.test_partner(identity="oe8:", fct_test="trigger")
    # In order to increase test coverage, from here trigger run before synchro test
    ext_test_env.test_tax(identity="oe8:", reset_id=True, fct_test="trigger")
    ext_test_env.test_tax(identity="oe8:")

    ext_test_env.teardown()


if __name__ == "__main__":
    exit(main())
