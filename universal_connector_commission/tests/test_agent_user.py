# -*- coding: utf-8 -*-
#
# Copyright 2026 Zeroincombenze srls <https://www.zeroincombenze.it>
#
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
"""Test apply_agent_user(): VG7 agent_id -> partner (vg73_id) -> sale.order user_id

These tests do not require any external instance.
"""
from odoo.tests.common import TransactionCase

EXT_REF = "vg7:agent_id"


class TestAgentUser(TransactionCase):

    def setUp(self):
        super(TestAgentUser, self).setUp()
        self.apply = self.env["ir.model.synchro.apply"]
        self.agent_partner = self.env["res.partner"].create({
            "name": "Test Agent With User",
            "vg73_id": 9016,
        })
        self.agent_user = self.env["res.users"].create({
            "name": "Test Agent With User",
            "login": "test_agent_user_9016",
            "partner_id": self.agent_partner.id,
        })
        self.agent_no_user = self.env["res.partner"].create({
            "name": "Test Agent Without User",
            "vg73_id": 9017,
        })

    def run_apply(self, vals):
        return self.apply.apply_agent_user(
            None, vals, "user_id", EXT_REF, "vg7_id", "sale.order")

    def test_agent_with_user(self):
        vals = self.run_apply({EXT_REF: 9016})
        self.assertEqual(vals.get("user_id"), self.agent_user.id)
        self.assertNotIn(EXT_REF, vals)

    def test_agent_id_as_string(self):
        vals = self.run_apply({EXT_REF: "9016"})
        self.assertEqual(vals.get("user_id"), self.agent_user.id)

    def test_agent_without_user(self):
        vals = self.run_apply({EXT_REF: 9017})
        self.assertNotIn("user_id", vals)
        self.assertNotIn(EXT_REF, vals)

    def test_agent_not_found(self):
        vals = self.run_apply({EXT_REF: 9099})
        self.assertNotIn("user_id", vals)
        self.assertNotIn(EXT_REF, vals)

    def test_agent_id_zero(self):
        for value in (0, "0", False, None, ""):
            vals = self.run_apply({EXT_REF: value})
            self.assertNotIn("user_id", vals)
            self.assertNotIn(EXT_REF, vals)

    def test_agent_id_missing(self):
        vals = self.run_apply({"name": "SO001"})
        self.assertEqual(vals, {"name": "SO001"})

    def test_user_id_already_set(self):
        vals = self.run_apply({EXT_REF: 9016, "user_id": self.env.uid})
        self.assertEqual(vals["user_id"], self.env.uid)
        self.assertNotIn(EXT_REF, vals)

    def test_salesman_with_customer(self):
        """Customer given: salesman set"""
        customer = self.env["res.partner"].create({"name": "Test Customer"})
        vals = self.run_apply({EXT_REF: 9016, "partner_id": customer.id})
        self.assertEqual(vals.get("user_id"), self.agent_user.id)
        self.assertEqual(vals["partner_id"], customer.id)


class TestAgentCustomer(TransactionCase):
    """Agent assigned to order customer"""

    def setUp(self):
        super(TestAgentCustomer, self).setUp()
        self.apply = self.env["ir.model.synchro.apply"]
        self.agent = self.env["res.partner"].create({
            "name": "Test Agent",
            "vg73_id": 9016,
            "agent": True,
        })
        self.other_agent = self.env["res.partner"].create({
            "name": "Test Other Agent",
            "agent": True,
        })

    def run_apply(self, vals):
        return self.apply.apply_agent_user(
            None, vals, "user_id", EXT_REF, "vg7_id", "sale.order")

    def test_customer_without_agent(self):
        customer = self.env["res.partner"].create({"name": "Test Customer"})
        self.run_apply({EXT_REF: 9016, "partner_id": customer.id})
        self.assertEqual(customer.agents, self.agent)

    def test_customer_with_agent(self):
        customer = self.env["res.partner"].create({
            "name": "Test Customer",
            "agents": [(6, 0, [self.other_agent.id])],
        })
        self.run_apply({EXT_REF: 9016, "partner_id": customer.id})
        self.assertEqual(customer.agents, self.other_agent)

    def test_agent_not_found(self):
        customer = self.env["res.partner"].create({"name": "Test Customer"})
        self.run_apply({EXT_REF: 9099, "partner_id": customer.id})
        self.assertFalse(customer.agents)

    def test_agent_id_zero(self):
        customer = self.env["res.partner"].create({"name": "Test Customer"})
        self.run_apply({EXT_REF: 0, "partner_id": customer.id})
        self.assertFalse(customer.agents)

    def test_no_customer(self):
        vals = self.run_apply({EXT_REF: 9016})
        self.assertNotIn("partner_id", vals)
