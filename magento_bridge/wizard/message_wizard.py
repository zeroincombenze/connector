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


class MessageWizard(models.TransientModel):
    _name = "message.wizard"

    text = fields.Text(string='Message', readonly=True, translate=True)


class RegionWizard(models.TransientModel):
    _name = "region.wizard"

    country_ids = fields.Many2one('res.country', string='Country')

    @api.model
    def _sync_mage_region(self, url, session, country_code):
        region_data = {}
        state_data = {}
        server = xmlrpclib.Server(url)
        try:
            regions = server.call(session, 'region.list', [country_code])
        except xmlrpclib.Fault as e:
            raise UserError(_('Error %s') % e)
        if regions:
            for i in regions:
                region_data['name'] = i['name']
                region_data['region_code'] = i['code']
                region_data['country_code'] = country_code
                region_data['mag_region_id'] = i['region_id']
                self.env['magento.region'].create(region_data)
                if country_code != 'US':
                    country_ids = self.env['res.country'].search(
                        [('code', '=', country_code)])
                    state_data['name'] = i['name']
                    state_data['country_id'] = country_ids[0].id
                    state_data['code'] = i['name'][:2].upper()
                    self.env['res.country.state'].create(state_data)

            return len(regions)
        else:
            return 0

    @api.one
    def sync_state(self):
        config_obj = self.env['magento.configure'].search(
            [('active', '=', True)])
        if len(config_obj) > 1:
            raise UserError(
                _('Error!\nSorry, only one Active Configuration setting is allowed.'))
        if not config_obj:
            raise UserError(
                _('Error!\nPlease create the configuration part for connection!!!'))
        else:
            url = config_obj.name + '/index.php/api/xmlrpc'
            user = config_obj.user
            pwd = config_obj.pwd
            try:
                server = xmlrpclib.Server(url)
                session = server.login(user, pwd)
            except xmlrpclib.Fault as e:
                raise UserError(_('Error\n %s, Invalid Information') % e)
            except IOError as e:
                raise UserError(_('Error\n %s') % e)
            except Exception as e:
                raise UserError(
                    _('Error!\n Magento Connection in connecting: %s') %
                    e)
            if session:
                country_id = self.country_ids
                country_code = country_id.code
                map_id = self.env['magento.region'].search(
                    [('country_code', '=', country_code)])
                if not map_id:
                    total_regions = self._sync_mage_region(
                        url, session, country_code)
                    if total_regions == 0:
                        raise UserError(
                            _('Error!\n There is no any region exist for country %s.') %
                            (country_id.name))
                        # return {
                        #     'type': 'ir.actions.act_window_close',
                        # }
                    else:
                        text = "%s Region of %s are sucessfully Imported to OpenERP." % (
                            total_regions, country_id.name)
                        partial = self.env[
                            'message.wizard'].create({'text': text})
                        return {'name': _("Message"),
                                'view_mode': 'form',
                                'view_id': False,
                                'view_type': 'form',
                                'res_model': 'message.wizard',
                                'res_id': partial,
                                'type': 'ir.actions.act_window',
                                'nodestroy': True,
                                'target': 'new',
                                'domain': '[]',
                                }
                else:
                    raise UserError(
                        _('Information!\nAll regions of %s are already imported to OpenERP.') %
                        (country_id.name))
