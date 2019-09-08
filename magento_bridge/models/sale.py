# flake8: noqa - pylint: skip-file
# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import xmlrpclib

from odoo import api, models

XMLRPC_API = '/index.php/api/xmlrpc'


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _get_ecommerces(self):
        res = super(SaleOrder, self)._get_ecommerces()
        res.append(('magento', 'Magento'))
        return res

    @api.one
    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        enableOrderCancel = self.env['ir.values'].sudo().get_default(
            'mob.config.settings', 'mob_sale_order_cancel', False)
        if self.ecommerce_channel == "magento" and enableOrderCancel:
            self.manual_magento_order_operation("cancel")
        return res

    @api.one
    def manual_magento_order_operation(self, opr):
        text = ''
        status = 'no'
        session = False
        mageShipment = False
        mapObjs = self.env['wk.order.mapping'].search(
            [('erp_order_id', '=', self.id)])
        if mapObjs:
            incrementId = mapObjs[0].name
            orderName = self.name
            connectionObj = mapObjs[0].instance_id
            if connectionObj.active:
                if connectionObj.state != 'enable':
                    return False
                else:
                    url = connectionObj.name + XMLRPC_API
                    user = connectionObj.user
                    pwd = connectionObj.pwd
                    email = connectionObj.notify
                    try:
                        server = xmlrpclib.Server(url)
                        session = server.login(user, pwd)
                    except xmlrpclib.Fault as e:
                        text = 'Error, %s Magento details are Invalid.' % e
                    except IOError as e:
                        text = 'Error, %s.' % e
                    except Exception as e:
                        text = 'Error in Magento Connection.'
                    if session and incrementId:
                        if opr == "shipment":
                            try:
                                shidData = [
                                    incrementId, "Shipped From Odoo", email]
                                mageShipment = server.call(
                                    session, 'magerpsync.order_shippment', shidData)
                                text = 'shipment of order %s has been successfully updated on magento.' % orderName
                                status = 'yes'
                            except xmlrpclib.Fault as e:
                                text = 'Magento shipment Error For Order %s , Error %s.' % (
                                    orderName, e)
                        elif opr == "cancel":
                            try:
                                server.call(
                                    session, 'sales_order.cancel', [incrementId])
                                text = 'sales order %s has been sucessfully canceled from magento.' % orderName
                                status = 'yes'
                            except Exception as e:
                                text = 'Order %s cannot be canceled from magento, Because Magento order %s \
                                    is in different state.' % (orderName, incrementId)
                        elif opr == "invoice":
                            try:
                                invData = [
                                    incrementId, "Invoiced From Odoo", email]
                                magInvoice = server.call(
                                    session, 'magerpsync.order_invoice', invData)
                                text = 'Invoice of order %s has been sucessfully updated on magento.' % orderName
                                status = 'yes'
                            except Exception as e:
                                text = 'Magento Invoicing Error For Order %s , Error %s.' % (
                                    orderName, e)
                self._cr.commit()
                self.env['magento.sync.history'].create(
                    {'status': status, 'action_on': 'order', 'action': 'b', 'error_message': text})
        return mageShipment
