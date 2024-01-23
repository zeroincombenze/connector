#
# Copyright 2019-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


SYSTEM_MODEL_ROOT = [
    "base.config.",
    "base_import.",
    "base.language.",
    "base.module.",
    "base.setup.",
    "base.update.",
    "ir.actions.",
    "ir.exports.",
    "ir.model.",
    "ir.module.",
    "ir.qweb.",
    "ir.ui.",
    "report.",
    "res.config.",
    "web_editor.",
    "web_tour.",
    "workflow.",
    "x_",
]
SYSTEM_MODELS = [
    "_unknown",
    "base",
    # "base.config.settings",
    "base_import",
    "change.password.wizard",
    "ir.autovacuum",
    "ir.config_parameter",
    "ir.exports",
    "ir.fields.converter",
    "ir.filters",
    "ir.http",
    "ir.logging",
    "ir.model",
    "ir.needaction_mixin",
    "ir.qweb",
    "ir.rule",
    "ir.translation",
    # "ir.ui.menu",
    # "ir.ui.view",
    "ir.values",
    "mail.alias",
    "mail.followers",
    "mail.message",
    "mail.notification",
    "report",
    "res.config",
    "res.font",
    "res.groups",
    "res.request.link",
    "res.users.log",
    "web_tour",
    "workflow",
]
TABLE_DEF = {
    'base': {
        'create_date': {'readonly': True},
        'create_uid': {'readonly': True},
        'message_channel_ids': {'readonly': True},
        'message_follower_ids': {'readonly': True},
        'message_ids': {'readonly': True},
        'message_is_follower': {'readonly': True},
        'message_last_post': {'readonly': True},
        'message_needaction': {'readonly': True},
        'message_needaction_counter': {'readonly': True},
        'message_unread': {'readonly': True},
        'message_unread_counter': {'readonly': True},
        'password': {'protect_update': 2},
        'password_crypt': {'protect_update': 2},
        'write_date': {'readonly': True},
        'write_uid': {'readonly': True},
    },
    'account.account.type': {
        'PRIO': 2,
        'PERM': 'C',
    },
    'res.bank': {
        'PRIO': 3,
        'PERM': 'CW',
    },
    'res.country': {
        'PRIO': 2,
        'PERM': 'C',
    },
    'res.country.group': {
        'PRIO': 3,
        'PERM': 'C',
    },
    'res.country.state': {
        'PRIO': 3,
        'PERM': 'C',
    },
    'res.currency': {
        'PRIO': 2,
        'PERM': 'C',
    },
    'res.currency.rate': {
        'PRIO': 3,
        'PERM': 'CW',
    },
    'res.groups': {
        'PRIO': 3,
        'PERM': '0',
    },
    'res.lang': {
        'PRIO': 2,
        'PERM': 'C',
    },
}


class IrModelBatchImporter(Component):
    """ Import the Odoo model."""

    _name = "synchro.ir.model.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["synchro.ir.model"]

    def run(self, filters=None):
        """ Run the synchronization """

        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo models %s returned %s", filters, external_ids
        )
        for external_id in external_ids:
            job_options = {"priority": 15} if self.backend_record.use_queue else {}
            self._import_record(external_id, job_options=job_options)


class IrModelImportMapper(Component):
    _name = "synchro.ir.model.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["synchro.ir.model"]

    direct = [
        ("name", "name"),
        ("model", "model"),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        filters = [("model", "=", record.model)]
        irmodel = self.env["ir.model"].search(filters)
        if len(irmodel) == 1:
            return {"odoo_id": irmodel.id}
        return {}


class IrModelImporter(Component):
    _name = "synchro.ir.model.importer"
    _inherit = "odoo.importer"
    _apply_on = ["synchro.ir.model"]
    # _usage = 'batch.importer'
    # _collection = 'synchro.backend'

    def _after_import(self, binding, external_data):
        """ Hook called at the end of the import """
        super()._after_import(binding, external_data)
        line_id = False
        ir_model_id = False
        for rec in binding.backend_id.model_ids:
            if rec.peer_name == 'ir.model':
                ir_model_id = True
            if rec.model_id == binding.odoo_id:
                line_id = rec.id
            if line_id and ir_model_id:
                break
        if not ir_model_id:
            vals = {
                'backend_id': binding.backend_id.id,
                'peer_name': 'ir.model',
                'model_id': self.env['ir.model'].search(
                    [('model', '=', 'ir.model')]).id,
                'permission': '0',
                'sequence': 96,
            }
            binding.backend_id.model_ids = [(0, 0, vals)]
        vals = {
            'backend_id': binding.backend_id.id,
            'peer_name': binding.model,
            'model_id': binding.odoo_id.id,
            'permission': TABLE_DEF.get(binding.odoo_id.model, {}).get('PERM', 'CW'),
            'sequence': TABLE_DEF.get(binding.odoo_id.model, {}).get('PRIO', 64),
        }
        if line_id:
            # binding.backend_id.model_ids = [(1, 0, vals)]
            pass
        else:
            binding.backend_id.model_ids = [(0, 0, vals)]

    def _must_skip(self):
        """ Hook called right after we read the data from the backend.

        If the method returns a message giving a reason for the
        skipping, the import will be interrupted and the message
        recorded in the job (if the import is called directly by the
        job, not by dependencies).

        If it returns None, the import will continue normally.

        :returns: None | str | unicode
        """
        odoo_model = self.odoo_record._name
        ir_model = self.odoo_record.model
        if odoo_model == 'ir.model':
            if ir_model in SYSTEM_MODELS:
                return 'Record %s[%s] is protect' % (odoo_model, ir_model)
            if any([ir_model.startswith(x) for x in SYSTEM_MODEL_ROOT]):
                return 'Record %s[%s] is protect' % (odoo_model, ir_model)
            if not self.env[odoo_model].search([('model', '=', ir_model)]):
                return 'Record %s[%s] does not exist' % (odoo_model, ir_model)
        return
