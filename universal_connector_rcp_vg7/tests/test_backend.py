#
# Copyright 2019-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
"""Universal connector base tests
*Warning*
Universal connector vg7 module connect local Odoo instance with external instance.
Without external running instance, these test CANNOT be executed

**************************************************************************

"""
import logging
from .testenv import MainTest as SingleTransactionCase

_logger = logging.getLogger(__name__)

TEST_SYNCHRO_CHANNEL = {
    "z0bug.localhost-vg7": {
        "name": "VG7 print",
        "identity": "vg7",
        "method": "https",
        "login": False,
        "odoo_version": False,
        "port": 0,
        "hostname": "localhost",
        "counterpart_url": "https://example.com/N/A",
        "exchange_path": "/N/A",
        "data_path": "/N/A",
        "client_key": "N/A",
        "prefix": "vg7",
    },
}
TEST_SETUP_LIST = [
    "synchro.channel",
]

MODEL_MAPPING = [
    ("res.partner", "customers"),
    ("res.country", "countries"),
    ("res.country.state", "regions"),
    ("account.tax", "tax_codes"),
]

FIELD_MAPPING = [
    ("res.partner", "city", "city"),
    # ("res.partner", "name", "name"),
    # ("res.users", "login", "login"),
    # ("res.company", "name", "name"),
]


class MyTest(SingleTransactionCase):

    def setUp(self):
        super().setUp()
        self.debug_level = 0
        self.odoo_commit_data = False
        self.setup_env()
        self.env["ir.model.synchro.cache"].set_loglevel(4)
        # This test can be executed just on real customer db so we cannot use clear
        # password or token. Now we read this data form local file, not published
        backend = self.resource_browse("z0bug.localhost-vg7")
        with open("/home/odoo/.local/test_rcp_vg7.dat") as fd:
            lines = fd.read().split("\n")
            backend.method = lines[1].split(":", 1)[0]
            backend.counterpart_url = lines[1]
            backend.exchange_path = lines[2]
            backend.counterpart_data_url = lines[3]
            backend.data_path = lines[4]
            backend.hostname = lines[5]
            backend.client_key = lines[6]
            backend.loglevel = "4"

    def tearDown(self):
        super().tearDown()

    def _test_check_connection(self, xref):
        backend = self.resource_browse(xref)
        self.resource_edit(
            backend,
            actions="button_check_connection",
        )
        self.assertEqual(backend.state, "checked")

    def _test_reset_connection(self, xref):
        backend = self.resource_browse(xref)
        self.resource_edit(
            backend,
            actions="button_reset_to_draft",
        )
        self.assertEqual(backend.state, "draft")

    def _test_check_models(self, xref):
        backend = self.resource_browse(xref)
        # self.resource_edit(
        #     backend,
        #     actions="button_build_model_map",
        # )
        for model, ext_model in MODEL_MAPPING:
            backend_model = self.env["synchro.channel.model"].search(
                [
                    ("name", "=", model),
                    ("counterpart_name", "=", ext_model),
                    ("synchro_channel_id", "=", backend.id),
                ]
            )
            self.assertEqual(len(backend_model), 1)

            for loc_model, loc_name, ext_name in FIELD_MAPPING:
                if loc_model != model:
                    continue
                backend_field = self.env["synchro.channel.model.fields"].search(
                    [
                        ("name", "=", loc_name),
                        ("counterpart_name", "=", ext_name),
                        ("model_id", "=", backend_model[0].id),
                    ]
                )
                self.assertEqual(len(backend_field), 1)

    def _test_import(self, xref):
        Synchro = self.env["ir.model.synchro"]
        backend = self.resource_browse(xref)
        sts = Synchro.trigger_one_record(MODEL_MAPPING[0][1], backend.prefix, 3)
        self.assertEqual(sts, -127)

    def test_01_connection(self):
        # This test requires external Odoo instance active. See header
        _logger.info("🎺 Starting connection test vg7")
        for xref in sorted(self.get_resource_data_list("synchro.channel")):
            self._test_check_connection(xref)
            self._test_reset_connection(xref)
            self._test_check_connection(xref)
            self._test_check_models(xref)
            self._test_import(xref)
