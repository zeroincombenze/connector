import os
import logging
from .testenv import MainTest as SingleTransactionCase

_logger = logging.getLogger(__name__)


class TestImport(SingleTransactionCase):

    def setUp(self):
        super().setUp()
        self.debug_level = 0
        self.setup_env(setup_list=[])
        # Force the load of the hook to test coverage
        self.env["ir.fields.converter"]._register_hook()

    def tearDown(self):
        super().tearDown()

    def wizard_import(self, res_model, file_name, fields):
        xlsx_file_path = os.path.join(self.data_dir, file_name)
        with open(xlsx_file_path, "rb") as fd:
            record = self.env["base_import.import"].create({
                "res_model": res_model,
                "file": fd.read(),
                "file_name": os.path.basename(file_name),
                "file_type":
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            })
        record.do(fields, [], {"headers": True,  "quoting": '"', "separator": ","})

    def test_01_update_phone(self):
        partner = self.env.ref("base.res_partner_10")
        # Check for no other modules had update original phone
        self.assertNotEqual(partner.phone, "0039 011 555555")
        # Now import Excel file
        self.wizard_import("res.partner",
                           "test_update_phone.xlsx",
                           ["name", "comment", "phone"])
        partner = self.env.ref("base.res_partner_10")
        self.assertEqual(partner.phone, "0039 011 555555")

    def test_02_by_xref(self):
        partner = self.env.ref("base.res_partner_10")
        # Check for no other modules had update original phone
        self.assertNotEqual(partner.website, "https://www.jackson.com")
        # Now import Excel file
        self.wizard_import("res.partner",
                           "test_by_xref.xlsx",
                           ["id", "name", "comment", "website"])
        partner = self.env.ref("base.res_partner_10")
        self.assertEqual(partner.website, "https://www.jackson.com")

    def test_03_country(self):
        partner = self.env.ref("base.res_partner_10")
        # Delete country
        partner.write({"country_id": False})
        self.assertNotEqual(partner.state_id, self.env.ref("base.us"))
        # Now import Excel file
        self.wizard_import("res.partner",
                           "test_country.xlsx",
                           ["id", "name", "comment", "country_id"])
        partner = self.env.ref("base.res_partner_10")
        self.assertEqual(partner.country_id, self.env.ref("base.us"))

    def test_04_country_state(self):
        partner = self.env.ref("base.res_partner_10")
        # Delete country state
        partner.write({"state_id": False})
        self.assertNotEqual(partner.state_id, self.env.ref("base.state_us_1"))
        # Now import Excel file
        self.wizard_import("res.partner",
                           "test_country_state.xlsx",
                           ["id", "name", "comment", "country_id", "state_id"])
        partner = self.env.ref("base.res_partner_10")
        self.assertEqual(partner.state_id, self.env.ref("base.state_us_1"))

    def _test_05_state(self):
        partner = self.env.ref("base.res_partner_10")
        # Delete country state
        partner.write({"state_id": False})
        self.assertNotEqual(partner.state_id, self.env.ref("base.state_us_1"))
        # Now import Excel file
        self.wizard_import("res.partner",
                           "test_country_state.xlsx",
                           ["id", "name", "comment", "state_id"])
        partner = self.env.ref("base.res_partner_10")
        self.assertEqual(partner.state_id, self.env.ref("base.state_us_1"))
