#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResCurrency(models.Model):
    _inherit = "res.currency"

    vg7_id = fields.Integer("VG7 ID", copy=False)


class ResCurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    vg7_id = fields.Integer("VG7 ID", copy=False)

