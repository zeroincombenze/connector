#
# Copyright 2019-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
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

    vg7_id = fields.Integer("VG7 ID", copy=False)


class ResCountryState(models.Model):
    _inherit = "res.country.state"

    vg7_id = fields.Integer("VG7 ID", copy=False)
