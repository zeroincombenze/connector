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

from odoo import _, api, fields, models
from odoo.exceptions import UserError

XMLRPC_API = '/index.php/api/xmlrpc'

Carrier_Code = [
    ('custom', 'Custom Value'),
    ('dhl', 'DHL (Deprecated)'),
    ('fedex', 'Federal Express'),
    ('ups', 'United Parcel Service'),
    ('usps', 'United States Postal Service'),
    ('dhlint', 'DHL')
]


class StockPicking(models.Model):
    _inherit = "stock.picking"

    carrier_code = fields.Selection(
        Carrier_Code,
        string='Magento Carrier',
        default="custom",
        help="Magento Carrier")
    magento_shipment = fields.Char(
        string='Magento Shipment',
        help="Contains Magento Order Shipment Number (eg. 300000008)")

    @api.multi
    def do_transfer(self):
        res = super(StockPicking, self).do_transfer()
        orderObj = self.sale_id
        origin = self.origin
        if origin == orderObj.name:
            enableOrderShipment = self.env['ir.values'].sudo().get_default(
                'mob.config.settings', 'mob_sale_order_shipment', False)
            if orderObj.is_shipped and orderObj.ecommerce_channel == "magento" \
                    and enableOrderShipment:
                magShipment = orderObj.manual_magento_order_operation(
                    "shipment")
                if magShipment and magShipment[0]:
                    self.magento_shipment = magShipment[0]
                    if self.carrier_tracking_ref:
                        self.action_sync_tracking_no()
        return res

    @api.multi
    def action_sync_tracking_no(self):
        text = ''
        for stockObj in self:
            saleId = stockObj.sale_id.id
            magShipment = stockObj.magento_shipment
            carrierCode = stockObj.carrier_code
            carrierTrackingNo = stockObj.carrier_tracking_ref
            if not carrierTrackingNo:
                raise UserError(
                    'Warning! Sorry No Carrier Tracking No. Found!!!')
            elif not carrierCode:
                raise UserError('Warning! Please Select Magento Carrier!!!')
            carrierTitle = dict(Carrier_Code)[carrierCode]
            mapObjs = self.env['wk.order.mapping'].search(
                [('erp_order_id', '=', saleId)])
            if mapObjs:
                obj = mapObjs[0].instance_id
                url = obj.name + XMLRPC_API
                user = obj.user
                pwd = obj.pwd
                email = obj.notify
                try:
                    server = xmlrpclib.Server(url)
                    session = server.login(user, pwd)
                except xmlrpclib.Fault as e:
                    text = 'Error, %s Magento details are Invalid.' % e
                except IOError as e:
                    text = 'Error, %s.' % e
                except Exception as e:
                    text = 'Error in Magento Connection.'
                if session:
                    trackArray = [magShipment, carrierCode,
                                  carrierTitle, carrierTrackingNo]
                    try:
                        mage_track = server.call(
                            session, 'sales_order_shipment.addTrack', trackArray)
                        text = 'Tracking number successfully added.'
                    except xmlrpclib.Fault as e:
                        text = "Error While Syncing Tracking Info At Magento. %s" % e
                return self.env['magento.synchronization'].display_message(
                    text)


# END
