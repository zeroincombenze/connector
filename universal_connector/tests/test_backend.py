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
# import os
import logging
from .testenv import MainTest as SingleTransactionCase

_logger = logging.getLogger(__name__)

TEST_SYNCHRO_CHANNEL = {
    "z0bug.localhost-oca10": {
        "name": "Test Odoo 10.0",
        "identity": "odoo",
        "client_key": "oca10",
        "odoo_version": "10.0",
        "method": "JSON",
        "password": "admin",
        "counterpart_url": "admin@localhost:8270",
        "prefix": "oe10",
    },
    "z0bug.localhost-oca12": {
        "name": "odoo12",
        "identity": "odoo",
        "client_key": "oca12",
        "odoo_version": "12.0",
        "method": "JSON",
        "password": "admin",
        "counterpart_url": "admin@localhost:8272",
        "prefix": "oe8",
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

    def test_component_attrs(self):
        _logger.info(
            "🎺 Starting test w/o connection"
        )
        editing = False
        for xref in self.get_resource_data_list("synchro.channel"):
            backend = self.resource_browse(xref)
            self.assertEqual(backend.state, 'draft')
            if not editing:
                self.resource_edit(
                    backend,
                    web_changes=[("identity", backend.identity)],
                )
                editing = True
            self.assertEqual(backend.state, 'draft')

    def test_connection(self):
        # This test requires external Odoo instance active. See header
        _logger.info(
            "🎺 Starting connection test on ports 8270 (db=oca10) and 8272 (db=oca12)"
        )
        for xref in self.get_resource_data_list("synchro.channel"):
            backend = self.resource_browse(xref)
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

            backend = self.resource_browse(xref)
            self.resource_edit(
                backend,
                actions="button_check_connection",
            )
            self.assertEqual(backend.state, 'checked')
