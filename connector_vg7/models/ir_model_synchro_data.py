# -*- coding: utf-8 -*-
#
# Copyright 2019-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class IrModelSynchroData(models.Model):
    _name = 'ir.model.synchro.data'

    model = fields.Char('Model')
    ext_id_name = fields.Char('External ID name', required=True)
    ext_id = fields.Integer('External ID', copy=False, required=True)
    res_id = fields.Integer('Model ID', copy=False, required=True)

    _sql_constraints = [
        ('ext_id_uniq', 'unique(model, ext_id_name, ext_id)',
         'Duplicate external ID!'),
    ]
