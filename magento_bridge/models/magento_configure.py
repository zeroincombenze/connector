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

from odoo import _, api, fields, models
from odoo.addons.base.res.res_partner import _lang_get
from odoo.exceptions import UserError

XMLRPC_API = '/index.php/api/xmlrpc'


class MagentoConfigure(models.Model):
    _name = "magento.configure"
    _inherit = ['mail.thread']
    _description = "Magento Configuration"
    _rec_name = 'instance_name'

    def _default_instance_name(self):
        return self.env[
            'ir.sequence'].next_by_code('magento.configure')

    def _default_category(self):
        ctx = dict(self._context or {})
        categId = ctx.get('categ_id', False)
        if categId:
            return categId
        try:
            return self.env['ir.model.data'].get_object_reference(
                'product', 'product_category_all')[1]
        except ValueError:
            return False

    def _fetch_magento_store(self, url, session):
        stores = []
        storeInfo = {}
        storeViewModel = self.env['magento.store.view']
        try:
            server = xmlrpclib.Server(url)
            stores = server.call(session, 'store.list')
        except xmlrpclib.Fault as e:
            raise UserError(
                _('Error!\nError While Fetching Magento Stores!!!, %s') % e)
        for store in stores:
            if store['website']['is_default'] == '1':
                storeObj = storeViewModel._get_store_view(store)
                storeInfo.update({
                    'website_id' : int(store['website']['website_id']),
                    'store_id' : storeObj.id,
                })
                break
        return storeInfo

    name = fields.Char(
        string='Base URL',
        track_visibility="onchange",
        required=True,
    )
    instance_name = fields.Char(
        string='Instance Name',
        default=lambda self: self._default_instance_name())
    user = fields.Char(
        string='API User Name',
        track_visibility="onchange",
        required=True)
    pwd = fields.Char(
        string='API Password',
        track_visibility="onchange",
        required=True,
        size=100)
    status = fields.Char(string='Connection Status', readonly=True)
    active = fields.Boolean(
        string="Active",
        track_visibility="onchange",
        default=True)
    connection_status = fields.Boolean(
        string="Connection Status", default=False)
    store_id = fields.Many2one(
        'magento.store.view', string='Default Magento Store')
    group_id = fields.Many2one(
        related="store_id.group_id",
        string="Default Store",
        readonly=True,
        store=True)
    website_id = fields.Many2one(
        related="group_id.website_id",
        string="Default Magento Website",
        readonly=True)
    credential = fields.Boolean(
        string="Show/Hide Credentials Tab",
        default=lambda *a: 1,
        help="If Enable, Credentials tab will be displayed, "
        "And after filling the details you can hide the Tab.")
    notify = fields.Boolean(
        string='Notify Customer By Email',
        default=lambda *a: 1,
        help="If True, customer will be notify"
        "during order shipment and invoice, else it won't.")
    language = fields.Selection(
        _lang_get, string="Default Language", default=api.model(
            lambda self: self.env.lang), help="Selected language is loaded in the system, "
        "all documents related to this contact will be synched in this language.")
    category = fields.Many2one(
        'product.category',
        string="Default Category",
        default=lambda self: self._default_category(),
        help="Selected Category will be set default category for odoo's product, "
        "in case when magento product doesn\'t belongs to any catgeory.")
    state = fields.Selection(
        [
            ('enable',
             'Enable'),
            ('disable',
             'Disable')],
        string='Status',
        default="enable",
        help="status will be consider during order invoice, "
        "order delivery and order cancel, to stop asynchronous process at other end.",
        size=100)
    inventory_sync = fields.Selection(
        [
            ('enable',
             'Enable'),
            ('disable',
             'Disable')],
        string='Inventory Update',
        default="enable",
        help="If Enable, Invetory will Forcely Update During Product Update Operation.",
        size=100)
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        default=lambda self: self.env['sale.order']._default_warehouse_id(),
        help="Used During Inventory Synchronization From Magento to Odoo.")
    location_id = fields.Many2one(
        related='warehouse_id.lot_stock_id', string='Location')
    create_date = fields.Datetime(string='Created Date')
    correct_mapping = fields.Boolean(string='Correct Mapping', default=True)

    @api.model
    def create(self, vals):
        activeConnections = self.search([('active', '=', True)])
        isMultiMobInstalled = False
        if self.env['ir.module.module'].search(
                [('name', '=', 'mob_multi_instance')], limit=1).state == 'installed':
            isMultiMobInstalled = True
        if vals.get('active') and activeConnections and not isMultiMobInstalled:
            raise UserError(
                _('Warning!\nSorry, Only one active connection is allowed.'))
        vals['instance_name'] = self.env[
            'ir.sequence'].next_by_code('magento.configure')
        res = super(MagentoConfigure, self).create(vals)
        self.env['mob.dashboard']._create_dashboard(res)
        return res

    @api.multi
    def write(self, vals):
        activeConnections = self.search([('active', '=', True)])
        isMultiMobInstalled = False
        dashboardModel = self.env['mob.dashboard']
        if self.env['ir.module.module'].search(
                [('name', '=', 'mob_multi_instance')], limit=1).state == 'installed':
            isMultiMobInstalled = True
        if vals:
            if len(activeConnections) > 0 and vals.get(
                    'active') and not isMultiMobInstalled:
                raise UserError(
                    _('Warning!\nSorry, Only one active connection is allowed.'))
            for instanceObj in self:
                if not instanceObj.instance_name:
                    vals['instance_name'] = self.env[
                        'ir.sequence'].next_by_code('magento.configure')
                isDashboardExist = dashboardModel.with_context(
                    active_test=False).search([('instance_id', '=', self.id)])
                if not isDashboardExist:
                    dashboardModel._create_dashboard(instanceObj)
        return super(MagentoConfigure, self).write(vals)

    @api.multi
    def set_default_magento_website(self, url, session):
        for obj in self:
            storeId = obj.store_id
            ctx = dict(self._context or {})
            ctx['instance_id'] = obj.id
            if not storeId:
                storeInfo = self.with_context(
                    ctx)._fetch_magento_store(url, session)
                if storeInfo:
                    self.write(storeInfo)
                else:
                    raise UserError(
                        _('Error!\nMagento Default Website Not Found!!!'))
        return True

    #############################################
    ##          magento connection             ##
    #############################################
    @api.multi
    def test_connection(self):
        session = 0
        connectionStatus = False
        msz = ''
        status = 'Magento Connection Un-successful'
        text = 'Test connection Un-successful please check the magento api credentials!!!'
        url = self.name + XMLRPC_API
        user = self.user
        pwd = self.pwd
        checkMapping = self.correct_mapping
        try:
            server = xmlrpclib.Server(url)
            session = server.login(user, pwd)
        except xmlrpclib.Fault as e:
            text = "Error, %s Invalid Login Credentials!!!" % (e.faultString)
        except IOError as e:
            text = str(e)
        except Exception as e:
            text = "Magento Connection Error in connecting: %s" % (e)
        if session:
            self.set_default_magento_website(url, session)
            text = 'Test Connection with magento is successful, now you can proceed with synchronization.'
            status = "Congratulation, It's Successfully Connected with Magento Api."
            msz = status
            connectionStatus = True

        else:
            msz = status
            msz += "<br/>" + text
        self.status = status
        if checkMapping:
            self.correct_instance_mapping()
        self.connection_status = connectionStatus
        self.message_post(body=msz)
        return self.env['magento.synchronization'].display_message(text)

    @api.model
    def _create_connection(self):
        """ create a connection between Odoo and magento
                returns: False or list"""
        ctx = dict(self._context or {})
        session = 0
        instanceObj = False
        if ctx.get('instance_id'):
            instanceObj = self.browse(ctx.get('instance_id'))
        else:
            activeConnections = self.search([('active', '=', True)])
            if len(activeConnections) > 1:
                raise UserError(
                    _('Error!\nSorry, only one Active Configuration setting is allowed.'))
            if not activeConnections:
                raise UserError(
                    _('Error!\nPlease create the configuration part for Magento connection!!!'))
            else:
                instanceObj = activeConnections[0]
        if instanceObj:
            url = instanceObj.name + XMLRPC_API
            user = instanceObj.user
            pwd = instanceObj.pwd
            if instanceObj.language:
                ctx.update(
                    lang=instanceObj.language
                )
            try:
                server = xmlrpclib.Server(url)
                session = server.login(user, pwd)
            except xmlrpclib.Fault as e:
                raise UserError(
                    _('Error, %s!\nInvalid Login Credentials!!!') %
                    e.faultString)
            except IOError as e:
                raise UserError(_('Error!\n %s') % e)
            except Exception as e:
                raise UserError(
                    _('Error!\nMagento Connection Error in connecting: %s') %
                    e)
            if session:
                return [url, session, instanceObj.id]
        return False

    @api.model
    def fetch_connection_info(self, vals):
        """
                Called by Xmlrpc from Magento
        """
        if vals.get('magento_url'):
            activeConnections = self.search([('active', '=', True)])
            moduleMultiInstance = self.env['ir.module.module'].sudo().search(
                [("name", "=", "mob_multi_instance"), ("state", "=", "installed")])
            if moduleMultiInstance:
                magentoUrl = re.sub(
                    r'^https?:\/\/', '', vals.get('magento_url'))
                for connectionObj in activeConnections:
                    act = connectionObj.name
                    act = re.sub(r'^https?:\/\/', '', act)
                    magentoUrl = re.split('index.php', magentoUrl)[0]
                    if magentoUrl == act or magentoUrl[:-
                                                       1] == act or act in magentoUrl:
                        return connectionObj.read(
                            ['language', 'category', 'warehouse_id'])[0]
            else:
                for connectionObj in activeConnections:
                    return connectionObj.read(
                        ['language', 'category', 'warehouse_id'])[0]
        return False

    @api.model
    def correct_instance_mapping(self):
        self.mapped_status("magento.product")
        self.mapped_status("magento.product.template")
        self.mapped_status("wk.order.mapping")
        self.mapped_status("magento.customers")
        self.mapped_status("magento.product.attribute.value")
        self.mapped_status("magento.product.attribute")
        self.mapped_status("magento.category")
        self.mapped_status("magento.website")
        self.mapped_status("magento.store")
        self.mapped_status("magento.store.view")
        self.mapped_status("magento.attribute.set")
        return True

    @api.model
    def mapped_status(self, model):
        falseInstances = self.env[model].search([('instance_id', '=', False)])
        if falseInstances:
            falseInstances.write({'instance_id': self.id})
        return True

    @api.model
    def mob_upgrade_hook(self):
        activeConfigs = self.sudo().search([('active', '=', True)])
        for activeConfig in activeConfigs :
            activeConfig.sudo().test_connection()
