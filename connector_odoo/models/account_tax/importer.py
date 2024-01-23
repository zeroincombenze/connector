# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component

# from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class AccountTaxBatchImporter(Component):
    """Import Odoo Tax"""

    _name = "odoo.account.tax.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = "odoo.account.tax"


class AccountTaxImportMapper(Component):
    _name = "odoo.account.tax.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.account.tax"

    direct = [("description", "description"), ("name", "name")]
