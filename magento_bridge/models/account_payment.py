# flake8: noqa
# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, models


class account_payment(models.Model):
    _inherit = "account.payment"

    @api.multi
    def post(self):
        res = super(account_payment, self).post()
        saleModel = self.env['sale.order']
        enableOrderInvoice = self.env['ir.values'].sudo().get_default(
            'mob.config.settings', 'mob_sale_order_invoice', False)
        for invObj in self.mapped('invoice_ids').filtered(lambda obj: obj.origin != ''):
            saleObj = saleModel.search(
                [('name', '=', invObj.origin)], limit=1)
            if saleObj.ecommerce_channel == "magento" \
                    and enableOrderInvoice and saleObj.is_invoiced:
                saleObj.manual_magento_order_operation("invoice")
        return res
