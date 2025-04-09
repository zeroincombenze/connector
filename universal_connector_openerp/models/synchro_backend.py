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


class SynchroBackend(models.Model):
    """Model for Odoo Backends"""

    _inherit = "synchro.backend"

    prefix = fields.Selection(
        selection_add=[
            ("oe8", "oe8"),
            ("oe7", "oe7"),
        ],
    )

    def selection_for_prefix(self):
        res = super().selection_for_prefix()
        return res + [
            ("oe8", "oe8"),
            ("oe7", "oe7"),
        ]

    def view_init(self, fields_list):
        super().view_init(fields_list)
