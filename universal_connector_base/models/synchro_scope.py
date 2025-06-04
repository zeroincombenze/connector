#
# Copyright 2019-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import fields, models


class SynchroBackendScope(models.Model):
    _name = "synchro.scope"
    _description = "Scope backend"
    _order = "code"

    code = fields.Char(
        "SCope code", required=True, help="Give a unique name for scope"
    )
    name = fields.Char("Scope Name")
    disable_xref_module = fields.Char(
        string="Protected xref modules",
        help="Record linked to external reference which module name match this field"
             " will be protect against update from remote counterpart;\n"
             "module names are comma separated;\n"
             "i.e. 'base,product' avoid update for records match external reference "
             "'base.it', 'base.EUR', 'product.template_1', etc",
        default="base,product")
    enable_user_partner = fields.Boolean(
        string="Enable update of user partner",
        help="Partner record linked to user are protected against update;\n"
             "enable this flag to enable update from remote counterpart",
        default=False)
