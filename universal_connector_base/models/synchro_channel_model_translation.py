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


class SynchroChannelDomainTnl(models.Model):
    _name = "synchro.channel.domain.translation"
    _description = "Field translation for field"

    model = fields.Char("Odoo model name")
    key = fields.Char("Odoo field name")
    odoo_value = fields.Char("Odoo field value")
    ext_value = fields.Char("External field value")
