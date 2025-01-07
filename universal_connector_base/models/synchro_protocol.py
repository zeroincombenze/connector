#
# Copyright 2019-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import api, fields, models


class SynchroProtocol(models.Model):
    _name = "synchro.protocol"
    _description = "Communication Protocol"

    code = fields.Char(
        "Protocol code", required=True, help="Give a unique name for identity"
    )
    name = fields.Char("Protocol Name", help="Give a name for identity")
    secure_protocol = fields.Boolean(string="Secure")
    http_protocol = fields.Boolean(string="Use http/https")
    default_port = fields.Integer(
        string="Default port",
    )
    default_lgi_path = fields.Char(
        "RPC login path",
        help="Counterpart login path when load by rpc over https",
    )
    default_exchange_path = fields.Char(
        "Exchange directory data path",
        help="Counterpart data path when load by rpc over https"
        " or where file will be read and written when load by csv",
    )
    pylib = fields.Char(
        string="Python Library used",
    )

    @api.multi
    @api.depends("code", "name")
    def name_get(self):
        result = []
        for protocol in self:
            name = "[%s] %s (%s)" % (protocol.code, protocol.name, protocol.pylib)
            result.append((protocol.id, name))
        return result
