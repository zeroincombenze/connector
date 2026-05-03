# -*- coding: utf-8 -*-
"""Universal connector tests
*Warning*
Universal connector module connect local Odoo instance with external instance.
Without external running instance, these test CANNOT be executed

**************************************************************************
In order to run full test on the same host MUST be active follow instance:

* Odoo 10.0 with OCA modules; http/xmlrpc port: 8270; DB name: oca10
* Odoo 12.0 with OCA modules; http/xmlrpc port: 8272; DB name: oca12

"""
import os
import os.path as pth
import logging
from python_plus import _u
from .testenv import MainTest as SingleTransactionCase

_logger = logging.getLogger(__name__)

TEST_SYNCHRO_CHANNEL = {
    # "z0bug.localhost-oca10": {
    #     "name": "Test Odoo 10.0",
    #     "identity": "odoo",
    #     "client_key": "oca10",
    #     "odoo_version": "10.0",
    #     "method": "JSON",
    #     "password": "admin",
    #     "counterpart_url": "admin@localhost:8270",
    #     "prefix": "oe10",
    # },
    "z0bug.localhost-odoo12": {
        "name": "odoo12",
        "identity": "odoo",
        "client_key": "demo12",
        "odoo_version": "12.0",
        "method": "JSON",
        "password": "admin",
        "counterpart_url": "admin@localhost:8172",
        "prefix": "oe8",
        "tracelevel": "4",
        "sequence": 16,
    },
    "z0bug.csv-vg7": {
        "name": "vg7",
        "identity": "vg7",
        "method": "CSV",
        # "exchange_path": self.get_exchange_path(backend.prefix),
        "prefix": "vg7",
        "ignore_child_lines": False,
        # "renum_lines": True,
        "tracelevel": "4",
        "sequence": 10,
    },
}
TEST_SETUP_LIST = ["synchro.channel", ]


class MyTest(SingleTransactionCase):

    def setUp(self):
        super(MyTest, self).setUp()
        self.debug_level = 0
        data = {"TEST_SETUP_LIST": TEST_SETUP_LIST}
        for resource in TEST_SETUP_LIST:
            item = "TEST_%s" % resource.upper().replace(".", "_")
            data[item] = globals()[item]
        self.declare_all_data(data)
        self.setup_env()

    def tearDown(self):
        super(MyTest, self).tearDown()

    def get_exchange_path(self, backend):
        testdir = pth.join(pth.dirname(__file__))
        root = ""
        if backend.identity == "vg7":
            root = pth.join(testdir, "data", "vg7")
            if not pth.isdir(root):
                os.makedirs(root)
        return root

    def _test_assign_backend(self, xref):
        backend = self.resource_browse(xref)
        vals = {backend.prefix + ":name": ""}
        assigned_backed = self.env["synchro.channel"].assign_backend(vals)
        self.assertEqual(backend, assigned_backed)
        if backend.identity == "vg7":
            vals = {"name": ""}
            assigned_backed = self.env["synchro.channel"].assign_backend(vals)
            self.assertEqual(backend, assigned_backed)

    def _test_backend_misc(self, xref):
        IrModelSynchro = self.env["ir.model.synchro"]
        backend = self.resource_browse(xref)
        model = "res.partner"
        ext_id_name = IrModelSynchro.get_loc_ext_id_name(backend, model)
        if backend.identity == "vg7":
            self.assertEqual("vg7_id", ext_id_name)
        else:
            self.assertEqual("oe8_id", ext_id_name)

        ext_id = IrModelSynchro.get_loc_ext_id_value(backend, model, 1)
        self.assertEqual(1, ext_id)
        if backend.identity == "vg7":
            ext_id = IrModelSynchro.get_loc_ext_id_value(
                backend, model, 1, spec="delivery")
            self.assertEqual(100000001, ext_id)

        if backend.identity == "odoo":
            self.env["synchro.channel.model"].build_odoo_synchro_model(
                backend, model, model=model)

        dirmap = backend.find_model_channel(model_name=model)
        self.assertTrue(dirmap)
        self.assertEqual(model, dirmap.name)

        if backend.identity == "vg7":
            ext_model = "customers"
            dirmap = backend.find_model_channel(ext_model=ext_model)
            self.assertTrue(dirmap)
            self.assertEqual(ext_model, dirmap.counterpart_name)
            self.assertEqual(model, dirmap.name)

    def _test_counterpart_model_response(self, xref):
        backend = self.resource_browse(xref)
        if backend.identity == "vg7":
            ext_model = "customers"
            dirmap = backend.find_model_channel(ext_model=ext_model)
            ext_id = 101
            vals = dirmap.get_counterpart_response(ext_id=ext_id)
            self.assertTrue(vals)
            self.assertEqual("Prima Alpha S.p.A.", vals["name"])
        elif backend.identity == "odoo":
            ext_model = "res.partner"
            dirmap = backend.find_model_channel(ext_model=ext_model)
            ext_id = 1
            vals = dirmap.get_counterpart_response(ext_id=ext_id)
            self.assertTrue(vals)
            self.assertTrue(vals["name"])

    def _test_misc(self):
        IrModelSynchro = self.env["ir.model.synchro"]
        vmodel = IrModelSynchro.get_vmodel("res.partner", "delivery")
        self.assertEqual("res.partner.shipping", vmodel)
        actual_model = IrModelSynchro.get_actual_model(vmodel, only_name=True)
        self.assertEqual("res.partner", actual_model)
        spec = IrModelSynchro.get_spec_from_vmodel(vmodel)
        self.assertEqual("delivery", spec)
        vmodel = IrModelSynchro.get_vmodel("res.partner", "supplier")
        self.assertEqual("res.partner.supplier", vmodel)
        actual_model = IrModelSynchro.get_actual_model(vmodel, only_name=True)
        self.assertEqual("res.partner", actual_model)
        spec = IrModelSynchro.get_spec_from_vmodel(vmodel)
        self.assertEqual("supplier", spec)

    def _test_purge(self):
        self.env["ir.model.synchro.log"].purge_log()

    def _test_simple_connection(self, xref):
        _logger.info(u"🎺 Connection test backend %s" % _u(xref))
        backend = self.resource_browse(xref)
        root = self.get_exchange_path(backend)
        self.resource_edit(
            backend,
            web_changes=[("exchange_path", root)],
            actions="button_check_connection",
        )
        self.assertEqual(backend.state, 'checked')

        self.resource_edit(
            backend,
            actions="button_reset_to_draft",
        )
        self.assertEqual(backend.state, 'draft')

        backend = self.resource_browse(xref)
        self.resource_edit(
            backend,
            actions="button_check_connection",
        )
        self.assertEqual(backend.state, 'checked')
        self.env["ir.model.synchro.cache"].setup_model_in_backends(
            backend, model="res.partner")
        if backend.identity == "vg7":
            self.env["ir.model.synchro.cache"].setup_model_in_backends(
                backend, model="res.partner.shipping")

    def _test_import_currency(self, xref):
        Synchro = self.env["ir.model.synchro"]
        backend = self.resource_browse(xref)
        if backend.identity != "vg7":
            _logger.info(u"🎺 Import currency from %s" % _u(xref))
            rec_id = Synchro.trigger_one_record("res.currency", backend.prefix, 1)
            self.assertEqual(1, rec_id)

    def _test_import_country(self, xref):
        Synchro = self.env["ir.model.synchro"]
        backend = self.resource_browse(xref)
        model = "res.country"
        _logger.info(u"🎺 Import country from %s" % _u(xref))
        if backend.identity == "vg7":
            rec_id = Synchro.trigger_one_record("countries", backend.prefix, 39)
            self.assertTrue(rec_id > 0)
            country = self.env[model].browse(rec_id)
            self.assertEqual("IT", country.code)
            self.assertEqual(39, country.vg7_id)
        else:
            rec_id = Synchro.trigger_one_record(model, backend.prefix, 233)
            # self.assertEqual(235, rec_id)

    def _test_import_partner(self, xref):
        Synchro = self.env["ir.model.synchro"]
        backend = self.resource_browse(xref)
        model = "res.partner"
        _logger.info(u"🎺 Import partner from %s" % _u(xref))
        if backend.identity == "vg7":
            rec_id = Synchro.trigger_one_record("customers", backend.prefix, 101)
            self.assertTrue(rec_id > 0)
            partner = self.env[model].browse(rec_id)
            self.assertEqual("Prima Alpha S.p.A.", partner.name)
            self.assertEqual(101, partner.vg7_id)
        else:
            rec_id = Synchro.trigger_one_record(model, backend.prefix, 1)
            # self.assertEqual(235, rec_id)

    def _test_import_partner_bank(self, xref):
        Synchro = self.env["ir.model.synchro"]
        backend = self.resource_browse(xref)
        model = "res.partner.bank"
        _logger.info(u"🎺 Import bank from %s" % _u(xref))
        if backend.identity == "vg7":
            rec_id = Synchro.trigger_one_record("banks", backend.prefix, 111)
            self.assertTrue(rec_id > 0)
            bank = self.env[model].browse(rec_id)
            self.assertEqual("IT73C0102001011010101987654", bank.acc_number)
            self.assertEqual(111, bank.vg7_id)
        # else:
        #     rec_id = Synchro.trigger_one_record(model, backend.prefix, 233)
        #     self.assertEqual(235, rec_id)

    def _test_import_payment(self, xref):
        Synchro = self.env["ir.model.synchro"]
        backend = self.resource_browse(xref)
        model = "account.payment.term"
        _logger.info(u"🎺 Import payment from %s" % _u(xref))
        if backend.identity == "vg7":
            rec_id = Synchro.trigger_one_record("payments", backend.prefix, 31)
            self.assertTrue(rec_id > 0)
            payment = self.env[model].browse(rec_id)
            self.assertEqual("BB 30GG/FM+10", payment.name)
            self.assertEqual(31, payment.vg7_id)
        # else:
        #     rec_id = Synchro.trigger_one_record(model, backend.prefix, 233)
        #     self.assertEqual(235, rec_id

    def _test_import_tax_code(self, xref):
        Synchro = self.env["ir.model.synchro"]
        backend = self.resource_browse(xref)
        model = "account.tax"
        _logger.info(u"🎺 Import payment from %s" % _u(xref))
        if backend.identity == "vg7":
            rec_id = Synchro.trigger_one_record("tax_codes", backend.prefix, 15)
            self.assertTrue(rec_id > 0)
            tax = self.env[model].browse(rec_id)
            self.assertEqual(15, tax.amount)
            self.assertEqual("sale", tax.type_tax_use)
            self.assertEqual(15, tax.vg7_id)
        # else:
        #     rec_id = Synchro.trigger_one_record(model, backend.prefix, 233)
        #     self.assertEqual(235, rec_id

    def _test_import_partner_supplier(self, xref):
        Synchro = self.env["ir.model.synchro"]
        backend = self.resource_browse(xref)
        model = "res.partner"
        _logger.info(u"🎺 Import partner supplier from %s" % _u(xref))
        if backend.identity == "vg7":
            rec_id = Synchro.trigger_one_record("suppliers", backend.prefix, 101)
            self.assertTrue(rec_id > 0)
            partner = self.env[model].browse(rec_id)
            self.assertEqual("Import Export Trifoglio s.r.l.", partner.name)
            self.assertEqual("IT01234560017", partner.vat)
            self.assertEqual(101, partner.vg72_id)
        # else:
        #     rec_id = Synchro.trigger_one_record(model, backend.prefix, 233)
        #     self.assertEqual(235, rec_id

    def _test_import_product(self, xref):
        Synchro = self.env["ir.model.synchro"]
        backend = self.resource_browse(xref)
        model = "product.product"
        _logger.info(u"🎺 Import product from %s" % _u(xref))
        if backend.identity == "vg7":
            rec_id = Synchro.trigger_one_record("products", backend.prefix, 11)
            self.assertTrue(rec_id > 0)
            product = self.env[model].browse(rec_id)
            self.assertEqual("Prodotto Alpha", product.name)
            self.assertEqual("AA", product.default_code)
            self.assertEqual(11, product.vg7_id)
        # else:
        #     rec_id = Synchro.trigger_one_record(model, backend.prefix, 233)
        #     self.assertEqual(235, rec_id

    def test_connection(self):
        # This test requires external Odoo instance active. See header
        _logger.info(
            "🎺🎺 Starting connection test on ports 8270 (db=oca10) and 8272 (db=oca12)"
        )
        self._test_misc()
        for xref in self.get_resource_data_list("synchro.channel"):
            self._test_simple_connection(xref)
            self._test_assign_backend(xref)
            self._test_backend_misc(xref)
            self._test_counterpart_model_response(xref)
            self._test_import_currency(xref)
            self._test_import_country(xref)
            self._test_import_partner(xref)
            self._test_import_partner_bank(xref)
            self._test_import_payment(xref)
            self._test_import_tax_code(xref)
            self._test_import_partner_supplier(xref)
            self._test_import_product(xref)
        self._test_purge()
