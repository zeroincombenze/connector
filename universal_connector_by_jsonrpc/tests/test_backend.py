#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
"""Universal connector base tests (jsonrpc-odoorpc)

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

    * Odoo 14.0 with OCA modules; http/xmlrpc port: 8174; DB name: demo14
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

    type,backed,loc.model,ext.model,loc.field,ext.field,ext_id,op,value,group_id
    * type is "=" if line contains data to store or configure
    * type is "?" if line contains data to compare
    * backend value "*" means all backends (only for test to compare)
    * op is "%" if test is <value in field> else is <value == field>
    * group_id = 0, record matches with all Odoo version which have the same value
    * group_id = 1, record matches single value, local ID is unknown
    * group_id = 2, record matches just new records added by push test
    * group_id > 10, record matches with Odoo version which have the same group_id

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
    "universal_connector_base.backend_odoo14": {
        "name": "Test Odoo 14.0",
        "scope_id": "universal_connector_base.scope_test",
        "hostname": "localhost",
        "identity_id": "universal_connector_base.identity_odoo",
        "database": "demo14",
        "remote_sw_version": "14.0",
        "protocol_id": "universal_connector_by_jsonrpc.protocol_jsonrpc",
        "port": 8174,
        "login": "admin",
        "password": "admin",
        "prefix": "odoo14",
        "sequence": 10,
    },
    "universal_connector_base.backend_odoo12": {
        "name": "Test Odoo 12.0",
        "scope_id": "universal_connector_base.scope_test",
        "hostname": "localhost",
        "identity_id": "universal_connector_base.identity_odoo",
        "database": "demo12",
        "remote_sw_version": "12.0",
        "protocol_id": "universal_connector_by_jsonrpc.protocol_jsonrpc",
        "port": 8272,
        "login": "admin",
        "password": "admin",
        "prefix": "odoo12",
        "sequence": 12,
    },
    "universal_connector_base.backend_odoo10": {
        "name": "Test Odoo 10.0",
        "scope_id": "universal_connector_base.scope_test",
        "hostname": "localhost",
        "identity_id": "universal_connector_base.identity_odoo",
        "database": "demo10",
        "remote_sw_version": "10.0",
        "protocol_id": "universal_connector_by_jsonrpc.protocol_jsonrpc",
        "port": 8170,
        "login": "admin",
        "password": "admin",
        "prefix": "odoo10",
        "sequence": 14,
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
        # Internal structure is:
        #  Odoo model to match/test
        #    \_  GRPKEY: group id or value with all data version to compare
        #          \_ backend (xref)
        #               \_ 'EXT_NAME': external table name for backend
        #                  'ext_id' external id
        #                     \_ 'loc_field': field name
        #                        'ext_field': external field name
        #                        'op': match operator
        #                        'value'; value to match
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
                "group_id",
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
                # type,backed,loc.model,ext.model,loc.field,ext.field,op,value,group_id
                values = qsplit(line, ",", quotes='"', escape=True)
                items = dict(zip(keys, values))
                if items["ext_id"]:
                    items["ext_id"] = int(items["ext_id"])
                items["group_id"] = int(
                    items["group_id"]) if items["group_id"] else 0
                if items["value"]:
                    # This code must be run with python 2.7,
                    # so, we cannot use isnumeric() builtin function
                    if (
                            isinstance(items["value"], str)
                            and all([x.isdigit()
                                     for x in items["value"].split(".")])
                    ):
                        items["value"] = eval(items["value"])
                if items["type"] == "=":
                    # Backend assignment
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
                        loc_model = items["loc_model"]
                        if loc_model not in self.test_data:
                            self.test_data[loc_model] = {}
                        key = items["group_id"] or items["value"]
                        if not key:
                            raise ValueError(line)
                        if key not in self.test_data[loc_model]:
                            self.test_data[loc_model][key] = {}
                        if xref not in self.test_data[loc_model][key]:
                            self.test_data[loc_model][key][xref] = {}
                            self.test_data[loc_model][key][xref]["EXT_NAME"] = items[
                                "ext_model"
                            ]
                        ext_id = items["ext_id"]
                        if ext_id not in self.test_data[loc_model][key]:
                            self.test_data[loc_model][key][xref][ext_id] = {}
                        for name in ("loc_field", "ext_field", "op", "value"):
                            self.test_data[loc_model][key][xref][ext_id][name] = (
                                items[name])
                else:
                    raise ValueError(line)
        for xref, backend in TEST_SYNCHRO_BACKEND.copy().items():
            if "active" in backend and not backend["active"]:
                del TEST_SYNCHRO_BACKEND[xref]
                continue
            for loc_model in self.test_data.copy().keys():
                if loc_model not in self.env:
                    del self.test_data[loc_model]

    def get_node_of_model_xref(self, xref, loc_model):
        return [node.get(xref) for node in self.test_data[loc_model].values()][0]

    def get_model_list(self, xref):
        models = []
        for loc_model in self.test_data.keys():
            ext_node = self.get_node_of_model_xref(xref, loc_model)
            if ext_node:
                models.append((loc_model, ext_node["EXT_NAME"], False))
        return models

    def get_ext_model(self, xref, loc_model):
        ext_node = self.get_node_of_model_xref(xref, loc_model)
        return ext_node["EXT_NAME"] if ext_node else None

    def get_field_list(self, xref, loc_model):
        fields = []
        node = self.get_node_of_model_xref(xref, loc_model)
        if node:
            for ext_id in node.keys():
                if ext_id == "EXT_NAME":
                    continue
                fields.append(
                    (node[ext_id]["loc_field"], node[ext_id]["ext_field"], False))
                break
        return fields

    def get_ext_id_list(self, xref, loc_model, group_id=False):
        ext_ids = []
        for key, node in self.test_data[loc_model].items():
            if (
                xref not in node
                or (not group_id and key == 2)
                or (group_id and key != group_id)
            ):
                continue
            for ext_id in node[xref].keys():
                if not ext_id or ext_id == "EXT_NAME":
                    continue
                ext_ids.append(ext_id)
        return sorted(list(set(ext_ids)))

    def get_local_xref(self):
        for node_model in self.test_data.values():
            for node_key in node_model.values():
                for loc_xref in node_key.keys():
                    if loc_xref.endswith(str(self.odoo_major_version)):
                        return loc_xref
        return False

    def get_loc_id(self, xref, loc_model, ext_id):
        loc_xref = self.get_local_xref()
        for ext_key, ext_node in self.test_data[loc_model].items():
            if xref not in ext_node or ext_id not in ext_node[xref]:
                continue
            for loc_key, loc_node in self.test_data[loc_model].items():
                if loc_key != ext_key or loc_xref not in loc_node:
                    continue
                for loc_id in loc_node[loc_xref]:
                    if not loc_id or loc_id == "EXT_NAME":
                        continue
                    return loc_id
        backend = self.resource_browse(xref)
        loc_ext_id = backend.get_loc_ext_id()
        recs = self.env[loc_model].search([(loc_ext_id, "=", ext_id)])
        if recs:
            return recs[0].id
        return False

    def get_test_pattern(self, xref, loc_model, ext_id):
        patterns = []
        for key, node in self.test_data[loc_model].items():
            if isinstance(key, int):
                # No value to match
                continue
            for xxref, node2 in node.items():
                if xxref != xref or ext_id not in node2:
                    continue
                patterns.append((
                    node2[ext_id]["loc_field"],
                    node2[ext_id]["op"],
                    node2[ext_id]["value"],
                ))
        return patterns

    def get_group_id(self, xref, loc_model, ext_id):
        for group_id, node in self.test_data[loc_model].items():
            if xref not in node or ext_id not in node[xref]:
                continue
            return group_id
        return False

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
        self.assertEqual(backend.pylib, "odoorpc")

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
        for loc_model, ext_model, model_spec in self.get_model_list(xref):
            backend_model = self.env["synchro.model"].search(
                [
                    ("name", "=", loc_model),
                    ("counterpart_name", "=", ext_model),
                    ("model_spec", "=", model_spec),
                    ("backend_id", "=", backend.id),
                ]
            )
            self.assertEqual(
                len(backend_model),
                1,
                msg="Model %s not found or oo many matches with %s!"
                    % (loc_model, ext_model)
            )

            for loc_name, ext_name, spec in self.get_field_list(xref, loc_model):
                backend_field = self.env["synchro.mapper"].search(
                    [
                        ("name", "=", loc_name),
                        ("counterpart_name", "=", ext_name),
                        ("spec", "=", spec),
                        ("model_id", "=", backend_model[0].id),
                    ]
                )
                self.assertEqual(
                    len(backend_field),
                    1,
                    msg="Field %s.%s not found or too many matches with %s!"
                        % (loc_model, loc_name, ext_name)
                )

    def _test_import_model(self, xref, loc_model):
        Synchro = self.env["ir.model.synchro"]
        backend = self.resource_browse(xref)
        loc_ext_id = backend.get_loc_ext_id()
        self.assertTrue(loc_ext_id, "%s_id" % backend.prefix)
        for ext_id in self.get_ext_id_list(xref, loc_model):
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
        if self.get_group_id(xref, loc_model, ext_id) != 2:
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
            "🎺 Starting connection test on ports 8170 (db=demo10) and 8272 (db=demo12)"
            " and 8174 (db=demo14) ..."
        )
        for xref in sorted(self.get_resource_data_list("synchro.backend")):
            self._test_check_connection(xref)
            self._test_check_models(xref)
            self._test_import_model(xref, "res.currency")
        for xref in sorted(self.get_resource_data_list("synchro.backend")):
            self._test_reset_connection(xref)
            self._test_check_connection(xref)
            self._test_import_model(xref, "res.country")
            self._test_import_model(xref, "res.partner")
        for xref in sorted(self.get_resource_data_list("synchro.backend")):
            # Now repeat some test in order to check for resync records
            self._test_import_model(xref, "res.currency")
            self._test_import_model(xref, "res.country")
        for xref in sorted(self.get_resource_data_list("synchro.backend")):
            self._test_pull_record(xref, "res.partner")
        for xref in sorted(self.get_resource_data_list("synchro.backend")):
            # 1. res.country.state requires country_id; we want to check for right code
            #    recognition; so, we must test a code which exists in 2+ countries.
            #    We use 'CA' which means California in the USA and Cagliari in Italy
            # 2. We check VAT w/o ISO code to test apply_sanitize_vat()
            # 3. We force default value for name to test apply_set_tmp_name()
            # 4. We force default value for name to test apply_set_default_value()
            backend = self.resource_browse(xref)
            dir_mapper = backend.get_dir_mapper(binding_model="res.partner")
            dir_mapper.get_mapper(loc_name="name").write({"apply4": "set_tmp_name()"})
            dir_mapper.get_mapper(loc_name="ref").write({"default": xref})
            self.env["synchro.mapper"].search([])
            for loc_model, vals in (
                ("ir.module.module", {
                    "name": "base",
                    "id": 13,
                    "state": "installed",
                }),
                ("res.lang", {
                    "code": "it_IT",
                    "id": 17,
                }),
                ("res.currency.rate", {
                    "currency_id": self.env.ref("base.EUR").id,
                    "name": "2025-01-01 01:00:00",
                    "rate": 1.23,
                    "id": 12,
                }),
                ("res.partner", {
                    "is_company": True,
                    "name": "",
                    "country_id": "IT",
                    "state_id": "CA",
                    "vat": "12345670017",
                    "id": 1001,
                }),
            ):
                self._test_push_record(xref, loc_model, vals)
        # self._test_purge()
