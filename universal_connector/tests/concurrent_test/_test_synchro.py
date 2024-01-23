#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
# from past.builtins import basestring

import os
import sys
from datetime import datetime
import logging
from .testenv_rpc import MainTest as SingleTransactionCase

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser
import odoorpc
if sys.version_info[0] == 2:
    import oerplib
else:
    import oerplib3 as oerplib
try:
    from z0lib.z0lib import z0lib
except ImportError:
    from z0lib import z0lib


_logger = logging.getLogger(__name__)
__version__ = "10.0.0.2.5"

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
    # "l10n_it_conai",
    # "universal_connector_conai",
]


class TestSynchro(SingleTransactionCase):

    def __init__(self):
        config = ConfigParser.ConfigParser({})
        config.read(__file__.replace(".py", ".conf"))
        self.lang = "en_US"
        if config.has_option("options", "lang"):
            self.lang = config.get("options", "lang")
        self.odoo_version = os.environ["ODOO_VERSION"]
        self.odoo_maj_version = int(self.odoo_version.split(".")[0])
        self.logfile = os.environ["LOGFILE"]
        if not os.path.isfile(self.logfile):
            self.logfile = None
        self.odoo_rundir = os.environ["ODOO_RUNDIR"]
        self.test_confn = os.environ["TEST_CONFN"]
        self.test_db = os.environ["TEST_DB"]
        self.test_vdir = os.environ["TEST_VDIR"]
        config = ConfigParser.ConfigParser({})
        config.read(self.test_confn)
        if config.has_option("options", "http_port"):
            port = int(config.get("options", "http_port"))
        elif config.has_option("options", "xmlrpc_port"):
            port = int(config.get("options", "xmlrpc_port"))
        else:
            port = 8069
        protocol = "xmlrpc" if self.odoo_maj_version < 10 else "jsonrpc"
        self.logger_info(
            "Starting client process (port=%d, prot='%s', db='%s', user='admin')"
            % (port, protocol, self.test_db))
        self.connect_odoo(protocol=protocol, port=port, db=self.test_db)

    def cnx(self, protocol, port, raise_if_not_found=True):
        try:
            if protocol == "jsonrpc":
                odoo = odoorpc.ODOO("localhost", protocol, port)
                self.pypi = "odoorpc"
            else:
                odoo = oerplib.OERP(protocol=protocol, port=port)
                self.pypi = "oerplib"
            self.protocol = protocol
            self.port = port
        except BaseException:                                       # pragma: no cover
            odoo = False
            if raise_if_not_found:
                raise RuntimeError("Cannot connect to Odoo")  # pragma: no cover
        return odoo

    def connect_odoo(self, protocol=None, port=None, db=None, only_login=False):
        if not only_login:
            self.odoo = self.cnx(protocol=protocol, port=port)
        if protocol == "jsonrpc":
            user = self.odoo.login(db=db, login="admin", password="admin")
        else:
            user = self.odoo.login(database=db, user="admin", passwd="admin")
        return user

    def log_fmt(self, mesg):
        log_mesg = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S,%f")[: -3]
        log_mesg += " "
        log_mesg += str(os.getpid())
        log_mesg += " RCP "
        log_mesg += os.environ["TEST_DB"]
        log_mesg += " "
        log_mesg += os.path.splitext(os.path.basename(__file__))[0]
        log_mesg += ": "
        log_mesg += mesg
        return log_mesg

    def logger_info(self, mesg):
        log_mesg = self.log_fmt(mesg)
        print(log_mesg)
        # if self.logfile:
        #     with open(self.logfile, "a") as fd:
        #         fd.write(log_mesg + "\n")

    def resource_search(self, resource, domain, order=None):
        if self.pypi == "odoorpc":
            return self.resource_browse(
                resource,
                self.odoo.env[resource].search(domain, order=order)
            )
        elif self.pypi.startswith("oerplib"):
            return self.resource_browse(
                resource,
                self.odoo.search(resource, domain, order=order)
            )
        return []

    def resource_browse(self, resource, id):
        if self.pypi == "odoorpc":
            return self.odoo.env[resource].browse(id)
        elif self.odoo.startswith("oerplib"):
            return self.odoo.browse(resource, id)
        return None

    def resource_execute(self, resource, action, *args):
        if self.odoo_maj_version < 10 and action == "invoice_open":
            return self.odoo.exec_workflow(resource, action, *args)
        if self.pypi in ("odoorpc", "oerplib", "oerplib3"):
            return self.odoo.execute(resource, action, *args)
        return False

    def resource_synchro(self, resource, vals):
        return self.odoo.execute(resource, "synchro", vals)

    def install_modules(self, module_list=None):
        resource = "ir.module.module"
        for name in module_list:
            module = self.resource_search(resource, [('name', '=', name)])
            # if not module:
            #     self.logger_info(
            #         "Module '%s' not found in DB %s" % (module, self.test_db))
            #     continue
            # if module.state != 'installed':
            self.logger_info("Installling %s" % module.name)
            self.resource_synchro(
                resource, {"eo8:name": name, "oe8:state": "installed"})
            # ctr = 15
            # while module.state != 'installed':
            #     if not ctr:
            #         break
            #     time.sleep(1)
            #     module = self.resource_browse(resource, module.id)
            #     ctr -= 1
            # time.sleep(1)

    def install_lang(self, lang):
        model = "res.lang"
        if lang not in ("en_US", "."):
            vals = {"code": lang, "oe8:id": 39}
            self.logger_info("Installling language %s" % lang)
            self.resource_synchro(model, vals)

    def full_tests(self):
        # self.install_lang(self.lang)
        self.install_modules(MODULE_LIST)
        return 0


def main():
    parser = z0lib.parseoptargs(
        "Odoo test environment", "© 2020-2023 by SHS-AV s.r.l.", version=__version__
    )
    parser.add_argument("-h")
    parser.add_argument("-n")
    parser.add_argument("-V")
    parser.parseoptargs(sys.argv[1:], apply_conf=False)
    test_synchro = TestSynchro()
    return test_synchro.full_tests()


if __name__ == "__main__":
    exit(main())
