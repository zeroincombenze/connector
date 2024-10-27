#
# Copyright 2019-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import fields, models


class SynchroConnectorProtocol(models.Model):
    _name = 'synchro.connector.protocol'
    _description = "Connection protocol"
    _inherit = "connector.backend"
    _order = 'code desc'

    code = fields.Char(
        'Protocol code',
        required=True,
        help="Give a unique name for identity")
    name = fields.Char(
        'Protocol Name',
        required=True,
        help="Give a name for identity")
    default_port = fields.Integer(
        string="Default port",
    )
    pylib = fields.Char(
        string="Python Library used",
    )
