# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, fields, models


class MobConfigSettings(models.TransientModel):
    _inherit = 'mob.config.settings'

    mob_stock_action = fields.Selection(
        [('qoh', 'Quantity on hand'), ('fq', 'Forecast Quantity')],
        string='Stock Management',
        help="Manage Stock")

    @api.multi
    def set_default_stock_fields(self):
        self.env['ir.values'].sudo().set_default(
            'mob.config.settings',
            'mob_stock_action',
            self.mob_stock_action or False,
            False)
        return True

    @api.multi
    def get_default_stock_fields(self, fields):
        mob_stock_action = self.env['ir.values'].sudo().get_default(
            'mob.config.settings', 'mob_stock_action', False)
        return {'mob_stock_action': mob_stock_action}
