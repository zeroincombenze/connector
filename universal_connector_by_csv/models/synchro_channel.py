#
# Copyright 2018-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
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

    method = fields.Selection(
        selection_add=[
            ("csv", "Import by csv"),
        ],
    )

    def get_method_from_protocol(self, prot):
        if prot == "csv":
            return prot
        return super().get_method_from_protocol(prot)

    def get_protocol_from_method(self, method):
        if method == "csv":
            return method
        return super().get_protocol_from_method(method)

    def extract_protocol(self, parts):
        return (
            parts.scheme if parts.scheme == "file:" else super().extract_protocol(parts)
        )
