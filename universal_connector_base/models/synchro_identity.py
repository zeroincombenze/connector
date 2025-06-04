#
# Copyright 2019-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import api, fields, models


class SynchroIdentity(models.Model):
    _name = "synchro.identity"
    _description = "Counterpart identity"
    _order = "sequence,code desc"

    code = fields.Char(
        "Identity code", required=True, help="Give a unique name for identity"
    )
    name = fields.Char("Identity Name", required=True, help="Give a name for identity")
    default_protocol_id = fields.Many2one(
        comodel_name="synchro.protocol",
        string="Default protocol",
    )
    default_login = fields.Char(
        string="Default Username / Client id",
        help="Username to login remote counterparty.",
    )
    default_password = fields.Char(
        "Counterpart Password",
    )
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
    remote_sw_version = fields.Char(
        "Counterpart software version",
        help="Counterpart software version available, comma separated",
    )
    enabled_protocols = fields.Many2many(
        "synchro.protocol",
        string="Enabled protocols",
        help="Protocols (enclosed by quote) valid for this identity, comma separated",
    )
    default_prefix = fields.Char(
        "Download Prefix",
        help="Download prefix which counterparty must use to identify itself",
    )
    sequence = fields.Integer("Priority", default=16)
    active = fields.Boolean(string="Active", default=True)

    @api.multi
    @api.depends("code")
    def name_get(self):
        result = []
        for identity in self:
            name = "[%s] %s " % (identity.code, identity.name)
            result.append((identity.id, name))
        return result
