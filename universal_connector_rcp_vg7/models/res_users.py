#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    _sql_constraints = [
        ("ref_unique_vg7_id", "unique(vg7_id)", "Remote ref must be unique!"),
    ]

    vg7_id = fields.Integer("VG7 ID", copy=False)


class ResGroups(models.Model):
    _inherit = "res.groups"

    _sql_constraints = [
        ("ref_unique_vg7_id", "unique(vg7_id)", "Remote ref must be unique!"),
    ]

    vg7_id = fields.Integer("VG7 ID", copy=False)
