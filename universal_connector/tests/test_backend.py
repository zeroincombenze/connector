#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
"""Universal connector base tests (base)
*Warning*
Universal connector (base) module connect local Odoo instance with external instance.
Without external running instance, these test CANNOT be executed

In order to run full test on the same host MUST be active follow instance:

* Odoo 12.0 with OCA modules; http/xmlrpc port: 8272; DB name: oca12
* Odoo 10.0 with OCA modules; http/xmlrpc port: 8270; DB name: oca10
* Odoo 8.0 with OCA modules; http/xmlrpc port: 8168; DB name: demo8
* Odoo 7.0 with OCA modules; http/xmlrpc port: 8167; DB name: demo7
"""

import os.path as pth
import logging

from python_plus import qsplit, str2bool

from .testenv import MainTest as SingleTransactionCase

_logger = logging.getLogger(__name__)

TEST_SYNCHRO_CHANNEL = {
    "z0bug.localhost-odoo10": {
        "name": "Test Odoo 10.0",
        "hostname": "localhost",
        "identity": "odoo",
        "database": "oca10",
        "odoo_version": "10.0",
        "method": "xmlrpc/http",
        "port": 8270,
        "login": "admin",
        "password": "admin",
        "counterpart_url": "http://admin@localhost:8270/xmlrpc/2/common",
        "counterpart_data_url": "http://admin@localhost:8270/xmlrpc/2/object",
        "prefix": "oe10",
    },
    "z0bug.localhost-odoo12": {
        "name": "Test Odoo 12.0",
        "hostname": "localhost",
        "identity": "odoo",
        "database": "oca12",
        "odoo_version": "12.0",
        "method": "xmlrpc/http",
        "port": 8272,
        "login": "admin",
        "password": "admin",
        "counterpart_url": "http://admin@localhost:8272/xmlrpc/2/common",
        "counterpart_data_url": "http://admin@localhost:8272/xmlrpc/2/object",
        "prefix": "oe12",
    },
    "z0bug.localhost-odoo7": {
        "name": "Test Odoo 7.0",
        "hostname": "localhost",
        "identity": "odoo",
        "database": "demo7",
        "odoo_version": "7.0",
        "method": "xmlrpc/http",
        "port": 8167,
        "login": "admin",
        "password": "admin",
        "lgi_path": "/xmlrpc/common",
        "exchange_path": "/xmlrpc/object",
        "counterpart_url": "http://admin@localhost:8167/xmlrpc/common",
        "counterpart_data_url": "http://admin@localhost:8167/xmlrpc/object",
        "prefix": "oe7",
    },
    "z0bug.localhost-odoo8": {
        "name": "Test Odoo 8.0",
        "hostname": "localhost",
        "identity": "odoo",
        "database": "demo8",
        "odoo_version": "8.0",
        "method": "xmlrpc/http",
        "port": 8168,
        "login": "admin",
        "password": "admin",
        "lgi_path": "/xmlrpc/common",
        "exchange_path": "/xmlrpc/object",
        "counterpart_url": "http://admin@localhost:8168/xmlrpc/common",
        "counterpart_data_url": "http://admin@localhost:8168/xmlrpc/object",
        "prefix": "oe8",
    },
}
TEST_SETUP_LIST = [
    "synchro.channel",
]


class MyTest(SingleTransactionCase):

    def setUp(self):
        super().setUp()
        self.debug_level = 0
        self.odoo_commit_data = False
        self.get_data_test()
        self.setup_env()
        self.env["ir.model.synchro.cache"].set_loglevel(self.debug_level + 1)
        self.env["synchro.channel"].search([]).write(
            {"tracelevel": str(self.debug_level + 1), "deferred_payload": "0"}
        )

    def tearDown(self):
        super().tearDown()

    def get_data_test(self):
        # In order to validate this connector module, we have to load record from
        # another Odoo instances, that are built outside the current environment.
        # So the solution is to create these Odoo instances before this test execution
        # and make available information about counterparties in a text file with data
        # to compare in order to validate current regression tests.
        # If file is not present we suppose the instances with minimal demo data.
        #
        # The condition to validate module are:
        #
        # 1. One or more external Odoo instances must be live
        # 2. Odoo instances have to be created with demo data
        #
        # Odoo instances should be:
        #
        # * Odoo 12.0 with OCA modules; http/xmlrpc port: 8272; DB name: oca12
        # * Odoo 10.0 with OCA modules; http/xmlrpc port: 8270; DB name: oca10
        # * Odoo 8.0 with OCA modules; http/xmlrpc port: 8168; DB name: demo8
        # * Odoo 7.0 with OCA modules; http/xmlrpc port: 8167; DB name: demo7
        #
        # Data to test, locally defined by python or based on text file must be
        # formatted as follows:
        #
        # type,backed,loc.model,ext.model,loc.field,ext.field,ext_id,op,value
        #       type is "=" if record contains data to store or configure
        #       type is "?" if record contains data to compare
        #       backend may "*" for all backends (only for test to compare)
        #       op is "%" if test is <value in field> else is <value == field>
        #
        # This test could be executed just on real customer db so we cannot use clear
        # password or token in data set/configure. In these case is mandatory
        # to read this data from local file, not published.
        # Text file name is "/home/odoo/.local/<CURRENT_MODULE_NAME>.dat")
        #
        # Warning: synchronization backends must be declared on global variables
        # TEST_SYNCHRO_CHANNEL and TEST_SETUP_LIST (read testenv documentation)
        # This function must be executed before setup_env()
        #
        self.test_data = {}
        data_fqn = pth.join("/home/odoo/.local", self.module.name + ".dat")
        if not pth.isfile(data_fqn):
            data_fqn = pth.join(
                pth.dirname(__file__), "data", self.module.name + ".dat"
            )
        if not pth.isfile(data_fqn):
            raise IOError(data_fqn)
        with open(data_fqn, "r") as fd:
            keys = [
                "type",
                "backend",
                "loc_model",
                "ext_model",
                "loc_field",
                "ext_field",
                "ext_id",
                "op",
                "value",
                "no_local",
            ]
            for line in fd.read().split("\n"):
                # Remove comments
                if line.startswith("#"):
                    line = ""
                else:
                    line = line.split(" #", 1)[0].strip()
                if not line:
                    continue
                #
                # type,backed,loc.model,ext.model,loc.field,ext.field,op,value
                values = qsplit(line, ",", quotes='"', escape=True)
                items = dict(zip(keys, values))
                if items["ext_id"]:
                    items["ext_id"] = int(items["ext_id"])
                items["no_local"] = str2bool(items["no_local"], False)
                if items["type"] == "=":
                    if items["backend"] not in TEST_SYNCHRO_CHANNEL:
                        raise ValueError(items["backend"])
                    TEST_SYNCHRO_CHANNEL[items["backend"]][items["loc_field"]] = items[
                        "value"
                    ]
                elif items["type"] == "?":
                    for xref in (
                        TEST_SYNCHRO_CHANNEL.keys()
                        if items["backend"] == "*"
                        else [items["backend"]]
                    ):
                        if xref not in self.test_data:
                            self.test_data[xref] = {}
                        loc_model = items["loc_model"]
                        if loc_model not in self.test_data[xref]:
                            self.test_data[xref][loc_model] = {}
                            self.test_data[xref][loc_model]["EXT_NAME"] = items[
                                "ext_model"
                            ]
                        loc_field = items["loc_field"]
                        if not loc_field:
                            continue
                        if loc_field not in self.test_data[xref][loc_model]:
                            self.test_data[xref][loc_model][loc_field] = {}
                            self.test_data[xref][loc_model][loc_field]["EXT_NAME"] = (
                                items["ext_field"]
                            )
                        if items["value"]:
                            self.test_data[xref][loc_model][loc_field][
                                items["ext_id"]
                            ] = (items["op"], items["value"], items["no_local"])
                else:
                    raise ValueError(items["type"])
        for xref, backend in TEST_SYNCHRO_CHANNEL.items():
            if "active" in backend and not backend["active"]:
                del TEST_SYNCHRO_CHANNEL[xref]

    def get_model_list(self, xref):
        models = []
        for loc_model in self.test_data[xref].keys():
            models.append((loc_model, self.test_data[xref][loc_model]["EXT_NAME"]))
        return models

    def get_field_list(self, xref, loc_model):
        fields = []
        for loc_name in self.test_data[xref][loc_model].keys():
            if loc_name == "EXT_NAME":
                continue
            fields.append(
                (loc_name, self.test_data[xref][loc_model][loc_name]["EXT_NAME"])
            )
        return fields

    def get_ext_id_list(self, xref, loc_model):
        ext_ids = []
        for loc_name in self.test_data[xref][loc_model].keys():
            if loc_name == "EXT_NAME":
                continue
            for ext_id in self.test_data[xref][loc_model][loc_name].keys():
                if ext_id == "EXT_NAME":
                    continue
                if ext_id and ext_id not in ext_ids:
                    ext_ids.append(ext_id)
        return ext_ids

    def get_loc_id(self, xref, loc_model, ext_id):
        value = ""
        loc_id = False
        for loc_name in self.test_data[xref][loc_model].keys():
            if loc_name == "EXT_NAME":
                continue
            if ext_id in self.test_data[xref][loc_model][loc_name]:
                value = self.test_data[xref][loc_model][loc_name][ext_id][1]
                break
        if not value:
            raise ValueError("%s.%s.%s" % (xref, loc_model, ext_id))
        found = False
        for xxref in self.test_data.keys():
            if xxref.endswith(str(self.odoo_major_version)):
                found = True
                break
        if found:
            for loc_name in self.test_data[xxref][loc_model].keys():
                if loc_name == "EXT_NAME":
                    continue
                for xext_id in self.test_data[xxref][loc_model][loc_name].keys():
                    if (
                        self.test_data[xxref][loc_model][loc_name][xext_id][1] == value
                        and not self.test_data[xxref][loc_model][loc_name][xext_id][2]
                    ):
                        loc_id = xext_id
                        break
        return loc_id

    def get_test_pattern(self, xref, loc_model, ext_id):
        patterns = []
        for loc_name in self.test_data[xref][loc_model].keys():
            if loc_name == "EXT_NAME":
                continue
            if ext_id in self.test_data[xref][loc_model][loc_name]:
                patterns.append(
                    (
                        loc_name,
                        self.test_data[xref][loc_model][loc_name][ext_id][0],
                        self.test_data[xref][loc_model][loc_name][ext_id][1],
                    )
                )
        return patterns

    def get_ext_model(self, xref, model):
        return self.test_data[xref][model]["EXT_NAME"]

    def is_no_local(self, xref, loc_model, ext_id):
        no_local = False
        for loc_name in self.test_data[xref][loc_model].keys():
            if loc_name == "EXT_NAME":
                continue
            if ext_id in self.test_data[xref][loc_model][loc_name]:
                no_local = self.test_data[xref][loc_model][loc_name][ext_id][2]
                break
        return no_local

    def _test_check_connection(self, xref):
        backend = self.resource_browse(xref)
        self.resource_edit(
            backend,
            actions="button_check_connection",
        )
        self.assertEqual(backend.state, "ready")
        self.assertEqual(backend.pypi_sign, "xmlrpc")

    def _test_reset_connection(self, xref):
        backend = self.resource_browse(xref)
        self.resource_edit(
            backend,
            actions="button_reset_to_draft",
        )
        self.assertEqual(backend.state, "draft")

    def _test_check_models(self, xref):
        backend = self.resource_browse(xref)
        self.resource_edit(
            backend,
            actions="button_build_model_map",
        )
        for model, ext_model in self.get_model_list(xref):
            backend_model = self.env["synchro.channel.model"].search(
                [
                    ("name", "=", model),
                    ("counterpart_name", "=", ext_model),
                    ("synchro_channel_id", "=", backend.id),
                ]
            )
            self.assertEqual(
                len(backend_model), 1, msg="Too many ext model %s" % ext_model
            )

            for loc_name, ext_name in self.get_field_list(xref, model):
                backend_field = self.env["synchro.channel.model.field"].search(
                    [
                        ("name", "=", loc_name),
                        ("counterpart_name", "=", ext_name),
                        ("model_id", "=", backend_model[0].id),
                    ]
                )
                self.assertEqual(
                    len(backend_field),
                    1,
                    msg="Too many field for %s.%s" % (ext_model, ext_name),
                )

    def _test_import_model(self, xref, loc_model):
        Synchro = self.env["ir.model.synchro"]
        backend = self.resource_browse(xref)
        loc_ext_id = "%s_id" % backend.prefix
        for ext_id in self.get_ext_id_list(xref, loc_model):
            ext_model = self.get_ext_model(xref, loc_model)
            loc_id = self.get_loc_id(xref, loc_model, ext_id)
            rec_id = Synchro.trigger_one_record(ext_model, backend.prefix, ext_id)
            if loc_id:
                self.assertEqual(rec_id, loc_id, msg="Unexpected local record ID")
            record = self.env[loc_model].browse(rec_id)
            self.assertEqual(
                getattr(record, loc_ext_id), ext_id, msg="Synchronization failed"
            )
            for loc_field, op, value in self.get_test_pattern(xref, loc_model, ext_id):
                if op == "%":
                    self.assertIn(
                        value,
                        getattr(record, loc_field),
                        msg="Unexpected value %s for %s.%s"
                        % (getattr(record, loc_field), loc_model, loc_field),
                    )
                else:
                    self.assertEqual(
                        getattr(record, loc_field),
                        value,
                        msg="Unexpected value %s for %s.%s"
                        % (getattr(record, loc_field), loc_model, loc_field),
                    )

    def _test_import_partner(self, xref):
        Synchro = self.env["ir.model.synchro"]
        backend = self.resource_browse(xref)
        loc_ext_id = "%s_id" % backend.prefix
        loc_model = "res.partner"

        if (
            self.odoo_major_version < 12
            and int(backend.odoo_version.split(".")[0]) < 12
        ) or (
            self.odoo_major_version >= 12
            and int(backend.odoo_version.split(".")[0]) >= 12
        ):
            for ext_id in self.get_ext_id_list(xref, loc_model):
                # This test load counterart record with local record which must be
                # present in DB. If ext_if has no_local attribute means this test
                # is to skip
                if self.is_no_local(xref, loc_model, ext_id):
                    continue
                ext_model = self.get_ext_model(xref, loc_model)
                loc_id = self.get_loc_id(xref, loc_model, ext_id)
                rec_id = Synchro.trigger_one_record(ext_model, backend.prefix, ext_id)
                if loc_id:
                    self.assertEqual(rec_id, loc_id, msg="Unexpected local record ID")
                partner = self.env[loc_model].browse(rec_id)
                self.assertEqual(
                    getattr(partner, loc_ext_id), ext_id, msg="Synchronization failed"
                )
                for loc_field, op, value in self.get_test_pattern(
                    xref, loc_model, ext_id
                ):
                    if op == "%":
                        self.assertIn(
                            value,
                            getattr(partner, loc_field),
                            msg="Unexpected value %s for %s.%s"
                            % (getattr(partner, loc_field), loc_model, loc_field),
                        )
                    else:
                        self.assertEqual(
                            getattr(partner, loc_field),
                            value,
                            msg="Unexpected value %s for %s.%s"
                            % (getattr(partner, loc_field), loc_model, loc_field),
                        )

    def _test_import_partner2(self, xref):
        Synchro = self.env["ir.model.synchro"]
        backend = self.resource_browse(xref)
        loc_ext_id = "%s_id" % backend.prefix
        loc_model = "res.partner"

        if (
            self.odoo_major_version >= 12
            and int(backend.odoo_version.split(".")[0]) < 12
        ) or (
            self.odoo_major_version < 12
            and int(backend.odoo_version.split(".")[0]) >= 12
        ):
            for ext_id in self.get_ext_id_list(xref, loc_model):
                # This test load counterpart record with local record which must be
                # present in DB. If ext_if has no_local attribute means this test
                # is to skip
                if self.is_no_local(xref, loc_model, ext_id):
                    continue
                ext_model = self.get_ext_model(xref, loc_model)
                loc_id = self.get_loc_id(xref, loc_model, ext_id)
                # Already synchronized
                partner = self.env[loc_model].browse(loc_id)
                partner.write({"%s_id" % backend.prefix: ext_id})
                rec_id = Synchro.trigger_one_record(ext_model, backend.prefix, ext_id)
                self.assertEqual(rec_id, loc_id, msg="Unexpected local record ID")
                partner = self.env[loc_model].browse(rec_id)
                self.assertEqual(
                    getattr(partner, loc_ext_id), ext_id, msg="Synchronization failed"
                )
                for loc_field, op, value in self.get_test_pattern(
                    xref, loc_model, ext_id
                ):
                    if op == "%":
                        self.assertIn(
                            value,
                            getattr(partner, loc_field),
                            msg="Unexpected value %s for %s.%s"
                            % (getattr(partner, loc_field), loc_model, loc_field),
                        )
                    else:
                        self.assertEqual(
                            getattr(partner, loc_field),
                            value,
                            msg="Unexpected value %s for %s.%s"
                            % (getattr(partner, loc_field), loc_model, loc_field),
                        )

        for ext_id in self.get_ext_id_list(xref, loc_model):
            ext_model = self.get_ext_model(xref, loc_model)
            loc_id = self.get_loc_id(xref, loc_model, ext_id)
            rec_id = Synchro.trigger_one_record(ext_model, backend.prefix, ext_id)
            if loc_id:
                self.assertEqual(rec_id, loc_id, msg="Unexpected local record ID")
            partner = self.env[loc_model].browse(rec_id)
            self.assertEqual(
                getattr(partner, loc_ext_id), ext_id, msg="Synchronization failed"
            )
            for loc_field, op, value in self.get_test_pattern(xref, loc_model, ext_id):
                if op == "%":
                    self.assertIn(
                        value,
                        getattr(partner, loc_field),
                        msg="Unexpected value %s for %s.%s"
                        % (getattr(partner, loc_field), loc_model, loc_field),
                    )
                else:
                    self.assertEqual(
                        getattr(partner, loc_field),
                        value,
                        msg="Unexpected value %s for %s.%s"
                        % (getattr(partner, loc_field), loc_model, loc_field),
                    )

    def _test_country_state_ca(self, xref):
        # res.country.state requires country_id; in order to check this configuration
        # we have to test a record which can exist in 2+ countries. We use 'CA' used in
        # "Delta PC" partner; "CA" means California in the USA and Cagliari in Italy
        loc_modeL = "res.country.state"
        backend = self.resource_browse(xref)
        loc_ext_id = "%s_id" % backend.prefix
        recs = self.env[loc_modeL].search([("code", "=", "CA")])
        for record in recs:
            ext_id = getattr(record, loc_ext_id)
            if record.country_id.code == "US":
                self.assertGreater(ext_id, 0, msg="No US country synchronized")
            else:
                self.assertEqual(ext_id, False, msg="Wrong country synchronization")

    def _test_pull_record(self, xref, loc_model):
        for ext_id in self.get_ext_id_list(xref, loc_model):
            # This test run pull_record function of existent and synchronized record.
            # If ext_if has no_local attribute we cannot find record to pull
            if self.is_no_local(xref, loc_model, ext_id):
                continue
            loc_id = self.get_loc_id(xref, loc_model, ext_id)
            record = self.env[loc_model].browse(loc_id)
            do_test = False
            for loc_field, op, value in self.get_test_pattern(xref, loc_model, ext_id):
                if loc_field == "name":
                    record.write({"name": "wrong"})
                    do_test = True
                    break
            if do_test:
                self.resource_edit(
                    record,
                    actions="pull_record",
                )
                record = self.env[loc_model].browse(loc_id)
                for loc_field, op, value in self.get_test_pattern(
                    xref, loc_model, ext_id
                ):
                    if op == "%":
                        self.assertIn(
                            value,
                            getattr(record, loc_field),
                            msg="Unexpected value %s for %s.%s"
                            % (getattr(record, loc_field), loc_model, loc_field),
                        )
                    else:
                        self.assertEqual(
                            getattr(record, loc_field),
                            value,
                            msg="Unexpected value %s for %s.%s"
                            % (getattr(record, loc_field), loc_model, loc_field),
                        )

    def _test_03_purge(self):
        _logger.info("🎺 Starting purge log test")
        self.env["ir.model.synchro.log"].purge_log()

    def test_connection(self):
        # This test requires external Odoo instance active. See header
        _logger.info(
            "🎺 Starting connection test on ports 8270 (db=oca10) and 8272 (db=oca12)"
            " and on ports 8167 (db=demo7) and 8168 (db=demo8)"
        )
        for xref in sorted(self.get_resource_data_list("synchro.channel")):
            self._test_check_connection(xref)
            self._test_reset_connection(xref)
            self._test_check_connection(xref)
            self._test_check_models(xref)
            self._test_import_model(xref, "res.currency")
        for xref in sorted(self.get_resource_data_list("synchro.channel")):
            self._test_import_model(xref, "res.country")
            self._test_import_partner(xref)
        for xref in sorted(self.get_resource_data_list("synchro.channel")):
            self._test_import_partner2(xref)
            # Now repeat some test in order to check for resync records
            self._test_import_model(xref, "res.currency")
            self._test_import_model(xref, "res.country")
            self._test_import_model(xref, "res.partner")
        for xref in sorted(self.get_resource_data_list("synchro.channel")):
            # self._test_country_state_ca(xref)
            self._test_pull_record(xref, "res.partner")
        self._test_03_purge()
