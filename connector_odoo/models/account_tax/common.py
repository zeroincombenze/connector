# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models
from odoo.addons.component.core import Component


class OdooAccountTax(models.Model):
    _name = "odoo.account.tax"
    _inherit = "odoo.binding"
    _inherits = {"account.tax": "odoo_id"}
    _description = "Odoo Tax Attribute"


class AccountTax(models.Model):
    _inherit = "account.tax"

    bind_ids = fields.One2many(
        comodel_name="odoo.account.tax",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class AccountTaxAdapter(Component):
    _name = "odoo.account.tax.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.account.tax"

    _odoo_model = "account.tax"
