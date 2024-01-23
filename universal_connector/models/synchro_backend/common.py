#
# Copyright 2019-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

import os
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta

from odoo import api, fields, models
from odoo.addons.universal_connector.components.backend_adapter import OdooAPI
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

IMPORT_DELTA_BUFFER = 30  # seconds

_logger = logging.getLogger(__name__)


class SynchroBackend(models.Model):
    """Model for Odoo Backends"""

    _name = "synchro.backend"
    _description = "Odoo Backend"
    _inherit = "connector.backend"
    _backend_type = "odoo"
    _order = 'sequence,name'

    @api.model
    def _select_state(self):
        """Available States for this Backend"""
        return [
            ("draft", "Draft"),
            ("checked", "Checked"),
            ("production", "In Production"),
        ]

    @api.model
    def is_odoo(self):
        res = False
        if self.identity_id:
            for nm in ('odoo', 'zero', 'powerp', 'librerp'):
                if self.identity_id.code.startswith(nm):
                    res = True
                    break
        return res

    @api.model
    def get_login_endpoint(self, with_port=None):
        if self.identity_id.login_endpoint:
            endpoint = '%s/%s' % (self.hostname,
                                  self.identity_id.login_endpoint)
        else:
            endpoint = self.hostname
        if self.protocol_id:
            if self.protocol_id.code.startswith('https'):
                endpoint = 'https://%s' % endpoint
            elif self.protocol_id.code.startswith('http'):
                endpoint = 'http://%s' % endpoint
        if with_port:
            endpoint = '%s:%d' % (endpoint, self.port)
        return endpoint

    @api.model
    def get_data_endpoint(self, with_port=None):
        if self.identity_id.data_endpoint:
            endpoint = '%s/%s' % (self.hostname,
                                  self.identity_id.data_endpoint)
        elif self.identity_id.login_endpoint:
            endpoint = '%s/%s' % (self.hostname,
                                  self.identity_id.login_endpoint)
        else:
            endpoint = self.hostname
        if self.protocol_id:
            if self.protocol_id.code.startswith('https'):
                endpoint = 'https://%s' % endpoint
            elif self.protocol_id.code.startswith('http'):
                endpoint = 'http://%s' % endpoint
        if with_port:
            endpoint = '%s:%d' % (endpoint, self.port)
        return endpoint

    def _default_protocol(self):
        if self.identity_id and self.identity_id.default_protocol_id:
            code = self.identity_id.default_protocol_id
        elif self.is_odoo():
            if self.version and int(self.version.split('.')[0]) < 10:
                code = 'xmlrpc'
            else:
                code = 'jsonrpc'
        else:
            code = 'https+json'
        prot_ids = self.env['synchro.connector.protocol'].search(
            [('code', '=', code)]
        )
        if prot_ids:
            return prot_ids[0]
        return False

    def _default_language(self):
        if self.env.user.lang and self.env.user.lang != 'en_US':
            lang = self.env.user.lang
        else:
            lang = (
                self.env.context.get('lang')
                or os.environ.get('LANG', 'en_US').split('.')[0]
            )
        lang_ids = self.env['res.lang'].search([('code', '=', lang)])
        if lang_ids:
            return lang_ids[0]
        return self.env['res.lang'].search([('code', '=', 'en_US')])[0]

    def _default_name(self):
        return '%.15s-%.8s-%s (%d)' % (
            self.hostname or 'localhost',
            self.database or 'demo',
            self.identity_id and self.identity_id.code or '',
            self.id,
        )

    name = fields.Char(string="Name", default=_default_name)
    sequence = fields.Integer('Priority', default=16)
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(
        selection="_select_state",
        string="State",
        default="draft",
    )
    identity_id = fields.Many2one(
        comodel_name="synchro.connector.identity",
        string="Identity",
        required=True,
        help="Remote identity like Odoo or Magento or others",
    )
    protocol_id = fields.Many2one(
        comodel_name="synchro.connector.protocol",
        string="Protocol",
        required=True,
        default=_default_protocol,
        help="Comunication Protocol like jsonrpc or http or others",
    )
    version = fields.Selection(
        selection=lambda self: self.select_odoo_version(),
        string="Remote Odoo version",
    )
    hostname = fields.Char(
        string="Hostname",
        required=True,
        help="Host name without protcol; may be an IP address",
    )
    database = fields.Char(string="Database")
    login = fields.Char(
        string="Username / Client id",
        required=True,
        help="Username to login remote counterpart or Client ID.",
    )
    password = fields.Char(
        string="Password / Client key",
        required=True,
        help="Password to login remote counterpart or Client KEY.",
    )
    port = fields.Integer(
        string="Communication Port",
        required=True,
        help="Port to comunicate with remote counterpart; Odoo uses 8069",
        default=8069,
    )
    create_only = fields.Boolean(
        string="Create only", help="Don't update imported records"
    )
    use_queue = fields.Boolean(
        string="Use queue",
        help="Use queue for big data: queue run in background"
    )
    pypi_sign = fields.Char(
        string="PYPI library",
        readonly=True,
        help="Python library used to communicate with remote counterpart",
    )
    login_endpoint = fields.Char(
        string="Login Endpoint",
        readonly=True,
        help="Remote counterpart full endpoint",
    )
    data_endpoint = fields.Char(
        string="Data Endpoint",
        readonly=True,
        help="Remote counterpart full endpoint",
    )

    default_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Default User",
        required=False,
        help="User will be used if external user is not present in Odoo",
    )
    default_lang_id = fields.Many2one(
        comodel_name="res.lang",
        string="Default Language",
        required=True,
        default=_default_language,
    )
    model_ids = fields.One2many(
        'synchro.backend.model', 'backend_id',
        string='Model mapping'
    )

    @api.multi
    def name_get(self):
        result = []
        for backend in self:
            result.append((backend.id, backend._default_name()))
        return result

    @api.onchange('identity_id')
    def _onchange_identity(self):
        if self.identity_id:
            self.version = self.identity_id.odoo_version
            self.login_endpoint = self.identity_id.login_endpoint
            self.data_endpoint = self.identity_id.data_endpoint
            self.protocol_id = self.identity_id.default_protocol_id
            protocol_domain = [
                (
                    'id',
                    'in',
                    [
                        x.id
                        for x in self.env['synchro.connector.protocol'].search(
                            [
                                (
                                    'code',
                                    'in',
                                    self.identity_id.enabled_protocols.split(
                                        ','
                                    ),
                                )
                            ]
                        )
                    ],
                )
            ]
        else:
            protocol_domain = []
        return {'domain': {'protocol_id': protocol_domain}}

    @api.onchange('protocol_id')
    def _onchange_protocol(self):
        if self.identity_id:
            protocol_ids = self.env['synchro.connector.protocol'].search(
                [('code', 'in', self.identity_id.enabled_protocols.split(','))]
            )
        else:
            protocol_ids = self.env['synchro.connector.protocol'].search([])
        if self.protocol_id not in protocol_ids:
            self.protocol_id = (
                self.identity_id.default_protocol_id
                if self.identity_id
                else False
            )
        self.port = self.protocol_id.default_port

    @api.multi
    def _check_connection(self):
        self.ensure_one()
        odoo_api = OdooAPI(self)
        self.pypi_sign = odoo_api._pypi_sign
        odoo_api.complete_check()
        self.login_endpoint = odoo_api._login_endpoint
        self.data_endpoint = odoo_api._data_endpoint
        self.write({"state": "checked"})

    @api.multi
    def button_check_connection(self):
        self._check_connection()

    @api.multi
    def button_reset_to_draft(self):
        self.ensure_one()
        self.pypi_sign = False
        self.write({"state": "draft"})

    @api.multi
    def button_discover_peer_model(self):
        self.ensure_one()
        # self.identity_id.search_peer_model(self)
        self._import_model('synchro.ir.model')
        self.write({"state": "draft"})

    @contextmanager
    @api.multi
    def work_on(self, model_name, **kwargs):
        """
        Place the connexion here regarding the documentation
        http://odoo-connector.com/api/api_components.html\
            #odoo.addons.component.models.collection.Collection
        """
        self.ensure_one()
        lang = self. default_lang_id.code
        with OdooAPI(self) as odoo_api:
            _super = super(SynchroBackend, self.with_context(lang=lang))
            # from the components we'll be able to do: self.work.odoo_api
            with _super.work_on(
                model_name, odoo_api=odoo_api, **kwargs
            ) as work:
                yield work

    @api.multi
    def _import_model(self, model, from_date_field=None, from_backend=None,
                      use_queue=None):
        import_start_time = datetime.now()
        filters = [
            # ("write_date", "<", fields.Datetime.to_string(import_start_time))
        ]
        use_queue = use_queue if use_queue is not None else self.use_queue
        from_backend = from_backend or self
        for backend in from_backend:
            from_date = None
            if from_date_field:
                from_date = backend[from_date_field]
            if from_date:
                filters.append(
                    (
                        "write_date",
                        ">",
                        import_start_time.strftime(
                            DEFAULT_SERVER_DATETIME_FORMAT
                        ),
                    )
                )
            if use_queue:
                self.env[model].with_delay().import_batch(backend, filters)
            else:
                self.env[model].import_batch(backend, filters)
            if from_date_field:
                next_time = fields.Datetime.to_string(
                    import_start_time - timedelta(
                        seconds=IMPORT_DELTA_BUFFER))
                self.write({from_date_field: next_time})
