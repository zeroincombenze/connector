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
from odoo.exceptions import UserError

XMLRPC_API = '/index.php/api/xmlrpc'


class MagentoSynchronization(models.TransientModel):
    _inherit = "magento.synchronization"

    #############################################
    ##   Export Attributes and values          ##
    #############################################

    @api.multi
    def export_attributes_and_their_values(self):
        mapArray = []
        mapDict = {}
        displayMessage = ''
        attributeCount = 0
        attributeModel = self.env['product.attribute']
        attributeMappingModel = self.env['magento.product.attribute']
        valueMappingModel = self.env['magento.product.attribute.value']
        connection = self.env['magento.configure']._create_connection()
        if connection:
            url = connection[0]
            session = connection[1]
            ctx = dict(self._context or {})
            ctx['instance_id'] = instance_id = connection[2]
            attributeMapObjs = attributeMappingModel.with_context(
                ctx).search([('instance_id', '=', instance_id)])
            for attributeMapObj in attributeMapObjs:
                mapArray.append(attributeMapObj.erp_id)
                mapList = [
                    attributeMapObj.mage_id,
                    attributeMapObj.mage_attribute_code
                    ]
                mapDict.update(
                    {attributeMapObj.erp_id: mapList})
            attributeObjs = attributeModel.search([])
            if attributeObjs:
                for attributeObj in attributeObjs:
                    if attributeObj.id not in mapArray:
                        name = attributeObj.name
                        label = attributeObj.name
                        attributeResponse = self.with_context(ctx).create_product_attribute(
                            url, session, attributeObj.id, name, label)
                    else:
                        mapListInfo = mapDict.get(attributeObj.id)
                        mageId = mapListInfo[0]
                        attrCode = mapListInfo[1]
                        attributeResponse = [1, int(mageId), attrCode]
                    if attributeResponse[0] == 0:
                        displayMessage = displayMessage + attributeResponse[1]
                    if attributeResponse[0] > 0:
                        mageId = attributeResponse[1]
                        for valueObj in attributeObj.value_ids:
                            if not valueMappingModel.with_context(ctx).search(
                                    [('erp_id', '=', valueObj.id), ('instance_id', '=', instance_id)]):
                                name = valueObj.name
                                position = valueObj.sequence
                                attributeCode = attributeResponse[2]
                                ctx.update({'attribute_code' : attributeCode})
                                valueResponse = self.with_context(ctx).create_attribute_value(
                                    url, session, valueObj.id, name, position)
                                if valueResponse[0] == 0:
                                    displayMessage = displayMessage + \
                                        valueResponse[1]
                        attributeCount += 1
            else:
                displayMessage = "No Attribute(s) Found To Be Export At Magento!!!"
            if attributeCount:
                displayMessage += "\n %s Attribute(s) and their value(s) successfully Synchronized To Magento." % (
                    attributeCount)
            return self.display_message(displayMessage)

    @api.model
    def create_product_attribute(self, url, session, attributeId, name, label):
        name = name.lower().replace(" ", "_").replace("-", "_")[:29]
        name = name.strip()
        ctx = dict(self._context or {})
        instanceId = ctx.get('instance_id')
        if session:
            attrributeDict = {
                'attribute_code' : name,
                'scope' : 'global',
                'frontend_input' : 'select',
                'is_configurable' : 1,
                'is_required' : 1,
                'frontend_label' : [{'store_id': 0, 'label': label}]
            }
            mageAttributeId = 0
            try:
                attrParameter = [attrributeDict, attributeId, 'Odoo']
                mageId = self.server_call(
                    session, url, 'magerpsync.create_attribute', attrParameter)
            except xmlrpclib.Fault as e:
                return [
                    0, '\nError in creating Attribute (Code: %s).%s' %
                    (name, str(e))]
            if mageId[0] > 0:
                mageAttributeId = mageId[1]
                mageId.append(name)
            else:
                attributeData = self.server_call(
                    session, url, 'product_attribute.info', [name])
                if attributeData[0] > 0:
                    mageAttributeId = attributeData[1]['attribute_id']
                    attrCode = attributeData[1]['attribute_code']
                    mageId = [1, mageAttributeId, attrCode]
                else:
                    mageId.append('')
                    return mageId
            erpMapData = {
                'name' : attributeId,
                'erp_id' : attributeId,
                'mage_id' : mageAttributeId,
                'mage_attribute_code' : name,
                'instance_id' : instanceId
            }
            self.env['magento.product.attribute'].create(
                erpMapData)
            return mageId

    @api.model
    def create_attribute_value(
            self,
            url,
            session,
            erpAttrId,
            name,
            position='0'):
        ctx = dict(self._context or {})
        instanceId = ctx.get('instance_id')
        attributeCode = ctx.get('attribute_code')
        if session:
            name = name.strip()
            try:
                attrOPtionParameter = [
                    attributeCode, name, erpAttrId, position, 'Odoo']
                mageId = self.server_call(
                    session,
                    url,
                    'magerpsync.create_attribute_option',
                    attrOPtionParameter)
            except xmlrpclib.Fault as e:
                return [
                    0, ' Error in creating Option( %s ).%s' %
                    (name, str(e))]
            if mageId[0] > 0:
                erpMapData = {
                    "name" : erpAttrId,
                    "erp_id" : erpAttrId,
                    "mage_id" : mageId[1],
                    "instance_id" : instanceId
                }
                self.env['magento.product.attribute.value'].create(
                    erpMapData)
                return mageId
            else:
                return mageId
