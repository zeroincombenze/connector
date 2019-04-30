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


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def action_confirm(self):
        """ Confirms stock move or put it in waiting if it's linked to another move.
        """
        mobStockAction = self.env['ir.values'].sudo().get_default(
            'mob.config.settings', 'mob_stock_action', False)
        res = super(StockMove, self).action_confirm()
        if mobStockAction == "fq":
            ctx = dict(self._context or {})
            ctx['mob_stock_action_val'] = mobStockAction
            self.with_context(ctx).fetch_stock_warehouse()
        return res

    @api.multi
    def action_cancel(self):
        """ Confirms stock move or put it in waiting if it's linked to another move.
        """
        ctx = dict(self._context or {})
        ctx['action_cancel'] = True
        mobStockAction = self.env['ir.values'].sudo().get_default(
            'mob.config.settings', 'mob_stock_action', False)
        check = False
        for obj in self:
            if obj.state == "cancel":
                check = True
        res = super(StockMove, self).action_cancel()
        if mobStockAction == "fq" and not check:
            ctx['mob_stock_action_val'] = mobStockAction
            self.with_context(ctx).fetch_stock_warehouse()
        return res

    @api.multi
    def action_done(self):
        """ Process completly the moves given as ids and if all moves are done, it will finish the picking.
        """
        mobStockAction = self.env['ir.values'].sudo().get_default(
            'mob.config.settings', 'mob_stock_action', False)
        check = False
        for obj in self:
            if obj.location_id.usage == "inventory" or obj.location_dest_id.usage == "inventory":
                check = True
        res = super(StockMove, self).action_done()
        if mobStockAction == "qoh" or check:
            ctx = dict(self._context or {})
            ctx['mob_stock_action_val'] = mobStockAction
            self.with_context(ctx).fetch_stock_warehouse()
        return res

    @api.multi
    def fetch_stock_warehouse(self):
        ctx = dict(self._context or {})
        productQuantity = 0
        productModel = self.env['product.product']
        if 'stock_from' not in ctx:
            for data in self:
                odooProductId = data.product_id.id
                ctx['warehouse'] = data.warehouse_id.id
                flag = 1
                if data.origin:
                    saleObjs = data.env['sale.order'].search(
                        [('name', '=', data.origin)])
                    if saleObjs:
                        get_channel = saleObjs[0].ecommerce_channel
                        if get_channel == 'magento' and data.picking_id \
                                and data.picking_id.picking_type_code == 'outgoing':
                            flag = 0
                else:
                    flag = 2  # no origin
                warehouseId = 0
                if flag == 1:
                    warehouseId = data.warehouse_id.id
                if flag == 2:
                    locationId = data.location_dest_id.id
                    companyId = data.company_id.id
                    checkIn = self.env['stock.warehouse'].search(
                        [('lot_stock_id', '=', locationId), ('company_id', '=', companyId)])
                    if not checkIn:
                        checkIn = data.check_warehouse_location(
                            data.location_dest_id, companyId)
                    if checkIn:
                        warehouseId = checkIn[0].id
                    checkOut = self.env['stock.warehouse'].search(
                        [('lot_stock_id', '=', data.location_id.id), ('company_id', '=', companyId)], limit=1)
                    if not checkOut:
                        checkOut = data.check_warehouse_location(
                            data.location_id, companyId)
                    if checkOut:
                        # Sending Goods.
                        warehouseId = checkOut[0].id
                data.check_warehouse(
                    odooProductId, warehouseId, productQuantity)
        return True

    @api.one
    def check_warehouse_location(self, locationObj, company_id):
        flag = True
        checkIn = []
        while flag and locationObj:
            locationObj = locationObj.location_id
            checkIn = self.env['stock.warehouse'].search(
                [('lot_stock_id', '=', locationObj.id), ('company_id', '=', company_id)], limit=1)
            if checkIn:
                flag = False
        return checkIn

    @api.one
    def check_warehouse(self, odooProductId, warehouseId, productQuantity):
        ctx = dict(self._context or {})
        mappingObjs = self.env['magento.product'].search(
            [('pro_name', '=', odooProductId)])
        if mappingObjs:
            mappingObj = mappingObjs[0]
            instanceObj = mappingObj.instance_id
            mageProductId = mappingObj.mag_product_id
            if mappingObj.instance_id.warehouse_id.id == warehouseId:
                ctx['warehouse'] = mappingObj.instance_id.warehouse_id.id
                product_obj = self.env['product.product'].with_context(
                    ctx).browse(odooProductId)
                if ctx.get('mob_stock_action_val') == "qoh":
                    productQuantity = product_obj.qty_available - product_obj.outgoing_qty
                else:
                    productQuantity = product_obj.virtual_available
                self.synch_quantity(
                    mageProductId, productQuantity, instanceObj)

    @api.one
    def synch_quantity(self, mageProductId, productQuantity, instanceObj):
        response = self.update_quantity(
            mageProductId, productQuantity, instanceObj)
        if response[0][0] == 1:
            return True
        else:
            self.env['magento.sync.history'].create(
                {'status': 'no', 'action_on': 'product', 'action': 'c', 'error_message': response[0][1]})

    @api.one
    def update_quantity(self, mageProductId, productQuantity, instanceObj):
        qty = 0
        text = ''
        stock = 0
        session = False
        if mageProductId:
            if not instanceObj.active:
                return [
                    0, ' Connection needs one Active Configuration setting.']
            else:
                url = instanceObj.name + XMLRPC_API
                user = instanceObj.user
                pwd = instanceObj.pwd
                try:
                    server = xmlrpclib.Server(url)
                    session = server.login(user, pwd)
                except xmlrpclib.Fault as e:
                    text = 'Error, %s Magento details are Invalid.' % e
                except IOError as e:
                    text = 'Error, %s.' % e
                except Exception as e:
                    text = 'Error in Magento Connection.'
                if not session:
                    return [0, text]
                else:
                    try:
                        if productQuantity > 0:
                            stock = 1
                        updateData = [
                            mageProductId, {
                                'manage_stock': 1, 'qty': productQuantity, 'is_in_stock': stock}]
                        server.call(
                            session, 'product_stock.update', updateData)
                        return [1, '']
                    except Exception as e:
                        return [
                            0, ' Error in Updating Quantity for Magneto Product Id %s' %
                            mageProductId]
        else:
            return [1, 'Error in Updating Stock, Magento Product Id Not Found!!!']
