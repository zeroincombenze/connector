# flake8: noqa - pylint: skip-file
# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import binascii
import logging
import xmlrpclib

import requests

from odoo import _, api, fields, models
from res_partner import _unescape
_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, vals):
        mageId = 0
        attrValIds = []
        ctx = dict(self._context or {})
        instanceId = ctx.get('instance_id')
        mapTempModel = self.env['magento.product.template']
        if 'magento' in ctx:
            vals, attrValIds, mageId = self.update_vals(vals, instanceId, True)
        productObj = super(ProductProduct, self).create(vals)
        if ctx.get('magento'):
            attrValModel = self.env['product.attribute.value']
            attrLineModel = self.env['product.attribute.line']
            templateId = productObj.product_tmpl_id.id
            if templateId:
                mappDict = {
                    'mag_product_id' : mageId,
                    'instance_id' : instanceId,
                    'created_by' : 'Magento',
                }
                domain = [('product_tmpl_id', '=', templateId)]
                for attrValId in attrValIds:
                    attrId = attrValModel.browse(attrValId).attribute_id.id
                    searchDomain = domain + [('attribute_id', '=', attrId)]
                    attrLineObjs = attrLineModel.search(searchDomain)
                    for attrLineObj in attrLineObjs:
                        attrLineObj.value_ids = [(4, attrValId)]
                if mageId:
                    mapTempObjs = self.env['magento.product.template'].search(
                        [('erp_template_id', '=', templateId), ('instance_id', '=', instanceId)])
                    if not mapTempObjs:
                        price = vals.get('list_price', 0)
                        mapTempDict = mappDict.copy()
                        mapTempDict.pop('mag_product_id', None)
                        mapTempDict.update({
                            'template_name' : templateId,
                            'erp_template_id' : templateId,
                            'mage_product_id' : mageId,
                            'base_price' : price,
                        })
                        mapTempModel.create(mapTempDict)
                    else:
                        mapTempObjs.need_sync = 'No'
                    mappDict.update({
                        'pro_name' : productObj.id,
                        'oe_product_id' : productObj.id
                    })
                    self.env['magento.product'].create(mappDict)

        return productObj

    @api.multi
    def write(self, vals):
        ctx = dict(self._context or {})
        instanceId = ctx.get('instance_id', False)
        tempModel = self.env['product.template']
        mapProdModel = self.env['magento.product']
        mapTempModel = self.env['magento.product.template']
        unlinkTemplateObj, stockMoveLines = False, False
        if 'magento' in ctx:
            if 'product_tmpl_id' in vals:
                configProdId = vals['product_tmpl_id']
                tempObj = self[0].product_tmpl_id
                if tempObj.id != configProdId:
                    vals['product_tmpl_id'] = configProdId
                    unlinkTemplateObj = tempObj
                    stockMoveLines = self[0].stock_move_ids
            vals, attrValIds, mageId = self.update_vals(vals, instanceId)
        for prodObj in self:
            mapObjs, tempMapObjs = [], []
            mapObjs = mapProdModel.search([('pro_name', '=', prodObj.id)])
            for mappedObj in mapObjs:
                if instanceId and mappedObj.instance_id.id == instanceId:
                    mappedObj.need_sync = "No"
                else:
                    mappedObj.need_sync = "Yes"
            templateId = prodObj.product_tmpl_id.id
            tempMapObjs = mapTempModel.search(
                [('template_name', '=', templateId)])
            for tempMapObj in tempMapObjs:
                if instanceId and tempMapObj.instance_id.id == instanceId:
                    tempMapObj.need_sync = "No"
                else:
                    tempMapObj.need_sync = "Yes"
        res = super(ProductProduct, self).write(vals)
        if unlinkTemplateObj:
            if stockMoveLines:
                unlinkTemplateObj.active = False
            else:
                test = unlinkTemplateObj.unlink()

        return res

    def update_vals(self, vals, instanceId, create=False):
        attrValIds = []
        mageId = 0
        if vals.get('default_code'):
            vals['default_code'] = _unescape(vals['default_code'])
        if 'category_ids' in vals and vals.get('category_ids'):
            categIds = list(set(vals.get('category_ids')))
            defaultCategObj = self.env["magento.configure"].browse(
                instanceId).category
            if defaultCategObj and create:
                vals['categ_id'] = defaultCategObj.id
            vals['categ_ids'] = [(6, 0, categIds)]
            vals.pop('category_ids')
        if 'value_ids' in vals:
            attrValIds = vals.get('value_ids')
            vals['attribute_value_ids'] = [(6, 0, attrValIds)]
            vals.pop('value_ids')
        if 'mage_id' in vals:
            mageId = vals.get('mage_id')
            vals.pop('mage_id')
        if vals.get('image_url'):
            imageUrl = vals.get('image_url')
            proImage = binascii.b2a_base64(str(requests.get(imageUrl).content))
            vals['image'] = proImage
            vals['image_variant'] = proImage
            vals.pop('image_url')
        return [vals, attrValIds, mageId]


class ProductCategory(models.Model):
    _inherit = 'product.category'

    @api.multi
    def write(self, vals):
        if 'magento' in self._context:
            if vals.get('name'):
                vals['name'] = _unescape(vals['name'])
        else:
            categModel = self.env['magento.category']
            for catObj in self:
                mapObjs = categModel.search(
                    [('oe_category_id', '=', catObj.id)])
                for mapObj in mapObjs:
                    mapObjs.need_sync = "Yes"
        return super(ProductCategory, self).write(vals)

    @api.multi
    def unlink(self):
        ctx = dict(self._context or {})
        mapCategModel = self.env['magento.category']
        connectionObjs = self.env['magento.configure'].search([])
        for connectionObj in connectionObjs:
            ctx['instance_id'] = connectionObj.id
            domain = [('instance_id', '=', connectionObj.id)]
            activeConnection = connectionObj.with_context(
                ctx)._create_connection()
            if activeConnection:
                url = activeConnection[0]
                session = activeConnection[1]
                server = xmlrpclib.Server(url)
            for categObj in self:
                categDomain = domain + [('oe_category_id', '=', categObj.id)]
                mapCategObjs = mapCategModel.search(categDomain)
                if mapCategObjs:
                    mapCategObjs[0].with_context(ctx).unlink()
                    childCatIds = categObj.child_id.ids
                    childCatDomain = domain + \
                        [('oe_category_id', 'in', childCatIds)]
                    mapChildCategObjs = mapCategModel.search(childCatDomain)
                    if mapChildCategObjs:
                        mapChildCategObjs.with_context(ctx).unlink()
                    if activeConnection:
                        try:
                            _logger.debug(
                                "MOB: Category ids for which Magento mapping is going to delete: %r ",
                                childCatIds + [
                                    categObj.id])
                            server.call(session,
                                        'magerpsync.category_map_delete',
                                        [childCatIds + [categObj.id]])
                        except Exception as e:
                            pass
        return super(ProductCategory, self).unlink()
