#
# Copyright 2019-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import fields, models


class SynchroBackendModel(models.Model):
    _name = 'synchro.backend.model'
    _description = "Remote peer & Odoo model"

    backend_id = fields.Many2one(
        comodel_name="synchro.backend",
        string="Backend",
        # required=True,
    )
    peer_name = fields.Char(
        'Remote peer model name',
        required=True,
        help="Give a unique name for remote model/table")
    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Odoo model",
    )
    sequence = fields.Integer('Priority', default=64)
    permission = fields.Selection(
        selection=[
            ("0", "No write/No create"),
            ("C", "Only create"),
            ("W", "Only write"),
            ("CW", "Write & Create"),
        ],
        String="Permissions",
        default="CW",
        required=True,
    )
