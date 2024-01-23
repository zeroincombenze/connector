#
# Copyright 2019-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import models, api
from odoo.addons.component.core import AbstractComponent


class BaseModelExtend(models.AbstractModel):
    """
    Additional models for all Odoo classes
    """
    _inherit = 'base'

    @api.model
    def select_odoo_version(self):
        return [
            ("6.1", "Odoo 6.1"),
            ("7.0", "Odoo 7.0"),
            ("8.0", "Odoo 8.0"),
            ("9.0", "Odoo 9.0"),
            ("10.0", "Odoo 10.0"),
            ("11.0", "Odoo 11.0"),
            ("12.0", "Odoo 12.0"),
            ("13.0", "Odoo 13.0"),
            ("14.0", "Odoo 14.0"),
            ("15.0", "Odoo 15.0"),
            ("16.0", "Odoo 16.0"),
        ]


class BaseSynchroConnector(AbstractComponent):
    """ Base Odoo Connector Component

    All components of this connector should inherit from it.
    """

    _name = 'base.synchro.connector'
    _inherit = 'base.connector'
    _collection = 'synchro.backend'
