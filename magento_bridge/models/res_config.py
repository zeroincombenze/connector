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
    _name = 'mob.config.settings'
    _inherit = 'res.config.settings'

    mob_discount_product = fields.Many2one(
        'product.product',
        string="Discount Product",
        help="""Service type product used for Discount purposes.""")
    mob_coupon_product = fields.Many2one(
        'product.product',
        string="Coupon Product",
        help="""Service type product used in Coupon.""")
    mob_payment_term = fields.Many2one(
        'account.payment.term',
        string="Magento Payment Term",
        help="""Default Payment Term Used In Sale Order.""")
    mob_sales_team = fields.Many2one(
        'crm.team',
        string="Magento Sales Team",
        help="""Default Sales Team Used In Sale Order.""")
    mob_sales_person = fields.Many2one(
        'res.users',
        string="Magento Sales Person",
        help="""Default Sales Person Used In Sale Order.""")
    mob_sale_order_invoice = fields.Boolean(string="Invoice")
    mob_sale_order_shipment = fields.Boolean(string="Shipping")
    mob_sale_order_cancel = fields.Boolean(string="Cancel")

    @api.multi
    def set_default_fields(self):
        irValuesModel = self.env['ir.values']
        irValuesModel.sudo().set_default('product.product', 'mob_discount_product',
                                         self.mob_discount_product and self.mob_discount_product.id or False, False)
        irValuesModel.sudo().set_default('product.product', 'mob_coupon_product',
                                         self.mob_coupon_product and self.mob_coupon_product.id or False, False)
        irValuesModel.sudo().set_default('account.payment.term', 'mob_payment_term',
                                         self.mob_payment_term and self.mob_payment_term.id or False, False)
        irValuesModel.sudo().set_default(
            'crm.team',
            'mob_sales_team',
            self.mob_sales_team and self.mob_sales_team.id or False,
            False)
        irValuesModel.sudo().set_default('res.users', 'mob_sales_person',
                                         self.mob_sales_person and self.mob_sales_person.id or False, False)
        irValuesModel.sudo().set_default(
            'mob.config.settings',
            'mob_sale_order_shipment',
            self.mob_sale_order_shipment or False,
            False)
        irValuesModel.sudo().set_default(
            'mob.config.settings',
            'mob_sale_order_cancel',
            self.mob_sale_order_cancel or False,
            False)
        irValuesModel.sudo().set_default(
            'mob.config.settings',
            'mob_sale_order_invoice',
            self.mob_sale_order_invoice or False,
            False)
        return True

    @api.model
    def get_default_fields(self, fields):
        irValuesModel = self.env['ir.values']
        mobDiscountProduct = irValuesModel.sudo().get_default(
            'product.product', 'mob_discount_product', False)
        mobCouponProduct = irValuesModel.sudo().get_default(
            'product.product', 'mob_coupon_product', False)
        mobPaymentTerm = irValuesModel.sudo().get_default(
            'account.payment.term', 'mob_payment_term', False)
        mobSalesTeam = irValuesModel.sudo().get_default(
            'crm.team', 'mob_sales_team', False)
        mobSalesPerson = irValuesModel.sudo().get_default(
            'res.users', 'mob_sales_person', False)
        mobSaleOrderShipment = irValuesModel.sudo().get_default(
            'mob.config.settings', 'mob_sale_order_shipment', False)
        mobSaleOrderCancel = irValuesModel.sudo().get_default(
            'mob.config.settings', 'mob_sale_order_cancel', False)
        mobSaleOrderInvoice = irValuesModel.sudo().get_default(
            'mob.config.settings', 'mob_sale_order_invoice', False)
        return {
            'mob_discount_product': mobDiscountProduct,
            'mob_coupon_product': mobCouponProduct,
            'mob_payment_term': mobPaymentTerm,
            'mob_sales_team': mobSalesTeam,
            'mob_sales_person': mobSalesPerson,
            'mob_sale_order_shipment': mobSaleOrderShipment,
            'mob_sale_order_cancel': mobSaleOrderCancel,
            'mob_sale_order_invoice': mobSaleOrderInvoice,
        }
