#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    _sql_constraints = [
        ('ref_unique_odoo_id', 'unique(odoo_id)', 'Remote ref must be unique!'),
        ('ref_unique_odoo16_id', 'unique(odoo16_id)', 'Remote ref must be unique!'),
        ('ref_unique_odoo14_id', 'unique(odoo14_id)', 'Remote ref must be unique!'),
        ('ref_unique_odoo12_id', 'unique(odoo12_id)', 'Remote ref must be unique!'),
        ('ref_unique_odoo10_id', 'unique(odoo10_id)', 'Remote ref must be unique!'),
    ]

    odoo_id = fields.Integer("Odoo ID", copy=False)
    odoo16_id = fields.Integer("Odoo16 ID", copy=False)
    odoo14_id = fields.Integer("Odoo14 ID", copy=False)
    odoo12_id = fields.Integer("Odoo12 ID", copy=False)
    odoo10_id = fields.Integer("Odoo10 ID", copy=False)
