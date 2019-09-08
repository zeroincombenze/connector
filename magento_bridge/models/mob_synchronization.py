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

from odoo import api, models


class MagentoSynchronization(models.TransientModel):
    _name = "magento.synchronization"
    _description = "Magento Synchronization"

    @api.multi
    def open_configuration(self):
        connectionId = False
        activeConn = self.env['magento.configure'].search(
            [('active', '=', True)])
        if activeConn:
            connectionId = activeConn[0].id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Configure Magento Api',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'magento.configure',
            'res_id': connectionId,
            'target': 'current',
            'domain': '[]',
        }

    def display_message(self, message):
        wizardObj = self.env['message.wizard'].create({'text': message})
        return {
            'name': ("Information"),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'message.wizard',
            'view_id': self.env.ref('magento_bridge.message_wizard_form1').id,
            'res_id': wizardObj.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
        }

    @api.model
    def sync_attribute_set(self, data):
        ctx = dict(self._context or {})
        odooSetId = 0
        setDict = {}
        res = False
        attrSetModel = self.env['magento.attribute.set']
        if data.get('name'):
            setMapObjs = attrSetModel.search([('name', '=', data.get('name'))])
            if not setMapObjs:
                setDict['name'] = data.get('name')
                if data.get('set_id'):
                    setDict['set_id'] = data.get('set_id')
                setDict['created_by'] = 'Magento'
                setDict['instance_id'] = ctx.get('instance_id')
                odooSetId = attrSetModel.create(setDict)
            else:
                odooSetId = setMapObjs[0]
            if odooSetId:
                if data.get('set_id'):
                    dic = {}
                    dic['set_id'] = data.get('set_id')
                    if data.get('attribute_ids'):
                        dic['attribute_ids'] = [
                            (6, 0, data.get('attribute_ids'))]
                    else:
                        dic['attribute_ids'] = [[5]]
                    if ctx.get('instance_id'):
                        dic['instance_id'] = ctx.get('instance_id')
                    res = odooSetId.write(dic)
        return res

    @api.model
    def server_call(self, session, url, method, params=None):
        if session:
            server = xmlrpclib.Server(url)
            mageId = 0
            try:
                if params is None:
                    mageId = server.call(session, method)
                else:
                    mageId = server.call(session, method, params)
            except xmlrpclib.Fault as e:
                name = ""
                return [0, '\nError in create (Code: %s).%s' % (name, str(e))]
            return [1, mageId]

    def get_mage_region_id(self, url, session, region, countryCode):
        """
        @return magneto region id
        """
        regionModel = self.env['magento.region']
        searchDomain = [('country_code', '=', countryCode)]
        mapObjs = regionModel.search(searchDomain)
        if not mapObjs:
            returnId = self.env['region.wizard']._sync_mage_region(
                url, session, countryCode)
        searchDomain += [('name', '=', region)]
        regionObjs = regionModel.search(searchDomain)
        if regionObjs:
            id = regionObjs[0].mag_region_id
            return id
        else:
            return 0

    @api.multi
    def reset_mapping(self, instanceId=None):
        activeConn = self.env['magento.configure'].search(
            [('active', '=', True)])
        if activeConn:
            instanceId = activeConn[0].id
        domain = [('instance_id', '=', instanceId)]
        message = 'All '
        regionObjs = self.env['magento.region'].search([])
        if regionObjs:
            regionObjs.unlink()
            message += 'region, '
        categObjs = self.env['magento.category'].search(domain)
        if categObjs:
            categObjs.unlink()
            message += 'category, '
        prodAttrObjs = self.env['magento.product.attribute'].search(domain)
        if prodAttrObjs:
            prodAttrObjs.unlink()
            message += 'product attribute, '
        prodAttrValObjs = self.env['magento.product.attribute.value'].search(
            domain)
        if prodAttrValObjs:
            prodAttrValObjs.unlink()
            message += 'attribute value, '
        attrSetObjs = self.env['magento.attribute.set'].search(domain)
        if attrSetObjs:
            attrSetObjs.unlink()
            message += 'attribute set, '
        prodTempObjs = self.env['magento.product.template'].search(domain)
        if prodTempObjs:
            prodTempObjs.unlink()
        prodObjs = self.env['magento.product'].search(domain)
        if prodObjs:
            prodObjs.unlink()
            message += 'product, '
        partnerObjs = self.env['magento.customers'].search(domain)
        if partnerObjs:
            partnerObjs.unlink()
            message += 'customers, '
        orderObjs = self.env['wk.order.mapping'].search(domain)
        if orderObjs:
            orderObjs.unlink()
            message += 'order, '
        historyObjs = self.env['magento.sync.history'].search([])
        if historyObjs:
            historyObjs.unlink()
        if len(message) > 4:
            message += 'mappings has been deleted successfully'
        else:
            message = "No mapping entry exist"
        return self.display_message(message)
# END
