#
# Copyright 2019-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import fields, models, _
from odoo.exceptions import UserError


class SynchroConnectorIdentity(models.Model):
    _name = 'synchro.connector.identity'
    _description = "Counterpart identity"
    _inherit = "connector.backend"
    _order = 'sequence,code desc'

    code = fields.Char(
        'Identity code',
        required=True,
        help="Give a unique name for identity")
    name = fields.Char(
        'Identity Name',
        required=True,
        help="Give a name for identity")
    odoo_version = fields.Selection(
        selection=lambda self: self.select_odoo_version(),
        string="Odoo version"
    )
    default_protocol_id = fields.Many2one(
        comodel_name="synchro.connector.protocol",
        string="Default protocol",
    )
    enabled_protocols = fields.Char(
        'Enabled protocols',
        help="Protocols valid for this identity, comma separated")
    login_endpoint = fields.Char('Login Endpoint')
    data_endpoint = fields.Char('Data Endpoint')
    sequence = fields.Integer('Priority', default=16)
    active = fields.Boolean(string='Active', default=True)

    def search_peer_model(self, backend):
        self.ensure_one()
        if not backend.identity_id or not backend.is_odoo():
            raise UserError(
                _("Unable to discover remote models/tables!")
            )
        model = 'ir.model'
        self.env[model].with_delay().import_batch(backend, None)
        default_models = self.env['ir.config_parameter'].sudo().get_param(
            'aynchro.default.models',
            default='res.partner,res.users')
        for model in default_models:
            pass
