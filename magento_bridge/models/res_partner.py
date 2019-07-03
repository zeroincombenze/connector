# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, models


def _unescape(text):
    ##
    # Replaces all encoded characters by urlib with plain utf8 string.
    #
    # @param text source text.
    # @return The plain text.
    from urllib import unquote_plus
    try:
        text = unquote_plus(text.encode('utf8'))
        return text
    except Exception as e:
        return text


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        if 'magento' in self._context:
            vals = self.customer_array(vals)
        return super(ResPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'magento' in self._context:
            vals = self.customer_array(vals)
        return super(ResPartner, self).write(vals)

    def customer_array(self, data):
        dic = {}
        stateModel = self.env['res.country.state']
        if 'country_code' in data:
            countryObjs = self.env['res.country'].search(
                [('code', '=', data.get('country_code'))])
            data.pop('country_code')
            if countryObjs:
                data['country_id'] = countryObjs[0].id
                if 'region' in data and data['region']:
                    region = _unescape(data.get('region'))
                    stateObjs = stateModel.search([('name', '=', region)])
                    if stateObjs:
                        data['state_id'] = stateObjs[0].id
                    else:
                        dic['name'] = region
                        dic['country_id'] = countryObjs[0].id
                        code = region[:3].upper()
                        temp = code
                        stateObjs = stateModel.search(
                            [('code', '=ilike', code)])
                        counter = 0
                        while stateObjs:
                            code = temp + str(counter)
                            stateObjs = stateModel.search(
                                [('code', '=ilike', code)])
                            counter = counter + 1
                        dic['code'] = code
                        stateObj = stateModel.create(dic)
                        data['state_id'] = stateObj.id
                    data.pop('region')
        if 'tag' in data:
            tag = _unescape(data.get('tag'))
            tagObjs = self.env['res.partner.category'].search(
                [('name', '=', tag)], limit=1)
            if not tagObjs:
                tagId = self.env['res.partner.category'].create({'name': tag})
            else:
                tagId = tagObjs[0].id
            data['category_id'] = [(6, 0, [tagId])]
            data.pop('tag')
        if 'mage_customer_id' in data:
            data.pop('mage_customer_id')
        if data.get('wk_company'):
            data['wk_company'] = _unescape(data['wk_company'])
        if data.get('name'):
            data['name'] = _unescape(data['name'])
        if data.get('email'):
            data['email'] = _unescape(data['email'])
        if data.get('street'):
            data['street'] = _unescape(data['street'])
        if data.get('street2'):
            data['street2'] = _unescape(data['street2'])
        if data.get('city'):
            data['city'] = _unescape(data['city'])
        return data
