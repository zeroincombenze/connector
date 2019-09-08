# flake8: noqa
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
import logging
_logger = logging.getLogger(__name__)

class MagentoSynchronization(models.TransientModel):
    _inherit = "magento.synchronization"

    @api.model
    def get_sync_template_ids(self, templateIds):
        ctx = dict(self._context or {})
        mappedObj = self.env['magento.product.template'].search(
            [('instance_id', '=', ctx.get('instance_id'))])
        if ctx.get('sync_opr') == 'export':
            mapTemplateIds = mappedObj.mapped('template_name').ids
            notMappedTempltIds = list(set(templateIds) - set(mapTemplateIds))
            return notMappedTempltIds
        if ctx.get('sync_opr') == 'update':
            mappedTempltObjs = mappedObj.filtered(
                lambda obj: obj.need_sync == 'Yes' and
                int(obj.template_name.id) in templateIds)
            return mappedTempltObjs
        return False

    @api.model
    def assign_attribute_Set(self, templateObjs):
        connection = self.env['magento.configure']._create_connection()
        if connection:
            for templateObj in templateObjs:
                attributeLineObjs = templateObj.attribute_line_ids
                setObj = self.get_default_attribute_set()
                if attributeLineObjs:
                    setObj = self.get_magento_attribute_set(
                        attributeLineObjs)
                if setObj:
                    templateObj.write({'attribute_set_id': setObj.id})
                else:
                    return False
        else:
            raise UserError(_("Connection Error!\nError in Odoo Connection"))
        return True

    @api.model
    def get_default_attribute_set(self):
        defaultAttrset = self.env['magento.attribute.set'].search(
            [('set_id', '=', 4), ('instance_id', '=', self._context['instance_id'])])
        if defaultAttrset:
            return defaultAttrset[0]
        else:
            raise UserError(
                _('Information!\nDefault Attribute set not Found, please sync all Attribute set from Magento!!!'))

    @api.model
    def get_magento_attribute_set(self, attributeLineObjs):
        flag = False
        templateAttributeIds = []
        aatrSetModel = self.env['magento.attribute.set']
        for attr in attributeLineObjs:
            templateAttributeIds.append(attr.attribute_id.id)
        attrSetObjs = aatrSetModel.search(
            [('instance_id', '=', self._context['instance_id'])], order="set_id asc")
        for attrSetObj in attrSetObjs:
            setAttributeIds = attrSetObj.attribute_ids.ids
            commonAttributes = sorted(
                set(setAttributeIds) & set(templateAttributeIds))
            templateAttributeIds.sort()
            if commonAttributes == templateAttributeIds:
                return attrSetObj
        return False

    @api.model
    def get_attribute_price_list(self, wkAttrLineObjs, templateId):
        magePriceChanges = []
        prodAttrPriceModel = self.env['product.attribute.price']
        attrValMapModel = self.env['magento.product.attribute.value']

        domain = [('product_tmpl_id', '=', templateId)]
        for attrLineObj in wkAttrLineObjs:
            for valueObj in attrLineObj.value_ids:
                magePriceChangesData = {}
                priceExtra = 0.0
                ##### product template and value extra price ##
                searchDomain = domain + [('value_id', '=', valueObj.id)]
                prodAttrPriceObjs = prodAttrPriceModel.search(searchDomain)
                if prodAttrPriceObjs:
                    priceExtra = prodAttrPriceObjs[0].price_extra
                    magePriceChangesData['price'] = priceExtra
                attrValMapObjs = attrValMapModel.search(
                    [('name', '=', valueObj.id)])
                if attrValMapObjs:
                    mageId = attrValMapObjs[0].mage_id
                    magePriceChangesData['value_id'] = mageId
                magePriceChanges.append(magePriceChangesData)
        return magePriceChanges

    @api.multi
    def export_product_check(self):
        text = text1 = text2 = ''
        updtErrorIds, errorIds = [], []
        successExpIds, successUpdtIds, templateIds = [], [], []
        connection = self.env['magento.configure']._create_connection()
        if connection:
            syncHistoryModel = self.env['magento.sync.history']
            templateModel = self.env['product.template']
            url = connection[0]
            session = connection[1]
            ctx = dict(self._context or {})
            instanceId = ctx['instance_id'] = connection[2]
            domain = [('instance_id', '=', instanceId)]
            if ctx.get('active_model') == "product.template":
                templateIds = self._context.get('active_ids')
            else:
                templateIds = templateModel.search(
                    [('type', '!=', 'service')]).ids
            if not templateIds:
                raise UserError(
                    _('Information!\nNo new product(s) Template found to be Sync.'))

            if ctx.get('sync_opr') == 'export':
                notMappedTemplateIds = self.with_context(
                    ctx).get_sync_template_ids(templateIds)
                if not notMappedTemplateIds:
                    raise UserError(
                        _('Information!\nListed product(s) has been already exported on magento.'))
                connectionObj = self.env[
                    'magento.configure'].browse(instanceId)
                warehouse_id = connectionObj.warehouse_id.id
                ctx['warehouse'] = warehouse_id
                for templateObj in templateModel.with_context(
                        ctx).browse(notMappedTemplateIds):
                    prodType = templateObj.type
                    if prodType == 'service':
                        errorIds.append(templateObj.id)
                        continue
                    expProduct = self.with_context(
                        ctx)._export_specific_template(templateObj, url, session)
                    if expProduct[0] > 0:
                        successExpIds.append(templateObj.id)
                    else:
                        errorIds.append(expProduct[1])
            if ctx.get('sync_opr') == 'update':
                updtMappedTemplateObjs = self.with_context(
                    ctx).get_sync_template_ids(templateIds)
                if not updtMappedTemplateObjs:
                    raise UserError(
                        _('Information!\nListed product(s) has been already updated on magento.'))
                for mappedTempObj in updtMappedTemplateObjs:
                    prodUpdate = self.with_context(ctx)._update_specific_product_template(
                        mappedTempObj, url, session)
                    if prodUpdate[0] > 0:
                        successUpdtIds.append(prodUpdate[1])
                    else:
                        updtErrorIds.append(prodUpdate[1])
            if successExpIds:
                text = "\nThe Listed product(s) %s successfully created on Magento." % (
                    successExpIds)
            if errorIds:
                text += '\nThe Listed Product(s) %s does not synchronized on magento.' % errorIds
            if text:
                syncHistoryModel.create(
                    {'status': 'yes', 'action_on': 'product', 'action': 'b', 'error_message': text})
            if successUpdtIds:
                text1 = '\nThe Listed Product(s) %s has been successfully updated to Magento. \n' % successUpdtIds
                syncHistoryModel.create(
                    {'status': 'yes', 'action_on': 'product', 'action': 'c', 'error_message': text1})
            if updtErrorIds:
                text2 = '\nThe Listed Product(s) %s does not updated on magento.' % updtErrorIds
                syncHistoryModel.create(
                    {'status': 'no', 'action_on': 'product', 'action': 'c', 'error_message': text2})
            dispMsz = text + text1 + text2
            return self.display_message(dispMsz)
    #############################################
    ##          Specific template sync         ##
    #############################################

    def _export_specific_template(self, templateObj, url, session):
        if templateObj:
            mageSetId = 0
            ctx = dict(self._context or {})
            instanceId = ctx.get('instance_id')
            getProductData = {}
            magePriceChanges = {}
            mageAttributeIds = []
            mapTmplModel = self.env['magento.product.template']
            attrPriceModel = self.env['product.attribute.price']
            templateId = templateObj.id
            templateSku = templateObj.default_code or 'Template Ref %s' % templateId
            if not templateObj.product_variant_ids:
                return [-2, str(templateId) + ' No Variant Ids Found!!!']
            else:
                if not templateObj.attribute_set_id.id:
                    res = self.assign_attribute_Set([templateObj])
                    if not res:
                        return [-1, str(templateId) +
                                ' Attribute Set Name not matched with attributes!!!']

                attrSetObj = templateObj.attribute_set_id
                attrSetObj = self.with_context(
                    ctx)._check_valid_attribute_set(attrSetObj, templateId)
                wkAttrLineObjs = templateObj.attribute_line_ids
                if not wkAttrLineObjs:
                    templateSku = 'single_variant'
                    magProdId = self.with_context(ctx)._sync_template_variants(
                        templateObj, templateSku, url, session)
                    name = templateObj.name
                    price = templateObj.list_price or 0.0
                    if magProdId:
                        odooMapData = {
                            'template_name' : templateId,
                            'erp_template_id' : templateId,
                            'mage_product_id' : magProdId[0],
                            'base_price' : price,
                            'is_variants' : False,
                            'instance_id' : instanceId
                        }
                        mapTmplModel.with_context(ctx).create(odooMapData)
                        return [1, magProdId[0]]
                    else:
                        return [0, templateId]
                else:
                    checkAttribute = self.with_context(
                        ctx)._check_attribute_with_set(attrSetObj, wkAttrLineObjs)
                    if checkAttribute[0] == -1:
                        return checkAttribute
                    mageSetId = templateObj.attribute_set_id.set_id
                    if not mageSetId:
                        return [-3, str(templateId) +
                                ' Attribute Set Name not found!!!']
                    else:
                        for attrLineObj in wkAttrLineObjs:
                            mageAttrIds = self.with_context(
                                ctx)._check_attribute_sync(attrLineObj)
                            if not mageAttrIds:
                                return [-1, str(templateId) +
                                        ' Attribute not syned at magento!!!']
                            mageAttributeIds.append(mageAttrIds[0])
                            getProductData[
                                'configurable_attributes'] = mageAttributeIds
                            attrName = attrLineObj.attribute_id.name.lower(
                            ).replace(" ", "_").replace("-", "_")[:29]
                            attrMappingObj = self.env['magento.product.attribute'].search(
                                [('name', '=', attrLineObj.attribute_id.id)])
                            if attrMappingObj:
                                attrName = attrMappingObj.mage_attribute_code
                            valDict = self.with_context(ctx)._search_single_values(
                                templateId, attrLineObj.attribute_id.id)
                            if valDict:
                                ctx.update(valDict)
                            domain = [('product_tmpl_id', '=', templateId)]
                            for valueObj in attrLineObj.value_ids:
                                priceExtra = 0.0
                                ##### product template and value extra price ##
                                searchDomain = domain + \
                                    [('value_id', '=', valueObj.id)]
                                attrPriceObjs = attrPriceModel.with_context(
                                    ctx).search(searchDomain)
                                if attrPriceObjs:
                                    priceExtra = attrPriceObjs[0].price_extra
                                valueName = valueObj.name
                                if attrName in magePriceChanges:
                                    magePriceChanges[attrName].update(
                                        {valueName: priceExtra})
                                else:
                                    magePriceChanges[attrName] = {
                                        valueName: priceExtra}
                        mageProdIds = self.with_context(ctx)._sync_template_variants(
                            templateObj, templateSku, url, session)
                        getProductData.update({
                            'associated_product_ids' : mageProdIds,
                            'price_changes' : magePriceChanges,
                            'visibility' : 4,
                            'price' : templateObj.list_price or 0.00,
                            'tax_class_id' : '0'
                        })
                        getProductData = self.with_context(ctx)._get_product_array(
                            url, session, templateObj, getProductData)
                        stockData = self._get_product_qty(templateObj)
                        stockData.pop('qty', 0)
                        getProductData.update(stock_data=stockData)
                        getProductData['websites'] = [1]
                        templateSku = 'Template sku %s' % templateId
                        templateObj.write({'prod_type': 'configurable'})
                        newProdData = [
                            'configurable',
                            mageSetId,
                            templateSku,
                            getProductData,
                            templateId]
                        try:
                            magProdId = self.server_call(
                                session, url, 'magerpsync.product_create', newProdData)
                        except xmlrpclib.Fault as e:
                            return [0, str(templateId) + ': ' + str(e)]
                        if magProdId[0] > 0:
                            odooMapData = {
                                'template_name' : templateId,
                                'erp_template_id' : templateId,
                                'mage_product_id' : magProdId[1],
                                'base_price' : getProductData['price'],
                                'is_variants' : True,
                                'instance_id' : instanceId
                            }
                            mapTmplModel.with_context(ctx).create(odooMapData)
                            try:
                                attributeLineData = self.get_attribute_price_list(
                                    templateObj.attribute_line_ids, templateId)
                                if attributeLineData:
                                    self.server_call(
                                        session, url, 'magerpsync.product_super_attribute', [
                                            magProdId[1], attributeLineData])
                            except xmlrpclib.Fault as e:
                                _logger.debug('super attribute did not updated')
                            return magProdId
                        else:
                            return [
                                0, str(templateId) + "Not Created at magento"]
        else:
            return [0, 'Not Template']

    def _check_valid_attribute_set(self, attrSetObj, templateId):
        ctx = dict(self._context or {})
        instanceId = ctx.get('instance_id')
        if instanceId and instanceId == attrSetObj.instance_id.id:
            return attrSetObj
        return False

    ############# sync template variants ########
    def _sync_template_variants(self, templateObj, templateSku, url, session):
        mageVariantIds = []
        mapProdModel = self.env['magento.product']
        ctx = dict(self._context or {})
        instanceId = ctx.get('instance_id')
        domain = [('instance_id', '=', instanceId)]
        for vrntObj in templateObj.product_variant_ids:
            searchDomain = domain + [('pro_name', '=', vrntObj.id)]
            existMapObjs = mapProdModel.search(searchDomain)
            if existMapObjs:
                mageVariantIds.append(existMapObjs[0].mag_product_id)
            else:
                mageVrntId = self._export_specific_product(
                    vrntObj, templateSku, url, session)
                if mageVrntId[0] > 0 and mageVrntId[1]:
                    mageVariantIds.append(mageVrntId[1])
        return mageVariantIds

    ############# check single attribute lines ########
    def _search_single_values(self, templId, attrId):
        dic = {}
        attrLineModel = self.env['product.attribute.line']
        attrLineObjs = attrLineModel.search(
            [('product_tmpl_id', '=', templId), ('attribute_id', '=', attrId)])
        if attrLineObjs:
            attrLineObj = attrLineObjs[0]
            if len(attrLineObj.value_ids) == 1:
                dic[attrLineObj.attribute_id.name] = attrLineObj.value_ids.name
        return dic

    ############# check attributes lines and set attributes are same ########
    def _check_attribute_with_set(self, attrSetObj, attrLineObjs):
        setAttrObjs = attrSetObj.attribute_ids
        if not setAttrObjs:
            return [-1, str(attrSetObj.name) +
                    ' Attribute Set Name has no attributes!!!']
        setAttrList = list(setAttrObjs.ids)
        for attrLineObj in attrLineObjs:
            if attrLineObj.attribute_id.id not in setAttrList:
                return [-1, str(attrSetObj.name) +
                        ' Attribute Set Name not matched with attributes!!!']
        return [1, '']

    ############# check attributes syned return mage attribute ids ########
    def _check_attribute_sync(self, attrLineObj):
        mapAttrModel = self.env['magento.product.attribute']
        mageAttributeIds = []
        magAttrObjs = mapAttrModel.search(
            [('name', '=', attrLineObj.attribute_id.id)])
        if magAttrObjs:
            mageAttributeIds.append(magAttrObjs[0].mage_id)
        return mageAttributeIds

    ############# fetch product details ########
    def _get_product_array(self, url, session, prodObj, getProductData):
        prodCategs = []
        for categobj in prodObj.categ_ids:
            mageCategId = self.sync_categories(url, session, categobj)
            if mageCategId:
                prodCategs.append(mageCategId)
        if prodObj.categ_id.id:
            mageCategId = self.sync_categories(
                url, session, prodObj.categ_id)
            if mageCategId:
                prodCategs.append(mageCategId)
        status = 2
        if prodObj.sale_ok:
            status = 1
        getProductData.update({
            'name' : prodObj.name,
            'short_description' : prodObj.description_sale or ' ',
            'description' : prodObj.description or ' ',
            'weight' : prodObj.weight or 0.00,
            'categories' : prodCategs,
            'cost' : prodObj.standard_price,
            'ean' : prodObj.barcode,
            'status' : status,
        })
        if prodObj.image:
            mediaData = self._get_product_media(prodObj)
            getProductData.update({
                'image_data' : mediaData
            })
        return getProductData

    def _get_product_qty(self, prodObj):
        mobStockAction = self.env['ir.values'].sudo().get_default(
            'mob.config.settings', 'mob_stock_action', False)
        productQty, stock = 0, 0
        if mobStockAction and mobStockAction == "qoh":
            productQty = prodObj.qty_available - prodObj.outgoing_qty
        else:
            productQty = prodObj.virtual_available
        if productQty:
            stock = 1
        stockData = {
            'manage_stock': 1,
            'qty': productQty,
            'is_in_stock': stock}
        return stockData

    def _get_product_media(self, prodObj):
        imageDict = {
            'content' : prodObj.image,
            'mime' : 'image/jpeg'
        }
        return imageDict

    #############################################
    ##          Specific product sync          ##
    #############################################
    def _export_specific_product(self, vrntObj, templateSku, url, session):
        """
        @param code: product Id.
        @param context: A standard dictionary
        @return: list
        """
        getProductData = {}
        priceExtra = 0
        prodAttrPriceModel = self.env['product.attribute.price']
        magProdAttrModel = self.env['magento.product.attribute']
        domain = [('product_tmpl_id', '=', vrntObj.product_tmpl_id.id)]
        if vrntObj:
            sku = vrntObj.default_code or 'Ref %s' % vrntObj.id
            prodVisibility = 1
            if templateSku == "single_variant":
                prodVisibility = 4
            crrntSetName = vrntObj.product_tmpl_id.attribute_set_id.name
            getProductData = {
                'currentsetname' : crrntSetName,
                'visibility' : prodVisibility
            }
            if vrntObj.attribute_value_ids:
                for valueObj in vrntObj.attribute_value_ids:
                    attrDomain = [('name', '=', valueObj.attribute_id.id)]
                    attrName = magProdAttrModel.search(
                        attrDomain, limit=1).mage_attribute_code or False
                    valueName = valueObj.name
                    getProductData[attrName] = valueName
                    searchDomain = domain + [('value_id', '=', valueObj.id)]
                    attrValPriceObj = prodAttrPriceModel.search(searchDomain)
                    if attrValPriceObj:
                        priceExtra += attrValPriceObj[0].price_extra

            getProductData['price'] = vrntObj.list_price + \
                priceExtra or 0.00
            getProductData = self._get_product_array(
                url, session, vrntObj, getProductData)
            stockData = self._get_product_qty(vrntObj)
            getProductData.update({'stock_data' : stockData})
            getProductData.update({
                'websites' : [1],
                'tax_class_id' : '0'
            })
            if vrntObj.type in ['product', 'consu']:
                prodtype = 'simple'
            else:
                prodtype = 'virtual'
            vrntObj.write({'prod_type': prodtype, 'default_code': sku})
            magProd = self.prodcreate(url, session, vrntObj,
                                      prodtype, sku, getProductData)
            return magProd

    #############################################
    ##          single products create         ##
    #############################################

    def prodcreate(
            self,
            url,
            session,
            vrntObj,
            prodtype,
            prodsku,
            getProductData):
        ctx = dict(self._context or {})
        stock = 0
        quantity = 0
        odooProdId = vrntObj.id
        if getProductData['currentsetname']:
            currentSet = getProductData['currentsetname']
        else:
            currset = self.server_call(
                session, url, 'product_attribute_set.list')
            currentSet = ""
            if currset[0] > 0:
                currentSet = currset[1].get('set_id')
        expProdData = [
            prodtype,
            currentSet,
            prodsku,
            getProductData,
            odooProdId]
        try:
            magProd = self.server_call(
                session, url, 'magerpsync.product_create', expProdData)
        except xmlrpclib.Fault as e:
            return [0, str(odooProdId) + ':' + str(e)]
        if magProd[0] > 0 and magProd[1]:
            odooMapData = {
                'pro_name' : odooProdId,
                'oe_product_id' : odooProdId,
                'mag_product_id' : magProd[1],
                'instance_id' : ctx.get('instance_id')
            }
            self.env['magento.product'].create(odooMapData)
        return magProd

    #############################################
    ##      update specific product template   ##
    #############################################
    def _update_specific_product_template(self, mappedObj, url, session):
        ctx = dict(self._context or {})
        getProductData = {}
        tempObj = mappedObj.template_name
        magProdIds = []
        mageProdId = mappedObj.mage_product_id
        mapProdModel = self.env['magento.product']
        domain = [('instance_id', '=', ctx.get('instance_id'))]
        if tempObj and mageProdId:
            if tempObj.product_variant_ids:
                templateSku = tempObj.default_code or 'Template Ref %s' % tempObj.id
                magProdIds = self._sync_template_variants(
                    tempObj, templateSku, url, session)
                for vrntObj in tempObj.product_variant_ids:
                    searchDomain = domain + [('pro_name', '=', vrntObj.id)]
                    prodMapObjs = mapProdModel.search(searchDomain)
                    if prodMapObjs:
                        updtProdIds = self._update_specific_product(
                            prodMapObjs[0], url, session)
            else:
                return [-1, str(tempObj.id) + ' No Variant Ids Found!!!']
            if mappedObj.is_variants and magProdIds:
                getProductData['price'] = tempObj.list_price or 0.00
                getProductData = self._get_product_array(
                    url, session, tempObj, getProductData)
                getProductData['associated_product_ids'] = magProdIds
                updateData = [mageProdId, getProductData]
                try:
                    magProd = self.server_call(
                        session, url, 'magerpsync.product_update', updateData)
                except xmlrpclib.Fault as e:
                    return [0, str(tempObj.id) + str(e)]
            attributeLineData = self.get_attribute_price_list(
                tempObj.attribute_line_ids, tempObj.id)
            if attributeLineData:
                self.server_call(
                    session, url, 'magerpsync.product_super_attribute', [
                        mageProdId, attributeLineData])
            mappedObj.need_sync = 'No'
            return [1, tempObj.id]

    #############################################
    ##          update specific product        ##
    #############################################
    def _update_specific_product(self, prodMapObj, url, session):
        getProductData = {}
        prodObj = prodMapObj.pro_name
        mageProdId = prodMapObj.mag_product_id
        instanceObj = prodMapObj.instance_id
        attrPriceModel = self.env['product.attribute.price']
        domain = [('product_tmpl_id', '=', prodObj.product_tmpl_id.id)]
        if prodObj and mageProdId:
            priceExtra = 0
            if prodObj.attribute_value_ids:
                for value_id in prodObj.attribute_value_ids:
                    getProductData[
                        value_id.attribute_id.name] = value_id.name
                    searchDomain = domain + [('value_id', '=', value_id.id)]
                    attrPriceObjs = attrPriceModel.search(searchDomain)
                    if attrPriceObjs:
                        priceExtra += attrPriceObjs[0].price_extra
            getProductData['price'] = prodObj.list_price + \
                priceExtra or 0.00
            getProductData = self._get_product_array(
                url, session, prodObj, getProductData)
            if instanceObj.inventory_sync == 'enable':
                stockData = self._get_product_qty(prodObj)
                getProductData.update({'stock_data' : stockData})
            updateData = [mageProdId, getProductData]
            try:
                magProd = self.server_call(
                    session, url, 'magerpsync.product_update', updateData)
            except xmlrpclib.Fault as e:
                return [0, str(prodObj.id) + str(e)]
            prodMapObj.need_sync = 'No'
            return [1, prodObj.id]
