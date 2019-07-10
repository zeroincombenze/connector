# -*- coding: utf-8 -*-
# Copyright 2019 Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from odoo import fields, models, api
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

try:
    from unidecode import unidecode
except ImportError as err:
    _logger.debug(err)


class ResCountry(models.Model):
    _inherit = "res.country"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)

    SKEYS = (['code'])
    CONTRAINTS = []
    KEEP = []
    DEFAULT = {}

    @api.model_cr_context
    def _auto_init(self):
        res = super(ResCountry, self)._auto_init()
        for prefix in ('vg7', 'oe7'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.model
    def synchro(self, vals):
        return self.env['ir.model.synchro'].synchro(self, vals)
