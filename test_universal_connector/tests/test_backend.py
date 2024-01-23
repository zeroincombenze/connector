# -*- coding: utf-8 -*-
# import unittest
# import odoo
# from odoo import api
from odoo.tests import common


class TransactionComponentCase(common.TransactionCase):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.env.cr.commit()  # pylint: disable=invalid-commit

    def test_component_attrs(self):
        """ Basic access to a Component's attribute """
        for backend in (self.env['synchro.backend']).search([]):
            self.assertEqual(backend.state, 'draft')
            backend._check_connection()
            self.assertEqual(backend.state, 'checked')
