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
        selection_add=[("vg7", "vg7")],
    )

    def selection_for_prefix(self):
        res = super().selection_for_prefix()
        return res + [("vg7", "vg7")]

    def selection_for_version(self, identity=None):
        res = super().selection_for_version(identity=identity)
        if not identity or identity.code == "vg7":
            res += [("1.0", "VG7 v1"), ("2.0", "VG/ v2")]
        return res
