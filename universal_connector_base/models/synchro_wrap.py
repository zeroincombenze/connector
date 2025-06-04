#
# Copyright 2019-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import fields, models


class SynchroWrap(models.Model):
    _name = "synchro.wrap"
    _description = "Model and field variant for synchronization mapping"
    _order = "sequence, code"

    sequence = fields.Integer("Priority", default=16)
    code = fields.Char(
        "Variant code", required=True, help="Give a unique name for variant"
    )
    name = fields.Char("Variant Name")
