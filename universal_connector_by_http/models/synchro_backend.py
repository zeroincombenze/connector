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


class SynchroChannel(models.Model):
    """Model for Odoo Backends"""

    _inherit = "synchro.channel"

    method = fields.Selection(
        selection_add=[
            ("https", "By http/https (requests)"),
            ("http", "By http/https (requests) with no certificate verification"),
        ],
    )

    def get_method_from_protocol(self, prot):
        if prot in ("http", "https"):
            return prot
        return super().get_method_from_protocol(prot)

    def get_protocol_from_method(self, method):
        if method in ("http", "https"):
            return method
        return super().get_protocol_from_method(method)

    def extract_protocol(self, parts):
        return (
            parts.scheme
            if parts.scheme in ("http", "https")
            else super().extract_protocol(parts)
        )
