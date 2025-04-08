#!/usr/bin/env python
# -*- coding: utf-8 -*-
# flake8: noqa
"""Connector concurrent test

This test is executed after ordinary Odoo module test, by zerobug; test connects to
active Odoo instance. Notice: in order to execute a full clear and repeatable tests a
new DB will be created and needed module installed on it.
This test communicates with Odoo instance through odoorpc library. However, some actions
are asked human operator.

Test structure (for historical reason, counterparty are Odoo 8.0 and VG7):
    1. Initialization (modules installing, data setting)
    2. VG7 backend tests
    3. Odoo 8.0 backend tests
    4. Cleaning

Every backend test executes test on a group of Odoo models (tables).
Before running test, all models matched data are read and loaded in counterparty path
in order to simulate counterparty instance.
Then, Odoo model test stages are:
    1. Load dirty data (if available)
    2. For every record to test:
        2.1 Calls synchro and trigger functions
        2.2 Record is read from DB and matched against expected data

All data (dirty, match and counterpaty instance) are stored in csv files, located in
tests/data path which has the following structure:
    tests/data/dirty -> files with dirty values to load before test
    tests/data/match -> files with expected results
    tests/data/oe8 -> files with simulated counterpaty Odoo8 instance
    tests/data/vg7 -> files with simulated counterpaty vg7 instance

Every csv file has the same name of the counterparty model and contains header
counterparty names required by instance; i.e. "res,partner" model has "res.partner.csv"
file and header can contain "name", "vat" and other field names.
VG7 counterparty file is "customers.csv" that and header has "name" and "piva" fields.

Every action run by test is logged in tests/concurrent_test/test_concurrent.log
Odoo instance log file is tests/log/nohup_YYYYMMDD.txt where YYYYMMDD is the test date.
This log is the logical concatenation of tests/log/universal_connector_YYYYMMDD.txt
created da zerobug library during ordinary Odoo test.

Notes on csv files.
Data to load and match are stored in csv files. Every column of csv contains data list
of the specific field named by header name; values in csv file are always text strings
even for non text fields. Here conversion rules:

* Integer: value is numeric text string, i.e. "123" for 123
* Data: ISO format, i.e. "2024-06-26"
* Many2one: line integer or else external ref, i.e. "base.main_partner"

Empty values always become False. Special notation "\\N" (with just 1 backslash)
on "id" field means <do not load any value>

Magic fields for dirty files.
Dirty csv files can have some magic fields:
* _action -> may be "update" (default) or "delete"
* _identity -> if not null, record is loaded only if matches the specific identity
* _only_reset -> if not null, record is loaded only reset stage
"""
from __future__ import print_function, unicode_literals
from __future__ import division
from __future__ import absolute_import
from future import standard_library

standard_library.install_aliases()  # noqa: E402
from past.builtins import basestring, long
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
    from python_plus.python_plus import _u, unicodes
except ImportError:
    from python_plus import _u, unicodes
try:
    from clodoo import clodoo
except ImportError:
    import clodoo
try:
    from z0lib.z0lib import z0lib
except ImportError:
    from z0lib import z0lib
from z0lib.z0librun import print_flush
# import pdb      # pylint: disable=deprecated-module

__version__ = "10.0.0.2.5"

# TEST_IBAN = "IT60X0542811101000000123456"
MODEL_KEYS = {
    "account.account.type": {"code": "name"},
    "account.account": {},
    "account.invoice": {"code": "number"},
    "account.journal": {},
    "account.payment.term": {"code": "name"},
    "account.tax": {"code": "description"},
    "product.product": {"code": "default_code"},
    "product.template": {"code": "default_code"},
    "product.uom": {"code": "name"},
    "purchase.order": {"code": "name"},
    "res.company": {"code": "vat"},
    "res.country": {},
    "res.country.state": {},
    "res.partner": {
        "code": "vat",
        "domain": [("type", "=", "contact"), ("customer", "=", True)]
    },
    "res.partner.supplier": {
        "code": "vat",
        "domain": [("type", "=", "contact"),("supplier", "=", True)]
    },
    "res.users": {"code": "login"},
    "sale.order": {"code": "name"},
    "stock.picking.transportation_reason": {"code": "name"},
    "stock.picking.carriage_condition": {"code": "name"},
    "stock.picking.goods_description": {"code": "name"},
    "stock.picking.transportation_method": {"code": "name"},
    "stock.picking.package.preparation": {"code": "ddt_number"},
}
MODEL_WITH_CHILD = {
    "account.payment.term": {
        "child_model": "account.payment.term.line",
        "child_field": "line_ids",
        "child_key": "sequence",
        "parent_field": "payment_id",
        "oe8:": {
            "fqn": "account.payment.term.line.csv",
            "parent_field": "payment_id",
            "child_field": "line_ids",
        },
    },
    "account.invoice": {
        "child_model": "account.invoice.line",
        "child_field": "invoice_line_ids",
        "child_key": "sequence",
        "parent_field": "invoice_id",
        "oe8:": {
            "fqn": "account.invoice.line.csv",
            "parent_field": "invoice_id",
            "child_field": "invoice_line",
        },
    },
    "account.move": {
        "child_model": "account.move.line",
        "child_field": "line_ids",
        "parent_field": "move_id",
    },
    "purchase.order": {
        "child_model": "purchase.order.line",
        "child_field": "order_line",
        "child_key": "sequence",
        "parent_field": "order_id",
        "vg7:": {
            "fqn": "purchase_orders.line.csv",
            "parent_field": "order_id",
            "child_field": "order_rows",
        },
        "oe8:": {
            "fqn": "purchase.order.line.csv",
            "parent_field": "order_id",
            "child_field": "order_line",
        },
    },
    "sale.order": {
        "child_model": "sale.order.line",
        "child_field": "order_line",
        "child_key": "sequence",
        "parent_field": "order_id",
        "vg7:": {
            "fqn": "orders.line.csv",
            "parent_field": "order_id",
            "child_field": "order_rows",
        },
        "oe8:": {
            "fqn": "sale.order.line.csv",
            "parent_field": "order_id",
            "child_field": "order_line",
        },
    },
    "stock.picking.package.preparation": {
        "child_model": "stock.picking.package.preparation.line",
        "child_field": "line_ids",
        "child_key": "sequence",
        "parent_field": "package_preparation_id",
        "vg7:": {
            "fqn": "ddt.line.csv",
            "parent_field": "ddt_id",
            "child_field": "order_rows",
        },
        "oe8:": {
            "fqn": "stock.picking.package.preparation.line.csv",
            "parent_field": "package_preparation_id",
            "child_field": "line_ids",
        },
    },
}
TNL_VG7_TABLES = {
    "account.account.type": "",
    "account.account": "",
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
    "purchase.order": "purchase_orders",
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
SETUP_MODEL_LIST = (
    "account.account.type",
    "res.country",
    "res.country.state",
    "res.partner",
    "res.partner.supplier",
    "res.users",
    "res.company",
    "account.account",
    "account.journal",
    "account.tax",
    "account.payment.term",
    "product.template",
    "stock.picking.transportation_reason",
    "stock.picking.carriage_condition",
    "stock.picking.goods_description",
    "stock.picking.transportation_method",
    # "stock.picking.package.preparation",
)
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

THIS_MODULE = "universal_connector"
COA_MODULE = "l10n_it_coa"
MODULE_LIST = [
    THIS_MODULE,
    COA_MODULE,
    "account",
    "account_payment_term_extension",
    "purchase",
    "sale",
    "stock",
    "l10n_it_fiscalcode",
    "l10n_it_conai",
    "l10n_it_einvoice_base",
    "connector_vg7_conai",
]
IDENTITY_LIST = ["vg7:", "oe8:"]


class ExtTestEnv(object):

    def __init__(self, *args):
        self.parseoptargs(args)
        for item in ("ask", "config", "database", "lang", "conai"):
            setattr(self, item, getattr(self.opt_args, item))
            print_flush("# %s=%s" % (item, getattr(self, item)))
        self.config = self.config or os.environ.get("TEST_CONFN")
        self.database = self.database or os.environ.get("TEST_DB")
        self.lang = self.lang or "it_IT"
        self.logfn = __file__.replace(".py", ".log")
        self.ctr = 0
        if pth.isfile(self.logfn):
            os.unlink(self.logfn)
        self.fqn_to_remove = []
        self.struct = {}

    def parseoptargs(self, args):
        parser = argparse.ArgumentParser(
            # formatter_class=argparse.RawDescriptionHelpFormatter,
            description="Odoo test environment - © 2020-2025 by SHS-AV s.r.l.",
        )
        parser.add_argument(
            "-a",
            "--ask",
            action="store_true",
            help="Ask for actions",
        )
        parser.add_argument(
            "-c",
            "--config",
            help="Odoo configuration file",
            dest="config",
            metavar="FILE",
        )
        parser.add_argument(
            "-d",
            "--database",
            help="DB name to test",
            dest="database",
            metavar="FILE",
        )
        parser.add_argument(
            "-l",
            "--lang",
            help="Language to test",
            metavar="ISO3166",
        )
        parser.add_argument(
            "--conai",
            action="store_true",
            help="Test with CONAI module",
        )
        self.opt_args = parser.parse_args(*args)

    def ask_4_ret(self, force=False):
        if force or self.ask:
            print_flush("Press RET to continue ...")
            input("")
            print_flush("")

    def write_log(self, mesg, eol=True, echo=True, no_ts=False, bb=0):
        lines = bb * "\n"
        if echo:
            if not eol:
                print_flush(lines + mesg + " -> ", end="")
            else:
                print_flush(lines + mesg)
        with open(self.logfn, "a") as fd:
            if no_ts:
                fd.write(u" -> ")
            else:
                if lines:
                    fd.write(lines)
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

    def search_4_xref(self, model, res_id):
        ir_model = "ir.model.data"
        return clodoo.searchL8(
            self.ctx, ir_model, [("model", "=", model), ("res_id", "=", res_id)]
        )

    def get_xref_from_id(self, model, res_id):
        xmlid = self.search_4_xref(model, res_id)
        if xmlid:
            ir_model = "ir.model.data"
            return clodoo.browseL8(self.ctx, ir_model, xmlid)
        return None

    @staticmethod
    def get_ext_id_field(identity, model=None):
        if model == "res.partner.supplier" and identity == "vg7:":
            return "vg72_id"
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

    def is_xref(self, xref):
        return (isinstance(xref, basestring)
                and re.match(r"[a-z][a-z0-9_]{3,}\.[\w]+", xref))

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
            if not ext_ref.startswith((prefix, ":", "_")):
                ref = "%s%s" % (prefix, ext_ref)
                if vals[ext_ref] in (r"\N", "None"):
                    vals[ref] = ""
                else:
                    vals[ref] = vals[ext_ref]
                del vals[ext_ref]
        return vals

    def cast_1_value(self, model, key, value, keep_id=False, keep_none=False):
        if value in (r"\N", "None"):
            value = r"\N" if keep_none else None
        elif key == "company_id" and not value:
            value = self.company_id
        elif isinstance(value, dict):
            value = self.cast_value(model, value, keep_id=keep_id)
        elif isinstance(value, (list, tuple)):
            value = [self.cast_1_value(model, key, v, keep_id=keep_id) for v in value]
        elif isinstance(value, basestring):
            x = (re.search(r"[a-z][a-z0-9_]{3,}\.[\w]+", value)
                 if " " not in value else None)
            while x and not value[x.end():].startswith("."):
                saved_value = self.env_ref(value[x.start():x.end()])
                if not saved_value and keep_id:
                    break
                if isinstance(saved_value, (int, long, float)):
                    value = value[:x.start()] + str(saved_value) + value[x.end():]
                else:
                    value = value[:x.start()] + "'" + saved_value + "'" + value[x.end():]
                x = re.search("[\w]+\.[\w]+", value)
            if value.isdigit() and (value.startswith("0")
                                    or len(value) > 9
                                    or key == "zip"):
                return value
            if re.match("[0-9]+[-+*/]+[0-9]+", value):
                return value
            if re.match("[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
                return value
            saved_value = value
            try:
                if key.endswith("id") and not value:
                    value = False
                else:
                    value = eval(value)
            except BaseException:
                value = saved_value
        return value

    def cast_value(self, model, vals, keep_id=False, keep_none=False):
        res = {}
        for k, v in vals.items():
            v = self.cast_1_value(model, k, v, keep_id=keep_id, keep_none=keep_none)
            if v is None:
                continue
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

    def load_csv_file(self, model, fqn, keep_id=False, keep_none=False):
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
                datas.append(self.cast_value(model, dict(zip(header, row)),
                                             keep_id=keep_id, keep_none=keep_none))
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

    def get_excl_list(self, model):
        excl_list = [
            rec.res_id
            for rec in clodoo.browseL8(
                self.ctx,
                "ir.model.data",
                clodoo.searchL8(self.ctx, "ir.model.data", [("model", "=", model)]),
            )
        ]
        if model == "res.partner":
            for submodel in ("res.users", "res.company"):
                for rec in clodoo.browseL8(
                    self.ctx, submodel,
                        clodoo.searchL8(self.ctx, submodel, [])
                ):
                    if rec.partner_id.id not in excl_list:
                        excl_list.append(rec.partner_id.id)
        return excl_list

    def delete_record(self, model, domains, why=""):
        excl_list = self.get_excl_list(model)
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
            if isinstance(domain, basestring):
                rec_ids = self.env_ref(domain)
                rec_ids = [rec_ids] if rec_ids else []
            else:
                if excl_list:
                    domain.append(("id", "not in", excl_list))
                rec_ids = clodoo.searchL8(self.ctx, model, domain)
            if rec_ids:
                try:
                    self.write_log("delete_record(%s, %s)  ##<%s>"
                                   % (model, domains, why),
                                   eol=False)
                    clodoo.unlinkL8(self.ctx, model, rec_ids)
                    self.write_log(str(rec_ids), no_ts=True)
                except BaseException as e:
                    self.write_log("Error %s removing records ..." % e, echo=True)
                    if self.ask:
                        self.ask_4_ret()
                    else:
                        exit(1)
            else:
                self.write_log("No record to delete(%s, %s)  ##<%s>"
                               % (model, domains, why),
                               echo=False)

    def init_new_db(self):
        self.write_log("init_new_db(%s, %s)" % (self.database, self.config))
        print_flush(
            "# Be patient, the universal connector full test takes a few time ...")
        if self.database != os.environ.get("TEST_DB", self.database):
            if self.ask:
                print_flush("# Please drop DB %s" % self.database)
                self.ask_4_ret()
                print_flush("# Now recreate DB %s (w/o demo data)" % self.database)
                self.ask_4_ret()
        with open(self.config, "r") as fd:
            contents = fd.read()
        if "psycopg2 = 1" not in contents:
            with open(self.config, "a") as fd:
                fd.write("psycopg2 = 1\n")
        uid, self.ctx = clodoo.oerp_set_env(confn=self.config, db=self.database)
        if not uid:
            raise IOError("DB %s not connected via json/xmlrpc!" % self.database)
        self.user = self.ctx["user"]

    def install_module(self, modname, connector_installed=False):
        self.write_log("install_module(%s)" % modname)
        model = "ir.module.module"
        if connector_installed:
            vals = {"name": modname}
            res_id = clodoo.executeL8(self.ctx, model, "synchro", vals)
            if res_id < 0:
                raise IOError("!!Error %s installing %s!" % (res_id, modname))
        else:
            module_ids = clodoo.searchL8(self.ctx, model, [("name", "=", modname)])
            if not module_ids:
                raise IOError("Module %s does not exist!!!" % modname)
            clodoo.executeL8(self.ctx,
                             "ir.module.module",
                             "button_immediate_install",
                             module_ids)

    def check_if_module_installed(self, modname, ctr=-1, maxctr=-1, wait=False):
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
            ctr = 40 if wait else 1
            while ctr > 0 and state != "installed":
                state = clodoo.browseL8(self.ctx, model, module_ids[0]).state
                ctr -= 2 if not state.startswith("to ") else 1
                sleep(1.0)
                # Following statement should clear the rcp cache
                clodoo.searchL8(self.ctx, model, [])
        return state == "installed"

    def wait_4_module_uninstalled(self, modname):
        installed = self.check_if_module_installed(modname)
        while installed:
            print_flush("# Module %s installed!" % modname)
            print_flush("# Please uninstall %s" % modname)
            self.ask_4_ret(force=True if modname == THIS_MODULE else self.ask)
            installed = self.check_if_module_installed(modname, wait=True)

    def wait_4_module_installed(self, modname, ctr, maxctr):
        installed = self.check_if_module_installed(modname)
        while not installed:
            print_flush("# Module %s not installed!" % modname)
            print_flush("# Please install %s" % modname)
            self.ask_4_ret()
            installed = self.check_if_module_installed(
                modname, ctr=ctr, maxctr=maxctr, wait=True)

    def assure_company(self):
        self.write_log("assure_company()", bb=1)
        model = "res.company"
        xref = "z0bug.mycompany"
        self.company_note = "Si prega di controllare i dati entro le 24h."
        self.company_id = self.env_ref(xref)
        if not self.company_id:
            company = self.resource_browse(model, xref="base.main_company")
            vals = {}
            if company.name != "Test Company":
                vals["name"] = "Test Company"
            if vals:
                vals["sale_note"] = self.company_note
            if "Zero" in company.chart_template_id.name:
                if not company.country_id:
                    vals["country_id"] = self.env_ref("base.it")
                self.company_id = company.id
                self.resource_write(model, company.id, values=vals, xref=xref)
            else:
                vals["country_id"] = self.env_ref("base.it")
                vals["currency_id"] = self.env_ref("base.EUR")
                self.company_id = self.resource_create(model, values=vals, xref=xref)
                company = self.resource_browse(model, self.company_id)
        else:
            company = self.resource_browse(model, self.company_id)
            vals = {}
            if company.name != "Test Company":
                vals["name"] = "Test Company"
            if not company.country_id:
                vals["country_id"] = self.env_ref("base.it")
            if vals:
                vals["sale_note"] = self.company_note
                self.resource_write(model, self.company_id, values=vals)
        self.resource_write(
            "res.partner",
            company.partner_id.id,
            {"lang": self.lang},
            xref="z0bug.partner_mycompany")
        if self.database != os.environ.get("TEST_DB", self.database):
            print_flush("# Activate Developer Mode and create full test environment")
            print_flush("#     lang=it_IT, no new company, CoA=Zero,%s CONAI ..."
                  % " not" if self.conai else " ")
            print_flush("# You need only chart of account, partners and products ...")
            self.ask_4_ret(force=True)

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
            self.write_log("Activate language %s ..." % self.lang, echo=True, bb=1)
            id = clodoo.createL8(
                self.ctx, "base.language.install", {"lang": self.lang})
            clodoo.executeL8(
                self.ctx, "base.language.install", "lang_install", [id])
            vals = {"oe8:code": self.lang, "id": 59}
            self.write_log("Installing language %s ..." % self.lang, echo=True)
            clodoo.executeL8(self.ctx, model, "synchro", vals)
        self.ctx["lang"] = self.lang


    def assure_user(self, lang=None):
        self.write_log("assure_user(lang=%s)" % lang, bb=1)
        model = "res.users"
        user_id = self.env_ref("base.user_root")
        if user_id != self.user.id:
            raise IOError(
                "!!Invalid current user id %s; set %s!" % (self.user.id, user_id)
            )
        user = self.resource_browse(model, self.user.id)
        vals = {}
        if self.company_id not in [x.id for x in user.company_ids]:
            vals["company_ids"] = [(4, self.company_id)]
        if user.lang != (lang or self.lang):
            vals["lang"] = lang or self.lang
        if vals:
            vals["tz"] = "Europe/Rome"
            self.resource_write("res.users", self.user.id, vals)
        if user.company_id.id != self.company_id:
            vals = {"company_id": self.company_id}
            self.resource_write("res.users", self.user.id, vals)
            coa_id = self.env_ref("l10n_it_coa.l10n_chart_it_zeroincombenze")
            clodoo.executeL8(self.ctx,
                             "account.chart.template",
                             "try_loading_for_current_company",
                             coa_id)
            self.write_log(
                "try_loading_for_current_company(l10n_chart_it_zeroincombenze)")
            sleep(1)
        self.lang = clodoo.browseL8(self.ctx, model, self.user.id).lang
        if self.ctx["lang"] != self.lang:
            raise IOError(
                "!!DB language %s is different from connection meta-data %s!"
                % (self.lang, self.ctx["lang"])
            )

    def assure_journals(self):
        for model, domain, company_id, vals in (
            ("account.journal",
             [("update_posted", "=", False)],
             self.company_id,
             {"update_posted": True}),
        ):
            self.resource_write(model, domain, vals)

    def action_after_installed(self, modname, connector_installed):
        if modname == "mk_test_env":
            pass
        elif modname == THIS_MODULE:
            connector_installed = True
            self.assure_cache()
            self.assure_all_backends()
        return connector_installed

    def setup(self):
        self.write_log("** self.setup() **")
        self.init_new_db()
        self.ask_4_ret()
        self.prior_model = self.prior_fct = ""
        # model = "ir.module.module"
        maxctr = len(MODULE_LIST)
        connector_installed = False
        for ctr, modname in enumerate(MODULE_LIST):
            installed = self.check_if_module_installed(modname, ctr=ctr, maxctr=maxctr)
            if "conai" in modname and not self.conai:
                if installed:
                    self.wait_4_module_uninstalled(modname)
                continue
            if not installed:
                self.install_module(modname, connector_installed=connector_installed)
                self.wait_4_module_installed(modname, ctr, maxctr)
            connector_installed = self.action_after_installed(
                modname, connector_installed)

        self.ask_4_ret()
        self.assure_lang()
        self.assure_company()
        self.assure_user()
        self.model_wkf = {}
        ext_id_field_oe8 = self.get_ext_id_field("oe8:")

        for model in SETUP_MODEL_LIST:
            ext_id_field_vg7 = self.get_ext_id_field("vg7:", model=model)
            setup_recs, child_setup_recs, child_model = self.load_setup_recs(model)
            parent_field = (MODEL_WITH_CHILD[model]["parent_field"]
                            if model in MODEL_WITH_CHILD else "")
            for setup_rec in setup_recs:
                vals = self.load_vals(model, {}, setup_rec)
                why, vals = self.extract_why(vals)
                vals[ext_id_field_vg7] = False
                vals[ext_id_field_oe8] = False
                code = MODEL_KEYS[model].get("code", "code")
                domain = MODEL_KEYS[model].get("domain", [])
                xref = None
                if "id" in setup_rec:
                    xref = setup_rec["id"]
                    full_domain = xref
                if not xref:
                    full_domain = self.get_domain(
                        model, setup_rec, code=code, domain=domain)
                loc_id = self.resource_write(
                    model, full_domain, vals, create=True, xref=xref)[0]
                if child_model:
                    child_domain = [
                        (MODEL_WITH_CHILD[model]["parent_field"], "=", loc_id)]
                    child_ids = clodoo.searchL8(self.ctx, child_model, child_domain)
                    ctr = 0
                    for ix, child_setup_rec in enumerate(child_setup_recs):
                        if self.cast_1_value(
                                child_model,
                                parent_field,
                                child_setup_rec[parent_field]) != loc_id:
                            continue
                        ctr += 1
                        child_vals = self.load_vals(child_model,{}, child_setup_rec)
                        child_vals[ext_id_field_vg7] = False
                        child_vals[ext_id_field_oe8] = False
                        child_id = False
                        if child_vals:
                            why, child_vals = self.extract_why(child_vals)
                            if ix < len(child_ids):
                                child_id = child_ids[ix]
                                child_rec = self.resource_browse(
                                    child_model, child_id, quiet=True)
                                child_vals = self.purge_values(child_rec, child_vals)
                        if not child_vals:
                            continue
                        child_vals[parent_field] = loc_id
                        self.resource_write(
                            child_model, child_id,  child_vals, create=True)
                    if ctr != len(child_ids):
                        self.write_log(
                            "DEVEL TROUBLE: found too many child record of %s"
                            % child_model)
            if model == "account.journal":
                self.assure_journals()
        self.reset_cache()

    def teardown(self):
        for model in self.model_wkf:
            if self.model_wkf[model] == 1:
                self.write_log(
                    "DEVEL TROUBLE: initialed model %s not processed" % model)
        for fqn in self.fqn_to_remove:
            if pth.isfile(fqn):
                self.write_log("os.unlink(%s)" % fqn)
                os.unlink(fqn)
        self.write_log("%d tests %s SUCCESSFULLY completed" % (self.ctr, THIS_MODULE),
                       bb=2)

    def get_domain(
            self, model, vals, code="code", name=None, domain=(), all_fields=False):
        def build_expr(vals, field, op_not=False):
            value = self.cast_1_value(model, field, vals[field])
            op = "="
            dom = (field, op, value)
            if field.startswith("_sel_"):
                field = field[5:]
                if value.startswith(("<", "=", ">", "!")):
                    op, value = re.match("([<=>!]+)(.*)", value)
                dom = (field, op, value)
            elif isinstance(value, basestring) and "%" in value:
                dom = (field, "not ilike" if op_not else "ilike", value)
            return dom

        full_domain = []
        if code in vals:
            full_domain += [build_expr(vals, code)]
        if name and name in vals and not all_fields:
            full_domain += [build_expr(vals, name)]
        if vals.get("parent_id"):
            full_domain += [build_expr(vals, "parent_id")]
        if domain and domain != ():
            full_domain += list(domain)
        if full_domain and "company_id" in vals and vals["company_id"]:
            full_domain += ["|"]
            full_domain += [("company_id", "=", False)]
            full_domain += [build_expr(vals, "company_id")]
        for (k, v) in vals.items():
            dom = []
            if k.startswith("_sel_"):
                k = k[5:]
                if v.startswith(("<", "=", ">", "!")):
                    op, v = re.match("([<=>!]+)(.*)", v).groups()
                else:
                    op = "="
                dom = [(k, op, self.cast_1_value(model, k, v))]
            elif all_fields and not k.startswith("_"):
                dom = [build_expr(vals, k)]
            if dom and dom not in full_domain:
                full_domain += dom
        if not full_domain:
            # NULL domain, avoid all records
            full_domain = [("id", "<", 0)]
        return full_domain

    def load_vals(self, model, vals, rec_vals):
        for (k, v) in rec_vals.items():
            if k in ("id", "vg7_id", "oe8_id"):
                continue
            vals[k] = self.cast_1_value(model, k, v)
        return vals

    def extract_action_from_vals(self, vals, identity, reset_id):
        action = vals.get("_action") or "update"
        if "_action" in vals:
            del vals["_action"]
        if identity != (vals.get("_identity") or identity):
            return False, vals
        if "_identity" in vals:
            del vals["_identity"]
        if (
                isinstance(vals.get("_only_reset"), bool)
                and vals["_only_reset"] != reset_id
        ):
            return False, vals
        if "_only_reset" in vals:
            del vals["_only_reset"]
        return action, vals

    def dirty_any_model(self, identity, model, code="code", domain=(), reset_id=False):
        fqn = pth.join(self.get_csv_path("dirty"), model + ".csv")
        if not pth.isfile(fqn):
            self.write_log("No dirty record to load for model %s)" % model, echo=False)
            return
        child_model = child_dirty_recs = None
        if model in MODEL_WITH_CHILD:
            child_model = MODEL_WITH_CHILD[model]["child_model"]
            child_fqn = pth.join(self.get_csv_path("dirty"), child_model + ".csv")
            child_dirty_recs = self.load_csv_file(child_model, child_fqn)
        dirty_recs = self.load_csv_file(model, fqn)
        for dirty_rec in dirty_recs:
            full_domain = self.get_domain(model, dirty_rec, code=code, domain=domain)
            action, dirty_rec = self.extract_action_from_vals(
                dirty_rec, identity, reset_id)
            if not action:
                continue
            if action.startswith("d"):
                why, dirty_rec = self.extract_why(dirty_rec)
                self.delete_record(model, full_domain, why=why)
                continue
            loc_ids = clodoo.searchL8(self.ctx, model, full_domain)
            if not loc_ids:
                continue
            self.resource_write(model, loc_ids, dirty_rec)
            if child_model:
                if len(loc_ids) > 1:
                    raise IOError(
                        "!!Found too many records for model %s with %s!"
                        % (model, full_domain)
                    )
                parent_field = MODEL_WITH_CHILD[model]["parent_field"]
                for child_dirty_rec in child_dirty_recs:
                    if parent_field not in child_dirty_rec:
                        continue
                    loc_id = self.cast_1_value(child_model, "id",  dirty_rec["id"])
                    if child_dirty_rec[parent_field] == loc_id:
                        child_key = MODEL_WITH_CHILD[model]["child_key"]
                        child_domain = [
                            (parent_field, "=", loc_id),
                            (child_key, "=", self.cast_1_value(
                                child_model, child_key, child_dirty_rec[child_key])),
                        ]
                        action, child_dirty_rec = self.extract_action_from_vals(
                            child_dirty_rec, identity, reset_id)
                        if not action:
                            continue
                        if action.startswith("d"):
                            self.delete_record(child_model, child_domain)
                            continue
                        child_ids = clodoo.searchL8(self.ctx, child_model, child_domain)
                        if not child_ids:
                            continue
                        self.resource_write(child_model, child_ids, child_dirty_rec)
        if child_model:
            parent_field = MODEL_WITH_CHILD[model]["parent_field"]
            for child_dirty_rec in child_dirty_recs:
                if (
                        parent_field not in child_dirty_rec
                        or not child_dirty_rec[parent_field]
                ):
                    child_key = MODEL_WITH_CHILD[model]["child_key"]
                    child_domain = self.get_domain(child_model, child_dirty_rec, code=child_key)
                    action, child_dirty_rec = self.extract_action_from_vals(
                        child_dirty_rec, identity, reset_id)
                    if not action:
                        continue
                    if action.startswith("d"):
                        why, child_dirty_rec = self.extract_why(child_dirty_rec)
                        self.delete_record(child_model, child_domain, why=why)
                        continue
                    child_ids = clodoo.searchL8(self.ctx, child_model, child_domain)
                    if not child_ids:
                        continue
                    self.resource_write(child_model, child_ids, child_dirty_rec)

    def load_test_recs(self, model, lang=None):
        # Test records may be equal to setup records
        actual_model = self.get_actual_model(model)
        child_model = child_test_recs = None
        if actual_model in MODEL_WITH_CHILD:
            child_model = MODEL_WITH_CHILD[actual_model]["child_model"]
            if lang:
                child_fqn = pth.join(
                    self.get_csv_path(), child_model + "." + lang + ".csv")
            else:
                child_fqn = pth.join(self.get_csv_path(), child_model + ".csv")
            if not os.path.isfile(child_fqn):
                self.write_log("Match records for model %s are the same of setup"
                               % child_model, echo=False)
                if lang:
                    child_fqn = pth.join(
                        self.get_csv_path("setup"), child_model + "." + lang + ".csv")
                else:
                    child_fqn = pth.join(
                        self.get_csv_path("setup"), child_model + ".csv")
            if not os.path.isfile(child_fqn):
                self.write_log("Missed match records for model %s)"
                               % child_model, echo=False)
            else:
                child_test_recs = self.load_csv_file(
                    child_model, child_fqn, keep_id=True)
        if lang:
            fqn = pth.join(self.get_csv_path(), actual_model + "." + lang + ".csv")
        else:
            fqn = pth.join(self.get_csv_path(), actual_model + ".csv")
        if not os.path.isfile(fqn):
            self.write_log("Match records for model %s are the same of setup"
                           % actual_model, echo=False)
            if lang:
                fqn = pth.join(self.get_csv_path("setup"), actual_model + "." + lang + ".csv")
            else:
                fqn = pth.join(self.get_csv_path("setup"), actual_model + ".csv")
        if not os.path.isfile(fqn):
            self.write_log("Missed match records for model %s)"
                           % actual_model, echo=False)
            test_recs = []
        else:
            test_recs = self.load_csv_file(model, fqn, keep_id=True)
        return test_recs, child_test_recs, child_model

    def load_setup_recs(self, model, lang=None):
        self.model_wkf[model] = 1
        child_model = None
        child_setup_recs = []
        if model in MODEL_WITH_CHILD:
            child_model = MODEL_WITH_CHILD[model]["child_model"]
            if lang:
                child_fqn = pth.join(
                    self.get_csv_path("setup"), child_model + "." + lang + ".csv")
            else:
                child_fqn = pth.join(self.get_csv_path("setup"), child_model + ".csv")
        if lang:
            fqn = pth.join(self.get_csv_path("setup"), model + "." + lang + ".csv")
        else:
            fqn = pth.join(self.get_csv_path("setup"), model + ".csv")
        if child_model:
            self.write_log("# setup(%s, %s)" % (model, child_model))
        else:
            self.write_log("# setup(%s)" % model)
        if not pth.isfile(fqn):
            self.write_log("No setup records for model %s)" % model, echo=False)
            return [], [], child_model
        setup_recs = self.load_csv_file(model, fqn, keep_id=True)
        if child_model:
            if not pth.isfile(child_fqn):
                self.write_log(
                    "No setup records for model %s)" % child_model, echo=False)
            else:
                child_setup_recs = self.load_csv_file(
                    child_model, child_fqn, keep_id=True)
        return setup_recs, child_setup_recs, child_model

    def init_model(
            self, identity, model,
            code=None, name=None, domain=(), reset_id=False, lang=None):
        if not self.conai and "conai" in model:
            return
        actual_model = self.get_actual_model(model)
        if actual_model not in self.struct:
            self.struct[actual_model] = clodoo.executeL8(
                self.ctx, actual_model, "fields_get")
        code = code or MODEL_KEYS[model].get("code", "code")
        name = name or MODEL_KEYS[model].get("name", "name")
        domain = domain or MODEL_KEYS[model].get("domain", [])
        ctx = {"lang": lang} if lang else {}
        self.write_log("* init_model(%s, %s, code=%s, name=%s, domain=%s, ctx=%s)"
                       % (identity, model, code, name, domain, ctx))
        if reset_id:
            ext_id_field = self.get_ext_id_field(identity, model=model)
        test_recs, child_test_recs, child_model = self.load_test_recs(model, lang=lang)
        for test_rec in test_recs:
            vals = {}
            loc_id = False
            if "id" in test_rec and test_rec["id"]:
                loc_id = self.cast_1_value(model,"id", test_rec["id"])
            if loc_id:
                full_domain = [("id", "=", loc_id)]
                vals = self.load_vals(model, vals, test_rec)
                if isinstance(test_rec["id"], basestring):
                    full_domain = [("id", "=", test_rec["id"])]
                else:
                    xref = self.get_xref_from_id(actual_model, loc_id)
                    if xref:
                        full_domain = [("id", "=", xref.complete_name)]
                loc_ids = [loc_id]
            else:
                # Avoid to initialize too many records
                full_domain = self.get_domain(
                    actual_model, test_rec,
                    code=code, name=name, domain=domain, all_fields=True)
                loc_ids = clodoo.searchL8(self.ctx, actual_model, full_domain, context=ctx)
                if not loc_ids:
                    continue
                for loc_id in loc_ids:
                    xref = self.get_xref_from_id(actual_model, loc_id)
                    if xref:
                        vals = self.load_vals(model, vals, test_rec)
                        full_domain = [("id", "=", xref.complete_name)]
                        break
            if reset_id:
                vals[ext_id_field] = False
                if model == "res.partner.supplier":
                    vals["vg72_id"] = False
            if vals:
                why, vals = self.extract_why(vals)
                if len(loc_ids) == 1:
                    rec = self.resource_browse(actual_model, loc_ids[0], quiet=True)
                    vals = self.purge_values(rec, vals)
            if vals:
                self.write_log("%s.write(%s, %s, ctx=%s)   # %s <%s>"
                               % (model, loc_ids, vals, ctx, full_domain, why),
                               echo=False)
                clodoo.writeL8(self.ctx, actual_model, loc_ids, vals, context=ctx)
            if child_test_recs:
                if len(loc_ids) > 1:
                    raise IOError(
                        "!!Found too many records for model %s with %s!"
                        % (model, full_domain)
                    )
                loc_id = loc_ids[0]
                child_key = MODEL_WITH_CHILD[model]["child_key"]
                child_domain = [(MODEL_WITH_CHILD[model]["parent_field"], "=", loc_id)]
                parent_field = MODEL_WITH_CHILD[model]["parent_field"]
                child_ids = clodoo.searchL8(
                    self.ctx, child_model, child_domain, order=child_key)
                for ix, child_test_rec in enumerate(child_test_recs):
                    if self.cast_1_value(
                            child_model,
                            parent_field,
                            child_test_rec[parent_field]) != loc_id:
                        continue
                    child_vals = {}
                    child_vals = self.load_vals(child_model, child_vals, child_test_rec)
                    if reset_id:
                        child_vals[ext_id_field] = False
                    if child_vals:
                        why, child_vals = self.extract_why(child_vals)
                        if ix < len(child_ids):
                            child_rec = self.resource_browse(
                                child_model, child_ids[ix], quiet=True)
                            child_vals = self.purge_values(child_rec, child_vals)
                    if not child_vals:
                        continue
                    self.write_log(
                        "%s.write(%s, %s, ctx=%s) # %s"
                        % (child_model, child_ids, child_vals, ctx, child_domain),
                        echo=False)
                    clodoo.writeL8(
                        self.ctx, child_model, child_ids, child_vals, context=ctx)
        self.dirty_any_model(
            identity, model, code=code, domain=domain, reset_id=reset_id)

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

    def write_file_2_pull(self, identity, model, ext_model, vals, mode="w"):
        fqn = pth.join(self.get_exchange_path(identity), "%s.csv" % ext_model)
        data = self.load_csv_file(
            model, fqn, keep_none=True) + [vals] if mode == "a" else [vals]
        with open(fqn, "wb") as fd:
            writer = csv.DictWriter(fd, fieldnames=vals.keys())
            writer.writeheader()
            for vals in data:
                why, vals = self.extract_why(vals)
                writer.writerow(self.cast_value(model, vals, keep_id=False, keep_none=True))
        if fqn not in self.fqn_to_remove:
            self.fqn_to_remove.append(fqn)

    def compare(self, model, loc_value, test_value, mode=None):
        if hasattr(loc_value, "ids") and isinstance(test_value, (list, tuple)):
            loc_value = loc_value.ids or False
        elif hasattr(loc_value, "id"):
            loc_value = loc_value.id or False
        if mode == "id" and isinstance(test_value,basestring):
            test_value = self.cast_1_value(model, mode, loc_value)
        elif isinstance(loc_value, datetime) and isinstance(test_value,basestring):
            loc_value = datetime.strftime(loc_value, "%Y-%m-%d %H:%M:%S")
        elif isinstance(loc_value, date) and isinstance(test_value,basestring):
            loc_value = datetime.strftime(loc_value, "%Y-%m-%d")
        elif (
                isinstance(loc_value, basestring)
                and loc_value.isdigit()
                and isinstance(test_value, (int, long))
        ):
            loc_value = int(loc_value)
        elif (
                isinstance(loc_value, (int, long))
                and isinstance(test_value, basestring)
                and test_value.isdigit()
        ):
            test_value = int(test_value)

        if mode == "nounknown":
            return not loc_value.startswith("Unknown")
        elif mode == "unknown":
            return loc_value.startswith("Unknown")
        elif mode == "delivery":
            return loc_value == test_value + 100000000
        elif mode == "invoice":
            return loc_value == test_value + 200000000
        elif test_value is None:
            return True
        elif mode == "nocase":
            return loc_value.lower() == test_value.lower()
        elif mode and mode == test_value:
            if mode == "supplier":
                return loc_value == "contact"
            return loc_value == test_value
        elif loc_value or test_value:
            return loc_value == test_value
        return True

    def check_records(
            self, identity, model, loc_id, test_rec, child_test_recs, child_model,
            mode=None, state=None, lang=None):
        def check_1_field():
            if loc_name in test_rec:
                if not self.compare(
                        model,
                        getattr(loc_rec, loc_name),
                        test_rec[loc_name],
                        "id" if loc_name == "id" else spec):
                    self.write_log(
                        "!!Field %s[%s].%s: invalid value <%s> expected <%s>"
                        % (model,
                           loc_id,
                           field,
                           getattr(loc_rec, loc_name),
                           test_rec[loc_name]),
                        echo=False)
                    raise IOError(
                        "!!Field %s[%s].%s: invalid value <%s> expected <%s>"
                        % (model,
                           loc_id,
                           field,
                           getattr(loc_rec, loc_name),
                           test_rec[loc_name])
                    )
                self.ctr += 1
                checked = True

        why, test_rec = self.extract_why(test_rec)
        self.write_log(
            "check_record(%s, %s, %s, %s)  ##<%s>"
            % (identity, model, loc_id, test_rec, why),
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
                fields_2_ignore.append(self.get_ext_id_field(ident, model=model))
        child_field = (MODEL_WITH_CHILD[model]["child_field"]
                       if model in MODEL_WITH_CHILD else "")
        loc_rec = self.resource_browse(model, loc_id, lang=lang, quiet=True)
        check_name = checked = False
        for field in [x for x in dir(loc_rec)
                      if (not x.startswith("_") and x != child_field)]:
            loc_name = self.get_loc_name(model, field, identity)[0]
            if loc_name in fields_2_ignore:
                continue
            if loc_name in ("firstname", "lastname"):
                check_name = True
            check_1_field()
        if check_name:
            loc_name = "name"
            check_1_field()
        if not checked:
            self.write_log("No field matched for %s[%s]" % (model, loc_id))
        if child_field:
            parent_field = MODEL_WITH_CHILD[model]["parent_field"]
            child_key = MODEL_WITH_CHILD[model]["child_key"]
            checked = False
            for child_rec in sorted([x for x in loc_rec[child_field]],
                                    key=lambda x: getattr(x, child_key)):
                for child_test_rec in child_test_recs:
                    if (
                            self.cast_1_value(
                                child_model,
                                parent_field,
                                child_test_rec[parent_field]) != loc_id
                            or child_rec[child_key] != child_test_rec[child_key]
                    ):
                        continue
                    checked = True
                    child_why, child_test_rec = self.extract_why(child_test_rec)
                    self.write_log(
                        "check_record(%s, %s, %s/%s, %s)  ##<%s>"
                        % (identity, child_model, loc_id, child_test_rec[child_key],
                           child_test_rec, child_why),
                        echo=False)
                    checked_field = False
                    for field in [x for x in dir(child_rec)
                                  if (not x.startswith("_") and x != parent_field)]:
                        loc_name = self.get_loc_name(child_model, field, identity)[0]
                        if (
                                loc_name in fields_2_ignore
                                or loc_name not in child_test_rec
                                or loc_name == "id"
                        ):
                            continue
                        if not self.compare(
                                child_model,
                                getattr(child_rec, loc_name),
                                child_test_rec[loc_name],
                                "id" if loc_name == "id" else spec):
                            self.write_log(
                                "!!Field %s[%s]/%s[%s].%s:"
                                " invalid value <%s> expected <%s>"
                                % (model,
                                   loc_id,
                                   child_model,
                                   child_rec.id,
                                   field,
                                   getattr(child_rec, loc_name),
                                   child_test_rec[loc_name]),
                                echo=False)
                            raise IOError(
                                "!!Field %s[%s]/%s[%s].%s:"
                                " invalid value <%s> expected <%s>"
                                % (model,
                                   loc_id,
                                   child_model,
                                   child_rec.id,
                                   field,
                                   getattr(child_rec, loc_name),
                                   child_test_rec[loc_name])
                            )
                        self.ctr += 1
                        checked_field = True
                    if not checked_field:
                        self.write_log(
                            "No field matched for %s[%s/%s]"
                            % (child_model,loc_id,  child_test_rec[child_key]))
            if not checked:
                self.write_log("No match child record %s[%s]" % (child_model, loc_id))

    def test_function_synchro(self, model, vals, identity=None, ext_id=None):
        """
        Test function synchro: child record datas are in model values
        """
        if identity:
            vals = self.jacket_vals(vals, identity)
        self.write_log("synchro(%s, %s)" % (model, vals), eol=False)
        rec_id = clodoo.executeL8(self.ctx, model, "synchro", vals)
        self.write_log(str(rec_id), no_ts=True)
        return rec_id

    def test_function_trigger(self, model, ext_model, identity, ext_id):
        fqn = pth.join(self.get_exchange_path(identity), "%s.csv" % ext_model)
        data = self.load_csv_file(model, fqn)
        vals = {}
        for vals in data:
            if ext_id == vals["id"]:
                break
        self.write_log(
            "trigger_one_record(%s, %s, %s)  # %s"
            % (ext_model, ext_id, identity, vals),
            eol=False
        )
        rec_id = clodoo.executeL8(
            self.ctx,
            "ir.model.synchro",
            "trigger_one_record",
            ext_model, identity, ext_id
        )
        self.write_log(str(rec_id), no_ts=True)
        return rec_id

    def merge_supplemetal_vals(
            self, identity, child_model, fn, parent_field, child_field, ext_recs, multi=False):
        child_ext_recs = self.load_csv_file(
            child_model, pth.join(self.get_csv_path(identity), fn))
        if multi:
            for ext_rec in ext_recs:
                ext_rec[child_field] = []
        for child_ext_rec in child_ext_recs:
            child_ext_rec, _, _ = self.prepare_rec(child_ext_rec, 0)
            checked = False
            if parent_field in child_ext_rec:
                parent_id = child_ext_rec[parent_field]
                for ext_rec in ext_recs:
                    if parent_id == ext_rec["id"]:
                        checked = True
                        if not multi:
                            ext_rec[child_field] = child_ext_rec
                        else:
                            ext_rec[child_field].append(child_ext_rec)
                        break
            if not checked:
                raise IOError("No match external id name for %s" % child_ext_rec)

    def load_ext_values(
            self, identity, model, ext_model=None, lang=None, keep_none=False):
        ext_model = ext_model or self.get_ext_model(model, identity)
        if lang:
            fqn = pth.join(self.get_csv_path(identity), ext_model + "." + lang + ".csv")
        else:
            fqn = pth.join(self.get_csv_path(identity), ext_model + ".csv")
        ext_recs_image = self.load_csv_file(model, fqn, keep_none=keep_none)
        if model == "res.partner" and identity.startswith("vg7"):
            self.merge_supplemetal_vals(
                identity,
                "res.partner",
                "customers_shipping_addresses.csv",
                "customer_id",
                "shipping",
                ext_recs_image)
            self.merge_supplemetal_vals(
                identity,
                "res.partner",
                "customers_billing_addresses.csv",
                "customer_id",
                "billing",
                ext_recs_image)
        elif model in MODEL_WITH_CHILD and identity in MODEL_WITH_CHILD[model]:
            self.merge_supplemetal_vals(
                identity,
                MODEL_WITH_CHILD[model]["child_model"],
                MODEL_WITH_CHILD[model][identity]["fqn"],
                MODEL_WITH_CHILD[model][identity]["parent_field"],
                MODEL_WITH_CHILD[model][identity]["child_field"],
                ext_recs_image,
                multi=True)
        return ext_recs_image

    def _add_xref(self, xref, xid, resource):
        module, name = xref.split(".", 1)
        if module == "external":
            return False
        ir_model = "ir.model.data"
        values = {
            "module": module,
            "name": name,
            "model": resource,
            "res_id": xid,
        }
        xref_ids = clodoo.searchL8(
            self.ctx,
            ir_model,
            [("module", "=", module), ("name", "=", name)])
        if not xref_ids:
            return clodoo.createL8(self.ctx, ir_model, values)
        clodoo.writeL8(self.ctx, ir_model, xref_ids[0], values)
        return xref_ids[0]

    def extract_why(self, values):
        if "_why" in values:
            why = values["_why"]
            del values["_why"]
        else:
            why = ""
        return why, values

    def purge_values(self, record, values):
        for (k, v) in values.copy().items():
            if k.startswith("_") or not hasattr(record, k):
                continue
            elif (
                    isinstance(values[k], (int, long))
                    and hasattr(record[k], "id")
                    and values[k] == record[k].id
            ):
                del values[k]
                continue
            elif (
                    isinstance(values[k], (int, long))
                    and isinstance(record[k], basestring)
                    and str(values[k]) == record[k]
            ):
                del values[k]
                continue
            elif values[k] is False and not record[k]:
                del values[k]
                continue
            elif values[k] == record[k]:
                del values[k]
                continue
        return values

    def resource_browse(self, resource, xref=None, quiet=False, lang=None):
        if isinstance(xref, basestring):
            res_id = self.env_ref(xref)
        else:
            res_id = xref
        if not quiet:
            self.write_log("resource_browse(%s, %d, xref=%s)" % (resource, res_id, xref))
        return clodoo.browseL8(
            self.ctx, resource, res_id, context={"lang": lang or self.lang})

    def resource_create(self, resource, values=None, xref=None):
        why, values = self.extract_why(values)
        self.write_log("resource_create(%s, %s, xref=%s)  ##<%s>"
                       % (resource, values, xref, why),
                       eol=False)
        res_id = clodoo.createL8(self.ctx, resource, values)
        self.write_log(str(res_id), no_ts=True)
        if xref:
            self._add_xref(xref, res_id, resource)
        return res_id

    def resource_write(self, resource, domain, values,
                       company_id=False, create=None, unique=None, xref=None):
        why, values = self.extract_why(values)
        if xref:
            unique = True
        if domain is False:
            ids = []
        elif isinstance(domain, basestring):
            ids = self.env_ref(domain)
            ids = [ids] if ids else []
        elif isinstance(domain, (int, long)):
            ids = [domain]
        elif isinstance(domain, (list, tuple)) and isinstance(domain[0], (int, long)):
            ids = domain
        else:
            if company_id:
                domain.append(("company_id", "=", company_id))
            ids = clodoo.searchL8(self.ctx, resource, domain)
        if ids:
            if len(ids) == 1:
                rec = self.resource_browse(resource, ids[0], quiet=True)
                values = self.purge_values(rec, values)
            if len(ids) > 1 or values:
                self.write_log("resource_write(%s, %s, %s, xref=%s)  ##<%s>"
                               % (resource, domain, values, xref, why),
                               eol=False)
                self.write_log(str(ids), no_ts=True)
                clodoo.writeL8(self.ctx, resource, ids, values)
                if unique and len(ids) > 1:
                    self.write_log(
                        "Warning: Too many records '%s(%s)'" % (resource, domain))
                    self.delete_record(resource, [("id", "in", ids[1:])])
                elif xref and isinstance(xref, basestring):
                    self._add_xref(xref, ids[0], resource)
        elif create:
            ids = [self.resource_create(resource, values, xref=xref)]
        return ids

    def load_n_test_model(
        self,
        identity,
        model,
        mode=None,
        ext_model=None,
        fct_test="synchro",
        lang=None,
        reset_id=False,
    ):
        self.write_log(
            "** load_n_test_model(%s, %s, mode=%s, fct=%s, ctx=%s) **"
            % (identity, model, mode, fct_test, lang or {}),
            bb=0 if model == self.prior_model and fct_test == self.prior_fct
            else 1 if model == self.prior_model else 2
        )
        self.prior_model = model
        self.fct = fct_test
        self.init_model(identity, model, reset_id=reset_id, lang=lang)
        ext_model = ext_model or self.get_ext_model(model, identity)
        ext_recs_image = self.load_ext_values(identity, model, lang=lang)
        test_recs, child_test_recs, child_model = self.load_test_recs(model, lang=lang)
        main_ext_id = False
        # wa = "w"
        ext_id_field = self.get_ext_id_field(identity, model=model)
        self.write_log("# Starting %s tests on %s" % (fct_test, model), echo=False)
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
                    model, ext_model, identity=identity, ext_id=ext_id
                )
            if loc_id < 0:
                raise IOError(
                    "Error %d processing %s=%s" % (loc_id, ext_id_field, ext_id))
            checked = False
            for test_rec in test_recs:
                if ext_id == test_rec[ext_id_field]:
                    if loc_id > 0 and isinstance(test_rec.get("id"), basestring):
                        self._add_xref(test_rec["id"], loc_id, model)
                    self.check_records(
                        identity, model, loc_id, test_rec, child_test_recs, child_model,
                        lang=lang)
                    checked = True
                    break
            if not checked:
                raise IOError(
                    "No match record found for %s=%s" % (ext_id_field, ext_id))
        return

    def store_csv_response(self, identity, models, lang=None):
        self.write_log(
            "store_csv_response(%s, %s)" % (identity, models), echo=False)
        for model in models:
            ext_id_field = self.get_ext_id_field(identity, model=model)
            if model not in self.model_wkf:
                self.write_log(
                    "DEVEL TROUBLE: model %s without initialization" % model)
            self.model_wkf[model] = 2
            for id in clodoo.searchL8(
                    self.ctx, model, [(ext_id_field, "!=", False)]):
                self.write_log("%s.write(%s, {%s: False})"
                               % (model, id, ext_id_field))
                clodoo.writeL8(self.ctx, model, id, {ext_id_field: False})
            ext_model = self.get_ext_model(model, identity)
            ext_recs_image = self.load_ext_values(
                identity, model, ext_model=ext_model, lang=lang, keep_none=True)
            main_ext_id = False
            wa = "w"
            # ext_id_field = self.get_ext_id_field(identity, model=model)
            # if not ext_id_field:
            #    raise IOError("No match external id name for %s" % identity)
            for ext_rec in ext_recs_image:
                ext_rec, ext_id, main_ext_id = self.prepare_rec(ext_rec, main_ext_id)
                self.write_file_2_pull(identity, model, ext_model, ext_rec, wa)
                wa = "a"


def run_full_identity_test(ext_test_env, model, test_prio, identity, lang=None):
    if test_prio == "synchro":
        ext_test_env.load_n_test_model(
            identity,
            model,
            fct_test=test_prio,
            reset_id=True,
            lang=lang,
        )
        ext_test_env.load_n_test_model(
            identity,
            model,
            fct_test="trigger",
            lang=lang,
        )
        if model == "res.partner":
            test_prio = "trigger"
    else:
        ext_test_env.load_n_test_model(
            identity,
            model,
            fct_test=test_prio,
            reset_id=True,
            lang=lang,
        )
        ext_test_env.load_n_test_model(
            identity,
            model,
            fct_test="synchro",
            lang=lang,
        )
    return test_prio


def main(cli_args=[]):
    if not cli_args:
        cli_args = sys.argv[1:]
    # Comment or activate following lines for specific test
    # if "--database" not in cli_args:
    #     cli_args.append("--database")
    #     cli_args.append("connect10")
    # if "--database" in cli_args and "--ask" not in cli_args:
    #     cli_args.append("--ask")
    if "--conai" not in cli_args:
        cli_args.append("--conai")
    if not os.environ.get("TEST_CONFN") and "--config" not in cli_args:
        cli_args.append("--config")
        cli_args.append("./tests/logs/zero10.connector.universal_connector.conf")
    ext_test_env = ExtTestEnv(cli_args)
    ext_test_env.setup()

    identity = "vg7:"
    ext_test_env.write_log(
        "*** Starting %s test ***" % identity.upper(), echo=True, bb=3)
    MODELS = (
        "res.country",
        "res.country.state",
        "res.partner",
        "res.partner.supplier",
        "product.uom",
        "product.product",
        "account.tax",
        "account.payment.term",
        "stock.picking.transportation_reason",
        "sale.order",
        "purchase.order",
        "stock.picking.package.preparation",
    )
    ext_test_env.store_csv_response(identity, MODELS)
    test_prio = "synchro"
    for model in MODELS:
        test_prio = run_full_identity_test(ext_test_env, model, test_prio, identity)

    identity = "oe8:"
    ext_test_env.write_log(
        "*** Starting %s test ***" % identity.upper(), echo=True, bb=3)
    MODELS = (
            "account.account.type",
            "res.country",
            "res.country.state",
            "account.account",
            "res.partner",
            "res.company",
            "res.users",
            "product.uom",
            "product.template",
            "product.product",
            "account.tax",
            "account.journal",
            "account.payment.term",
            "stock.picking.transportation_reason",
            "stock.picking.carriage_condition",
            "stock.picking.goods_description",
            "stock.picking.transportation_method",
            "sale.order",
            "purchase.order",
            "stock.picking.package.preparation",
            "account.invoice",
    )
    ext_test_env.store_csv_response(identity, MODELS)
    test_prio = "synchro"
    for model in MODELS:
        test_prio = run_full_identity_test(ext_test_env, model, test_prio, identity)

    lang = "en_US"
    ext_test_env.write_log(
        "*** Starting %s test (%s) ***" % (identity.upper(), lang), echo=True, bb=3)
    MODELS = (
            # "account.account.type",
            "res.country",
    )
    ext_test_env.store_csv_response(identity, MODELS, lang=lang)
    test_prio = "synchro"
    for model in MODELS:
        test_prio = run_full_identity_test(
            ext_test_env, model, test_prio, identity, lang=lang)

    ext_test_env.teardown()
    return 0


if __name__ == "__main__":
    exit(main())
