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
import csv
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
        "prefix": "vg7",
        "child_lines_mode": "N",
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

    # def tearDown(self):
    #     super(MyTest, self).tearDown()

    def get_exchange_path(self, backend):
        testdir = pth.join(pth.dirname(__file__))
        root = ""
        if backend.identity == "vg7":
            root = pth.join(testdir, "data", "vg7")
            if not pth.isdir(root):
                os.makedirs(root)
        return root

    def load_csv_file(self, fqn,
                      billing_fqn=None, shipping_fqn=None,
                      lines_fqn=None, only_merge=False):
        ext_model = os.path.basename(fqn).rsplit(".", 1)[0]
        partner_purge = "partner" in ext_model or "purchase" in ext_model
        partner_only_merge = "orders" in ext_model
        billing_data = self.load_csv_file(
            billing_fqn, only_merge=True) if billing_fqn else []
        shipping_data = self.load_csv_file(
            shipping_fqn, only_merge=partner_only_merge) if shipping_fqn else []
        lines_data = self.load_csv_file(
            lines_fqn, only_merge=True) if lines_fqn else []
        pk = (
            "order_id" if "orders" in ext_model
            else "customer_shipping_id" if "shipping" in ext_model
            else "ddt_id" if "ddt" in ext_model
            else "id")
        partner_key = "supplier_id" if ("purchase" in ext_model
                                        or "supplier" in ext_model) else "customer_id"
        datas = []
        if not pth.isfile(fqn):
            raise IOError("File %s not found!" % fqn)
        with open(fqn, "r") as fd:
            header = False
            id_ix = 0
            partner_ix = 0
            merge_items = []
            reader = csv.reader(fd)
            # row is a list, *_data are dict
            for row in reader:
                if not header:
                    if pk in row:
                        id_ix = row.index(pk)
                    if partner_key in row:
                        partner_ix = row.index(partner_key)
                    if partner_only_merge:
                        header = []
                        for i, name in enumerate(row):
                            if not name.startswith("billing_"):
                                header.append(name)
                            else:
                                # Store index in descending key in order to delete
                                merge_items.insert(0, ((name, i)))
                    else:
                        header = row
                    if billing_data:
                        header.append("billing")
                    if shipping_data:
                        header.append("shipping")
                    if lines_data:
                        header.append("order_rows")
                    continue
                if billing_data:
                    for billing in billing_data:
                        if billing.get(partner_key, 0) == row[partner_ix]:
                            if partner_only_merge:
                                for (name, i) in merge_items:
                                    billing[name] = row[i]
                                    del row[i]
                            if partner_purge:
                                del billing[partner_key]
                            if partner_key == "supplier_id":
                                del billing["billing_payment_id"]
                            row.append(billing)
                            break
                if shipping_data:
                    for shipping in shipping_data:
                        if shipping[partner_key] == row[partner_ix]:
                            if partner_key == "supplier_id":
                                del shipping[partner_key]
                            row.append(shipping)
                            break
                if lines_data:
                    lines = []
                    for line in lines_data:
                        if line[pk] == row[id_ix]:
                            lines.append(line)
                    row.append(lines)
                datas.append(dict(zip(header, row)))
        if not only_merge:
            new_fqn = os.path.join(os.path.dirname(os.path.dirname(fqn)),
                                   os.path.basename(fqn))
            with open(new_fqn, "wb") as fd:
                writer = csv.DictWriter(fd, fieldnames=header)
                writer.writeheader()
                for vals in datas:
                    writer.writerow(vals)
        return datas

    def prepare_env_regresion(self):
        xref = "z0bug.csv-vg7"
        backend = self.resource_browse(xref)
        root = self.get_exchange_path(backend)

        for fn in (
                "banks",
                "causals",
                "countries",
                "payments",
                "products",
                "regions",
                "tax_codes",
                "ums"
        ):
            fqn = os.path.join(root, fn + ".csv")
            self.load_csv_file(fqn)

        fqn = os.path.join(root, "customers.csv")
        billing_fqn = os.path.join(root, "customers_billing_addresses.csv")
        shipping_fqn = os.path.join(root, "customers_shipping_addresses.csv")
        self.load_csv_file(fqn, billing_fqn=billing_fqn, shipping_fqn=shipping_fqn)

        fqn = os.path.join(root, "orders.csv")
        billing_fqn = os.path.join(root, "customers_billing_addresses.csv")
        shipping_fqn = os.path.join(root, "customers_shipping_addresses.csv")
        lines_fqn = os.path.join(root, "orders.line.csv")
        self.load_csv_file(fqn,
                           billing_fqn=billing_fqn,
                           shipping_fqn=shipping_fqn,
                           lines_fqn=lines_fqn)

        fqn = os.path.join(root, "ddt.csv")
        lines_fqn = os.path.join(root, "ddt.line.csv")
        self.load_csv_file(fqn, lines_fqn=lines_fqn)

        fqn = os.path.join(root, "purchase_orders.csv")
        billing_fqn = os.path.join(root, "supplier_billing_addresses.csv")
        shipping_fqn = os.path.join(root, "supplier_shipping_addresses.csv")
        lines_fqn = os.path.join(root, "purchase_orders.line.csv")
        self.load_csv_file(fqn,
                           billing_fqn=billing_fqn,
                           shipping_fqn=shipping_fqn,
                           lines_fqn=lines_fqn)

        backend.button_reset_to_draft()
        backend.write({"exchange_path": os.path.dirname(root), "child_lines_mode": ""})
        backend.button_check_connection()

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
        ext_id_name = IrModelSynchro.get_ext_id_name(backend, model)
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

    def _test_import_country_state(self, xref):
        Synchro = self.env["ir.model.synchro"]
        backend = self.resource_browse(xref)
        model = "res.country.state"
        _logger.info(u"🎺 Import country state from %s" % _u(xref))
        if backend.identity == "vg7":
            rec_id = Synchro.trigger_one_record("regions", backend.prefix, 2)
            self.assertTrue(rec_id > 0)
            country = self.env[model].browse(rec_id)
            self.assertEqual("MI", country.code)
            self.assertEqual(2, country.vg7_id)
        # else:
        #     rec_id = Synchro.trigger_one_record(model, backend.prefix, 233)
        #     self.assertEqual(235, rec_id)

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
            rec_id = Synchro.trigger_one_record("products", backend.prefix, 3000011)
            self.assertTrue(rec_id > 0)
            product = self.env[model].browse(rec_id)
            self.assertEqual("Prodotto Alpha", product.name)
            self.assertEqual("AA", product.default_code)
            self.assertEqual(3000011, product.vg7_id)
        # else:
        #     rec_id = Synchro.trigger_one_record(model, backend.prefix, 233)
        #     self.assertEqual(235, rec_id

    def _test_import_uom(self, xref):
        Synchro = self.env["ir.model.synchro"]
        backend = self.resource_browse(xref)
        model = "product.uom"
        _logger.info(u"🎺 Import uom from %s" % _u(xref))
        if backend.identity == "vg7":
            rec_id = Synchro.trigger_one_record("ums", backend.prefix, 3)
            self.assertTrue(rec_id > 0)
            uom = self.env[model].browse(rec_id)
            self.assertEqual("Unit(s)", uom.name)
            self.assertEqual(3, uom.vg7_id)
        # else:
        #     rec_id = Synchro.trigger_one_record(model, backend.prefix, 233)
        #     self.assertEqual(235, rec_id

    def _test_regression_partner(self, delete_before=False):
        Synchro = self.env["ir.model.synchro"]
        xref = "z0bug.csv-vg7"
        backend = self.resource_browse(xref)
        model = "res.partner"
        _logger.info(u"🎺 Import partner from %s" % _u(xref))
        if delete_before:
            self.env["res.partner.bank"].search([("vg7_id", "=", 111)]).unlink()
            self.env["account.payment.term"].search([("vg7_id", "=", 311)]).unlink()
            self.env[model].search([("vg7_id", "=", 101)]).unlink()

        rec_id = Synchro.trigger_one_record("customers", backend.prefix, 101)
        self.assertTrue(rec_id > 0)
        partner = self.env[model].browse(rec_id)
        self.assertEqual("Prima Alpha S.p.A.", partner.name)
        self.assertEqual(101, partner.vg7_id)
        self.assertEqual("contact", partner.type)
        self.assertTrue(partner.child_ids)
        self.assertTrue(partner.bank_ids)
        self.assertEqual("IT73C0102001011010101987654",
                         partner.bank_ids[0].acc_number)
        self.assertTrue(partner.property_payment_term_id)
        self.assertEqual("BB 30GG/FM+10", partner.property_payment_term_id.name)
        delivery = self.env[model].search([("parent_id", "=", rec_id)])
        self.assertTrue(delivery)
        self.assertTrue(len(delivery) == 1)
        self.assertEqual("delivery", delivery.type)
        self.assertEqual(100000001, delivery.vg7_id)

        rec_id = Synchro.trigger_one_record("customers", backend.prefix, 109)
        self.assertTrue(rec_id > 0)
        partner = self.env[model].browse(rec_id)
        self.assertEqual("Rossi Mario", partner.name)
        self.assertEqual(109, partner.vg7_id)
        self.assertEqual("contact", partner.type)

    def _test_regression_order(self, delete_before=False):
        Synchro = self.env["ir.model.synchro"]
        xref = "z0bug.csv-vg7"
        backend = self.resource_browse(xref)
        model = "sale.order"
        _logger.info(u"🎺 Import order from %s" % _u(xref))
        if delete_before:
            for order in self.env[model].search([("vg7_id", "=", 101)]):
                order.action_cancel()
                order.unlink()

        order_id = 131
        rec_id = Synchro.trigger_one_record("orders", backend.prefix, order_id)
        self.assertTrue(rec_id > 0)
        order = self.env[model].browse(rec_id)
        self.assertEqual("240131", order.name)
        self.assertEqual("sale", order.state)
        self.assertTrue(len(order.order_line) > 0)
        self.assertEqual(101, order.partner_id.vg7_id)
        self.assertEqual(order.partner_id, order.partner_invoice_id)
        self.assertEqual(100000001, order.partner_shipping_id.vg7_id)
        # Now simulate the VG7 behavior
        fqn = os.path.join(backend.exchange_path, "orders.csv")
        orders_data = self.load_csv_file(fqn)
        for order_data in orders_data:
            if int(order_data["order_id"]) != order_id:
                continue
            for nm in (
                    "iva", "order_id", "order_state",
                    "customer_id", "customer_shipping_id"
            ):
                if order_data[nm]:
                    order_data[nm] = int(order_data[nm])
            order_data["order_rows"] = eval(order_data["order_rows"])
            del order_data["billing"]
            del order_data["shipping"]
            order_lines = order_data["order_rows"]
            del order_data["order_rows"]
            vals = {
                "vg7:%s" % k: v for k, v in order_data.items()
            }
            vals[":origin"] = "test_backend"
            rec_id = Synchro.synchro("sale.order", vals)
            self.assertTrue(rec_id > 0)
            order = self.env[model].browse(rec_id)
            self.assertEqual("240131", order.name)
            self.assertEqual("draft", order.state)
            for order_line in order_lines:
                order_line["job_name"] = (
                    order_line["job_name"] + "\nCustomized work " + order_line["id"])
                for nm in ("id", "order_id"):
                    if order_line[nm]:
                        order_line[nm] = int(order_line[nm])
                for nm in ("quantity", "unitary_price", "weight"):
                    if order_line[nm]:
                        order_line[nm] = eval(order_line[nm])
                vals = {
                    "vg7:%s" % k: v for k, v in order_line.items()
                }
                line_id = Synchro.synchro("sale.order.line", vals)
                self.assertTrue(line_id > 0)
            errcode = Synchro.commit("sale.order", rec_id)
            self.assertEqual(errcode, rec_id)
            order = self.env[model].browse(rec_id)
            self.assertEqual("240131", order.name)
            self.assertEqual("sale", order.state)
            self.assertTrue(len(order.order_line) > 0)
            self.assertEqual(101, order.partner_id.vg7_id)
            self.assertEqual(order.partner_id, order.partner_invoice_id)
            self.assertEqual(100000001, order.partner_shipping_id.vg7_id)
            break

        order_id = 132
        rec_id = Synchro.trigger_one_record("orders", backend.prefix, order_id)
        self.assertTrue(rec_id > 0)
        order = self.env[model].browse(rec_id)
        self.assertEqual("240132", order.name)
        self.assertEqual("sale", order.state)
        self.assertTrue(len(order.order_line) > 0)
        self.assertEqual(109, order.partner_id.vg7_id)
        self.assertEqual(order.partner_id, order.partner_invoice_id)
        self.assertEqual(109, order.partner_shipping_id.vg7_id)

    def _test_regression_ddt(self, delete_before=False):
        Synchro = self.env["ir.model.synchro"]
        xref = "z0bug.csv-vg7"
        backend = self.resource_browse(xref)
        model = "stock.picking.package.preparation"
        _logger.info(u"🎺 Import ddt from %s" % _u(xref))
        if delete_before:
            for ddt in self.env[model].search([("vg7_id", "=", 101)]):
                ddt.set_draft()
                ddt.unlink()

        ddt_id = 231
        rec_id = Synchro.trigger_one_record("ddt", backend.prefix, ddt_id)
        self.assertTrue(rec_id > 0)
        ddt = self.env[model].browse(rec_id)
        self.assertEqual("24/231", ddt.ddt_number)
        self.assertTrue(len(ddt.line_ids) > 0)
        self.assertEqual(101, ddt.partner_id.vg7_id)
        self.assertEqual(100000001, ddt.partner_shipping_id.vg7_id)

        ddt_id = 232
        rec_id = Synchro.trigger_one_record("ddt", backend.prefix, ddt_id)
        self.assertTrue(rec_id > 0)
        ddt = self.env[model].browse(rec_id)
        self.assertEqual("24/232", ddt.ddt_number)
        self.assertTrue(len(ddt.line_ids) > 0)
        self.assertEqual(109, ddt.partner_id.vg7_id)
        self.assertEqual(109, ddt.partner_shipping_id.vg7_id)

    def _test_regression_purchase_order(self, delete_before=False):
        Synchro = self.env["ir.model.synchro"]
        xref = "z0bug.csv-vg7"
        backend = self.resource_browse(xref)
        model = "purchase.order"
        _logger.info(u"🎺 Import purchase order from %s" % _u(xref))
        if delete_before:
            for order in self.env[model].search([("vg7_id", "=", 101)]):
                order.button_cancel()
                order.unlink()
        rec_id = Synchro.trigger_one_record("purchase_orders", backend.prefix, 111)
        self.assertTrue(rec_id > 0)
        order = self.env[model].browse(rec_id)
        self.assertEqual("111", order.name)
        self.assertEqual("PO-24517", order.partner_ref)
        self.assertEqual("purchase", order.state)
        self.assertTrue(len(order.order_line) > 0)
        self.assertEqual(101, order.partner_id.vg72_id)

    def test_connection(self):
        # This test requires external Odoo instance active. See header
        _logger.info(
            "🎺🎺 Starting connection test on 8172 (db=demo12)"
        )
        self._test_misc()
        for xref in self.get_resource_data_list("synchro.channel"):
            self._test_simple_connection(xref)
            self._test_assign_backend(xref)
            self._test_backend_misc(xref)
            self._test_counterpart_model_response(xref)
            self._test_import_currency(xref)
            self._test_import_country(xref)
            self._test_import_country_state(xref)
            self._test_import_partner(xref)
            self._test_import_partner_bank(xref)
            self._test_import_payment(xref)
            self._test_import_tax_code(xref)
            self._test_import_partner_supplier(xref)
            self._test_import_uom(xref)
            self._test_import_product(xref)
        self._test_purge()

        ###################################################################
        # FUNCTIONAL TESTS
        ###################################################################
        _logger.info(
            "🎺🎺 Starting Regression test"
        )
        self.prepare_env_regresion()
        # Test on record already in DB by previous tests
        self._test_regression_partner()
        # Delete all record and try again
        self._test_regression_partner(delete_before=True)
        # Delete dirty record and import
        self._test_regression_order(delete_before=True)
        # Try again to reimport order
        self._test_regression_order()
        # Delete dirty record and import
        self._test_regression_ddt(delete_before=True)
        # Try again to reimport order
        self._test_regression_ddt()
        # Delete dirty record and import
        self._test_regression_purchase_order(delete_before=True)
        # Try again to reimport order
        self._test_regression_purchase_order()
        # self.env.cr.commit()
