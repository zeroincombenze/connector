# flake8: noqa
# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import re
import xmlrpclib

from odoo import api, models


class ProductAttributeLine(models.Model):
    _inherit = "product.attribute.line"

    @api.multi
    def onchange_attribute_set_id(self, setId):
        result = {}
        if setId:
            setObj = self.env["magento.attribute.set"].browse(setId)
            attributeIds = [x.id for x in setObj.attribute_ids]
            result['domain'] = {'attribute_id': [('id', 'in', attributeIds)]}
        return result


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    @api.model
    def check_attribute(self, vals):
        if vals.get('name'):
            attributeObj = self.search(
                [('name', '=ilike', vals['name'])], limit=1)
            return attributeObj
        return False

    @api.model
    def create(self, vals):
        if 'magento' in self._context:
            attributeObj = self.check_attribute(vals)
            if attributeObj:
                return attributeObj
        return super(ProductAttribute, self).create(vals)

    @api.multi
    def unlink(self):
        ctx = dict(self._context or {})
        mapAttrModel = self.env['magento.product.attribute']
        mapAttrValModel = self.env['magento.product.attribute.value']
        connectionObjs = self.env['magento.configure'].search([])
        for connectionObj in connectionObjs:
            domain = [('instance_id', '=', connectionObj.id)]
            ctx['instance_id'] = connectionObj.id
            activeConnection = connectionObj.with_context(
                ctx)._create_connection()
            if activeConnection:
                url = activeConnection[0]
                session = activeConnection[1]
                server = xmlrpclib.Server(url)
            for attrObj in self:
                attrDomain = domain + [('erp_id', '=', attrObj.id)]
                mapAttrObjs = mapAttrModel.search(attrDomain)
                if mapAttrObjs:
                    mapAttrObjs[0].with_context(ctx).unlink()
                    for attrValId in attrObj.value_ids.ids:
                        attrValDomain = domain + [('erp_id', '=', attrValId)]
                        mapAttrValObjs = mapAttrValModel.search(attrValDomain)
                        if mapAttrValObjs:
                            mapAttrValObjs[0].with_context(ctx).unlink()
                            if activeConnection:
                                try:
                                    server.call(
                                        session, 'magerpsync.attribute_value_map_delete', [attrValId])
                                except Exception as e:
                                    pass
                    if activeConnection:
                        try:
                            server.call(
                                session, 'magerpsync.attribute_map_delete', [
                                    attrObj.id])
                        except Exception as e:
                            pass
        return super(ProductAttribute, self).unlink()


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    @api.model
    def create(self, vals):
        if 'magento' in self._context:
            attributeValueObjs = self.search([('name', '=', vals.get(
                'name')), ('attribute_id', '=', vals.get('attribute_id'))])
            if attributeValueObjs:
                return attributeValueObjs[0]
        return super(ProductAttributeValue, self).create(vals)

    @api.multi
    def unlink(self):
        ctx = dict(self._context or {})
        connectionObjs = self.env['magento.configure'].search([])
        mapAttrValModel = self.env['magento.product.attribute.value']
        for connectionObj in connectionObjs:
            ctx['instance_id'] = connectionObj.id
            domain = [('instance_id', '=', connectionObj.id)]
            activeConnection = connectionObj.with_context(
                ctx)._create_connection()
            for attrValObj in self:
                attrValDomain = domain + [('erp_id', '=', attrValObj.id)]
                mapAttrValObjs = mapAttrValModel.search(attrValDomain)
                if mapAttrValObjs:
                    mapAttrValObjs[0].with_context(ctx).unlink()
                    if activeConnection:
                        url = activeConnection[0]
                        session = activeConnection[1]
                        server = xmlrpclib.Server(url)
                        try:
                            server.call(
                                session, 'magerpsync.attribute_value_map_delete', [
                                    attrValObj.id])
                        except Exception as e:
                            pass
                return super(ProductAttributeValue, self).unlink()
