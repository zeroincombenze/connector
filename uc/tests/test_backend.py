# -*- coding: utf-8 -*-
"""Universal connector tests
*Warning*
Universal connector module connect local Odoo instance with external instance.
Without external running instance, these test CANNOT be executed

In order to run full test on the same host MUST be active follow instance:

* Odoo 10.0 with OCA modules; http/xmlrpc port: 8270; DB name: oca10
* Odoo 12.0 with OCA modules; http/xmlrpc port: 8272; DB name: oca12

"""
import os
import logging
from .testenv import MainTest as SingleTransactionCase

_logger = logging.getLogger(__name__)

TEST_SYNCHRO_BACKEND = {
    "universal_connector.localhost-oca10": {
        "hostname": "localhost",
        "identity_id": "universal_connector.odoo10",
        "database": "oca10",
        "version": "10.0",
        "protocol_id": "universal_connector.jsonrpc",
        "port": 8270,
        "login": "admin",
        "password": "admin"
    },
    "universal_connector.localhost-oca12": {
        "hostname": "localhost",
        "identity_id": "universal_connector.odoo12",
        "database": "oca12",
        "version": "12.0",
        "protocol_id": "universal_connector.jsonrpc",
        "port": 8272,
        "login": "admin",
        "password": "admin"
    },
}
TEST_SETUP_LIST = ["synchro.backend", ]


class MyTest(SingleTransactionCase):

    def setUp(self):
        super().setUp()
        self.debug_level = 3
        data = {"TEST_SETUP_LIST": TEST_SETUP_LIST}
        for resource in TEST_SETUP_LIST:
            item = "TEST_%s" % resource.upper().replace(".", "_")
            data[item] = globals()[item]
        self.declare_all_data(data)
        self.setup_env()

    def tearDown(self):
        super().tearDown()
        if os.environ.get("ODOO_COMMIT_TEST", ""):
            # Save test environment, so it is available to use
            self.env.cr.commit()  # pylint: disable=invalid-commit
            _logger.info("✨ Test data committed")

    def test_component_attrs(self):
        _logger.info(
            "🎺 Starting test w/o connection"
        )
        editing = False
        for xref in self.get_resource_data_list("synchro.backend"):
            backend = self.resource_bind(xref)
            self.assertEqual(backend.state, 'draft')
            if not editing:
                self.resource_edit(
                    backend,
                    web_changes=[("identity_id", backend.identity_id)],
                )
                editing = True
            self.assertEqual(backend.state, 'draft')

    def test_connection(self):
        # This test requires external Odoo instance active. See header
        _logger.info(
            "🎺 Starting connection test"
        )
        for xref in self.get_resource_data_list("synchro.backend"):
            backend = self.resource_bind(xref)
            self.resource_edit(
                backend,
                actions="button_check_connection",
            )
            self.assertEqual(backend.state, 'checked')

            self.resource_edit(
                backend,
                actions="button_reset_to_draft",
            )
            self.assertEqual(backend.state, 'draft')

            backend = self.resource_bind(xref)
            self.resource_edit(
                backend,
                actions="button_check_connection",
            )
            self.assertEqual(backend.state, 'checked')
