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


class ResCountry(models.Model):
    _inherit = "res.country"

    _sql_constraints = [
        ("ref_unique_oe8_id", "unique(oe8_id)", "Remote ref must be unique!"),
        ("ref_unique_oe7_id", "unique(oe7_id)", "Remote ref must be unique!"),
    ]

    oe7_id = fields.Integer("Odoo7 ID", copy=False)
    oe8_id = fields.Integer("Odoo8 ID", copy=False)


class ResCountryState(models.Model):
    _inherit = "res.country.state"

    _sql_constraints = [
        ("ref_unique_oe8_id", "unique(oe8_id)", "Remote ref must be unique!"),
        ("ref_unique_oe7_id", "unique(oe7_id)", "Remote ref must be unique!"),
    ]

    oe7_id = fields.Integer("Odoo7 ID", copy=False)
    oe8_id = fields.Integer("Odoo8 ID", copy=False)
