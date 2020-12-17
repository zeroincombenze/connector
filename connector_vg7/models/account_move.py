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

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.multi
    @api.depends('name')
    def _set_dim_name(self):
        for partner in self:
            partner.dim_name = self.env[
                'ir.model.synchro'].dim_text(partner.name)

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)
    original_state = fields.Char('Original Status', copy=False)
    timestamp = fields.Datetime('Timestamp', copy=False, readonly=True)
    errmsg = fields.Char('Error message', copy=False, readonly=True)

    @api.model_cr_context
    def _auto_init(self):
        res = super(AccountMove, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.multi
    def pull_record(self):
        self.env['ir.model.synchro'].pull_record(self)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)
    to_delete = fields.Boolean('Record to delete')

    @api.model_cr_context
    def _auto_init(self):
        res = super(AccountMoveLine, self)._auto_init()
        for prefix in ('vg7', 'oe7'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.model
    def synchro(self, vals, disable_post=None, no_deep_fields=None,
                only_minimal=None):
        if 'type' in vals:
            del vals['type']
        return self.env['ir.model.synchro'].synchro(self, vals,
            disable_post=disable_post,
            no_deep_fields=no_deep_fields, only_minimal=only_minimal)

    @api.multi
    def pull_record(self):
        self.env['ir.model.synchro'].pull_record(self)
