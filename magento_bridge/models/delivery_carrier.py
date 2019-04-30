# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, models
from res_partner import _unescape


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    @api.model
    def create(self, vals):
        if 'magento' in self._context:
            vals['name'] = _unescape(vals['name'])
            vals['product_type'] = 'service'
        return super(DeliveryCarrier, self).create(vals)
