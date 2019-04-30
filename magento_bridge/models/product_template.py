# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import binascii
import xmlrpclib

import requests

from odoo import api, fields, models
from res_partner import _unescape

XMLRPC_API = '/index.php/api/xmlrpc'


class ProductTemplate(models.Model):
    _inherit = "product.template"

    prod_type = fields.Char(string='Magento Type')
    categ_ids = fields.Many2many(
        'product.category',
        'product_categ_rel',
        'product_id',
        'categ_id',
        string='Extra Categories')
    attribute_set_id = fields.Many2one(
        'magento.attribute.set',
        string='Magento Attribute Set',
        help="Magento Attribute Set, Used during configurable product generation at Magento.")

    @api.model
    def create(self, vals):
        mage_id = 0
        ctx = dict(self._context or {})
        if 'magento' in ctx:
            vals, mageId = self.update_vals(vals, True)
        prodTempObj = super(ProductTemplate, self).create(vals)
        if 'magento' in ctx and 'configurable' in ctx:
            mappingData = {
                'template_name' : prodTempObj.id,
                'erp_template_id' : prodTempObj.id,
                'mage_product_id' : mageId,
                'base_price' : vals['list_price'],
                'is_variants' : True,
                'instance_id' : ctx.get('instance_id'),
                'created_by' : 'Magento'
            }
            self.env['magento.product.template'].create(mappingData)
        return prodTempObj

    @api.multi
    def write(self, vals):
        ctx = dict(self._context or {})
        instanceId = ctx.get('instance_id', False)
        if 'magento' in ctx:
            vals, mageId = self.update_vals(vals)
        mapTempModel = self.env['magento.product.template']
        for tempObj in self:
            tempMapObjs = mapTempModel.search(
                [('template_name', '=', tempObj.id)])
            for tempMapObj in tempMapObjs:
                if instanceId and tempMapObj.instance_id.id == instanceId:
                    tempMapObj.need_sync = 'No'
                else:
                    tempMapObj.need_sync = 'Yes'
        return super(ProductTemplate, self).write(vals)

    def update_vals(self, vals, create=False):
        mageId = 0
        if vals.get('name'):
            vals['name'] = _unescape(vals['name'])
        if vals.get('description'):
            vals['description'] = _unescape(vals['description'])
        if vals.get('description_sale'):
            vals['description_sale'] = _unescape(vals['description_sale'])
        if 'category_ids' in vals:
            categIds = list(set(vals.get('category_ids')))
            defaultCategObj = self.env["magento.configure"].browse(
                self._context['instance_id']).category
            if defaultCategObj and create:
                vals['categ_id'] = defaultCategObj.id
            vals['categ_ids'] = [(6, 0, categIds)]
            vals.pop('category_ids')
        if 'mage_id' in vals:
            mageId = vals.get('mage_id')
            vals.pop('mage_id')
        if 'attribute_list' in vals:
            vals.pop('attribute_list')
        if vals.get('image_url'):
            imageUrl = vals.get('image_url')
            proImage = binascii.b2a_base64(str(requests.get(imageUrl).content))
            vals['image'] = proImage
            vals['image_variant'] = proImage
            vals.pop('image_url')
        return [vals, mageId]

    @api.multi
    def unlink(self):
        ctx = dict(self._context or {})
        mapTempModel = self.env['magento.product.template']
        mapProdModel = self.env['magento.product']
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
            for tempObj in self:
                tempDomain = domain + [('erp_template_id', '=', tempObj.id)]
                mapTempObjs = mapTempModel.search(tempDomain)
                if mapTempObjs:
                    mapTempObjs[0].with_context(ctx).unlink()
                    for prodId in tempObj.product_variant_ids.ids:
                        prodSearch = domain + [('oe_product_id', '=', prodId)]
                        mapProdObjs = mapProdModel.search(prodSearch)
                        if mapProdObjs:
                            mapProdObjs[0].with_context(ctx).unlink()
                            if activeConnection:
                                try:
                                    server.call(
                                        session, 'magerpsync.product_map_delete', [prodId])
                                except Exception as e:
                                    pass
                    if tempObj.prod_type == "configurable":
                        if activeConnection:
                            try:
                                server.call(
                                    session, 'magerpsync.template_map_delete', [
                                        tempObj.id])
                            except Exception as e:
                                pass

        return super(ProductTemplate, self).unlink()
