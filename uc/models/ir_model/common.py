#
# Copyright 2019-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

import logging

from odoo import fields, models
from odoo.addons.component.core import Component
from odoo.addons.component_event.components.event import skip_if

_logger = logging.getLogger(__name__)


class SynchroIrModel(models.Model):
    _name = "synchro.ir.model"
    _inherit = "odoo.binding"
    _inherits = {"ir.model": "odoo_id"}
    _description = "External Odoo Models"


class IrModel(models.Model):
    _inherit = "ir.model"

    bind_ids = fields.One2many(
        comodel_name="synchro.ir.model",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class IrModelAdapter(Component):
    _name = "synchro.ir.model.adapter"
    _inherit = "synchro.adapter"
    _apply_on = "synchro.ir.model"
    _odoo_model = "ir.model"

    def search(self, filters=None, model=None):
        """ Search records according to some criteria
        and returns a list of ids

        :rtype: list
        """
        # filters = filters or [('model', 'in', ('res.partner', 'res.users'))]
        filters = filters or [('model', 'like', 'res.%')]
        return super().search(filters=filters, model=model)


class IrModelListener(Component):
    _name = 'ir.model.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['ir.model']
    _usage = 'event.listener'

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        # FIXME: do the proper way
        bind_model = self.env['synchro.res.partner']
        backend = self.env['odoo.backend'].search([])
        binding = bind_model.create({
            "backend_id": backend[0].id,
            "odoo_id": record.id,
            "external_id": 0,
        })
        binding.with_delay().export_record(backend)
