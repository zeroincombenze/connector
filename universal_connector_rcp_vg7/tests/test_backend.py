#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
"""Universal connector base tests (vg7)

In order to validate this connector module, we have to load record from another Odoo
instances, that were built outside the current environment.
So the solution is to create these Odoo instances before current test execution.
We stored information about counterparties in a text file with data to compare, and
we can validate test results against data in this text file found in
"<MODULE/TO/TEST/PATH>/tests/data/<CURRENT_MODULE_NAME>.dat"

The conditions to validate module are:

    1. One or more external Odoo instances must be live
    2. Odoo instances had to be created with demo data, english, no country
    3. External software instance must be live, for specific tests

Tests are designed to run in the same way with all connector modules but every
connector module could connect just with some specific instances.

Odoo instances to match full connector tests, should be:

    * Odoo 12.0 with OCA modules; http/xmlrpc port: 8272; DB name: demo12
    * Odoo 10.0 with OCA modules; http/xmlrpc port: 8170; DB name: demo10
    * Odoo 8.0 with OCA modules; http/xmlrpc port: 8168; DB name: demo8
    * Odoo 7.0 with OCA modules; http/xmlrpc port: 8167; DB name: demo7
    * External software instance; currently only VG7 is supported

When text is executed on external software or on real customer db, we cannot use clear
password or token stored in published configuration file. In these case is mandatory
to read this data from a local file, not published which can be found in
"/home/odoo/.local/<CURRENT_MODULE_NAME>.dat"

Data to test, declared in local text file, must be formatted as follows:

    type,backed,loc.model,ext.model,loc.field,ext.field,ext_id,op,value
    * type is "=" if record contains data to store or configure
    * type is "?" if record contains data to compare
    * backend may "*" for all backends (only for test to compare)
    * op is "%" if test is <value in field> else is <value == field>

This test is based on zeroincombenze(R) test flow (read testenv documentation), which
declares backends in global variables TEST_SYNCHRO_BACKEND and TEST_SETUP_LIST.
Tests are tha same for all Odoo version. Backend with current Odoo version cannot be
tested because it is not useful and Odoo tests are executed before installation
is completed.
"""

import os.path as pth
import logging

from python_plus import qsplit

from .testenv import MainTest as SingleTransactionCase

_logger = logging.getLogger(__name__)

TEST_SYNCHRO_BACKEND = {
    "universal_connector_rcp_vg7.backend_vg7": {
        "name": "VG7 print",
        "identity_id": "universal_connector_rcp_vg7.identity_vg7",
        "remote_sw_version": "2.0",
        "protocol_id": "universal_connector_by_http.protocol_http",
        "counterpart_url": "https://example.com/N/A",
        "lgi_path": "/N/A",
        "exchange_path": "/N/A",
        "prefix": "vg7",
        "sequence": 10,
    },
}
TEST_SETUP_LIST = [
    "synchro.backend",
]


class MyTest(SingleTransactionCase):

    def setUp(self):
        super().setUp()
        self.debug_level = 0
        self.odoo_commit_data = False
        self.get_data_test()
        self.setup_env()
        self.env["synchro.cache"].set_loglevel(self.debug_level + 1)
        self.env["synchro.backend"].search([]).write(
            {"tracelevel": str(self.debug_level + 1), "deferred_payload": "0"}
        )

    def tearDown(self):
        super().tearDown()

    def get_data_test(self):
        # This function must be executed before setup_env()
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
                items["no_local"] = int(items["no_local"]) if items["no_local"] else 0
                if items["type"] == "=":
                    if items["backend"] not in TEST_SYNCHRO_BACKEND:
                        raise ValueError(items["backend"])
                    TEST_SYNCHRO_BACKEND[items["backend"]][items["loc_field"]] = items[
                        "value"
                    ]
                elif items["type"] == "?":
                    for xref in (
                        TEST_SYNCHRO_BACKEND.keys()
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
                            # This code must be run with python 2.7,
                            # so, we cannot use isnumeric() builtin function
                            if (
                                    isinstance(items["value"], str)
                                    and all([x.isdigit()
                                             for x in items["value"].split(".")])
                            ):
                                items["value"] = eval(items["value"])
                            self.test_data[xref][loc_model][loc_field][
                                items["ext_id"]
                            ] = (items["op"], items["value"], items["no_local"])
                else:
                    raise ValueError(items["type"])
        for xref, backend in TEST_SYNCHRO_BACKEND.items():
            if "active" in backend and not backend["active"]:
                del TEST_SYNCHRO_BACKEND[xref]

    def get_model_list(self, xref):
        models = []
        for loc_model in self.test_data[xref].keys():
            models.append(
                (loc_model, self.test_data[xref][loc_model]["EXT_NAME"], False)
            )
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

    def validate_result(self, xref, record, loc_model, loc_field, ext_id, op, value):
        res = getattr(record, loc_field)
        if op == "is" and value == "True":
            self.assertTrue(
                res,
                msg="Unexpected value %s for %s.%s (ext_id %s of %s)"
                    % (getattr(record, loc_field),
                       loc_model, loc_field, ext_id, xref),
            )
        elif op == "is" and value == "False":
            self.assertFalse(
                res,
                msg="Unexpected value %s for %s.%s (ext_id %s of %s)"
                    % (getattr(record, loc_field),
                       loc_model, loc_field, ext_id, xref),
            )
        elif op == "%":
            self.assertIn(
                value,
                res,
                msg="Unexpected value %s for %s.%s (ext_id %s of %s)"
                    % (getattr(record, loc_field),
                       loc_model, loc_field, ext_id, xref),
            )
        else:
            self.assertEqual(
                res.id if hasattr(res, "id") else res,
                value,
                msg="Unexpected value %s for %s.%s (ext_id %s of %s)"
                    % (getattr(record, loc_field),
                       loc_model, loc_field, ext_id, xref),
            )

    def _test_check_connection(self, xref):
        backend = self.resource_browse(xref)
        self.resource_edit(
            backend,
            actions="button_check_connection",
        )
        self.assertEqual(backend.state, "ready")
        self.assertEqual(backend.pylib, "requests")

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
        for model, ext_model, model_spec in self.get_model_list(xref):
            backend_model = self.env["synchro.model"].search(
                [
                    ("name", "=", model),
                    ("counterpart_name", "=", ext_model),
                    ("model_spec", "=", model_spec),
                    ("backend_id", "=", backend.id),
                ]
            )
            self.assertEqual(
                len(backend_model), 1, msg="Too many ext model %s" % ext_model
            )

            for loc_name, ext_name in self.get_field_list(xref, model):
                backend_field = self.env["synchro.mapper"].search(
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
            if self.is_no_local(xref, loc_model, ext_id) == 2:
                continue
            ext_model = self.get_ext_model(xref, loc_model)
            loc_id = self.get_loc_id(xref, loc_model, ext_id)
            rec_id = Synchro.trigger_one_record(ext_model, backend.prefix, ext_id)
            if loc_id:
                self.assertEqual(rec_id, loc_id, msg="Unexpected local record ID")
            record = self.env[loc_model].browse(rec_id)
            self.assertEqual(
                getattr(record, loc_ext_id),
                ext_id,
                msg="Model %s: unexpected value %s (%s)"
                    % (loc_model, getattr(record, loc_ext_id), ext_id),
            )
            for loc_field, op, value in self.get_test_pattern(xref, loc_model, ext_id):
                self.validate_result(
                    xref, record, loc_model, loc_field, ext_id, op, value)

    def _test_pull_record(self, xref, loc_model):
        for ext_id in self.get_ext_id_list(xref, loc_model):
            # This test run pull_record function of existent and synchronized record.
            # If ext_if has no_local attribute we cannot find record to pull
            if self.is_no_local(xref, loc_model, ext_id):
                continue
            loc_id = self.get_loc_id(xref, loc_model, ext_id)
            self.assertTrue(
                loc_id,
                msg="No external record %s for model %s" % (ext_id, loc_model),
            )
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
                    self.validate_result(
                        xref, record, loc_model, loc_field, ext_id, op, value)

    def _test_push_record(self, xref, loc_model, vals):
        ext_id = vals["id"]
        # This test run push_record function in order to test magic record which
        # do not exist in local DB
        if self.is_no_local(xref, loc_model, ext_id) != 2:
            raise IOError("Invalid external id %s for model %s" % (ext_id, loc_model))
        backend = self.resource_browse(xref)
        loc_id = self.env["ir.model.synchro"].push_record(
            loc_model, backend.prefix, vals)
        self.assertTrue(
            loc_id,
            msg="No external record %s for model %s" % (ext_id, loc_model),
        )
        record = self.env[loc_model].browse(loc_id)
        for loc_field, op, value in self.get_test_pattern(
            xref, loc_model, ext_id
        ):
            self.validate_result(xref, record, loc_model, loc_field, ext_id, op, value)

    def _test_purge(self):
        _logger.info("🎺 Starting purge log test ...")
        self.env["synchro.log"].purge_log()

    def test_connection(self):
        # This test requires external Odoo instance active. See header
        _logger.info(
            "🎺 Starting connection test VG7"
        )
        for xref in sorted(self.get_resource_data_list("synchro.backend")):
            self._test_check_connection(xref)
            self._test_reset_connection(xref)
            self._test_check_connection(xref)
            self._test_check_models(xref)
            self._test_import_model(xref, "res.partner")
        for xref in sorted(self.get_resource_data_list("synchro.backend")):
            self._test_pull_record(xref, "res.partner")
