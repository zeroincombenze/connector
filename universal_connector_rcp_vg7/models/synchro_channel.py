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


class SynchroChannel(models.Model):
    """Model for Odoo Backends"""

    _inherit = "synchro.channel"

    identity = fields.Selection(
        selection_add=[
            ("vg7", "VG7 print"),
        ],
    )
    prefix = fields.Selection(
        selection_add=[
            ("vg7", "vg7"),
        ],
    )
