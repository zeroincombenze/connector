# -*- coding: utf-8 -*-
#
# Copyright 2019-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging
from datetime import datetime, timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)
try:
    from python_plus import unicodes
except ImportError as err:
    _logger.error(err)
try:
    from odoo_score import odoo_score
except ImportError as err:
    _logger.error(err)
try:
    from unidecode import unidecode
except ImportError as err:
    _logger.error(err)
try:
    from os0 import os0
except ImportError as err:
    _logger.error(err)
try:
    import oerplib
except ImportError as err:
    _logger.error(err)

SKEYS = {
    'res.country': (['code'], ['name']),
    'res.country.state': (['name', 'country_id'],
                          ['code', 'country_id'],),
    'res.partner': (['vat', 'fiscalcode', 'type'],
                    ['vat', 'name', 'type'],
                    ['fiscalcode', 'dim_name', 'type'],
                    ['rea_code'],
                    ['vat', 'dim_name', 'type'],
                    ['vat', 'type'],
                    ['dim_name', 'type'],
                    ['vat', 'fiscalcode', 'is_company'],
                    ['vat'],
                    ['name', 'is_company'],
                    ['name']),
    'res.company': (['vat'], ['name']),
    'account.account': (['code', 'company_id'],
                        ['name', 'company_id'],
                        ['dim_name', 'company_id']),
    'account.account.type': (['type'], ['name'], ['dim_name']),
    'account.tax': (['description', 'company_id'],
                    ['name', 'company_id'],
                    ['dim_name', 'company_id'],
                    ['amount', 'company_id'],),
    'account.invoice': (['number', 'company_id'], ['move_name', 'company_id']),
    'account.invoice.line': (['invoice_id', 'sequence'],
                             ['invoice_id', 'name']),
    'product.template': (['name', 'default_code'],
                         ['name', 'barcode'],
                         ['name'],
                         ['default_code'],
                         ['barcode'],
                         ['dim_name']),
    'product.product': (['name', 'default_code'],
                        ['name', 'barcode'],
                        ['name'],
                        ['default_code'],
                        ['barcode'],
                        ['dim_name']),
    'sale.order': (['name']),
    'sale.order.line': (['order_id', 'sequence'], ['order_id', 'name']),
}


class IrModelSynchroCache(models.Model):
    _name = 'ir.model.synchro.cache'

    CACHE = odoo_score.SingletonCache()
    SYSTEM_MODEL_ROOT = [
        'base.config.',
        'base_import.',
        'base.language.',
        'base.module.',
        'base.setup.',
        'base.update.',
        'ir.actions.',
        'ir.exports.',
        'ir.model.',
        'ir.module.',
        'ir.qweb.',
        'report.',
        'res.config.',
        'web_editor.',
        'web_tour.',
        'workflow.',
    ]
    SYSTEM_MODELS = [
        '_unknown',
        'base',
        'base.config.settings',
        'base_import',
        'change.password.wizard',
        'ir.autovacuum',
        'ir.config_parameter',
        'ir.exports',
        'ir.fields.converter',
        'ir.filters',
        'ir.http',
        'ir.logging',
        'ir.model',
        'ir.needaction_mixin',
        'ir.qweb',
        'ir.rule',
        'ir.translation',
        'ir.ui.menu',
        'ir.ui.view',
        'ir.values',
        'mail.alias',
        'report',
        'res.config',
        'res.font',
        'res.request.link',
        'res.users.log',
        'web_tour',
        'workflow',
    ]
    TABLE_DEF = {
        'base': {
            # 'company_id': {'required': True},
            'create_date': {'readonly': True},
            'create_uid': {'readonly': True},
            'message_channel_ids': {'readonly': True},
            'message_follower_ids': {'readonly': True},
            'message_ids': {'readonly': True},
            'message_is_follower': {'readonly': True},
            'message_last_post': {'readonly': True},
            'message_needaction': {'readonly': True},
            'message_needaction_counter': {'readonly': True},
            'message_unread': {'readonly': True},
            'message_unread_counter': {'readonly': True},
            'password': {'protect_update': 2},
            'password_crypt': {'protect_update': 2},
            'write_date': {'readonly': True},
            'write_uid': {'readonly': True},
        },
        'account.account': {
            'user_type_id': {'required': True},
            'internal_type': {'readonly': False},
        },
        'account.invoice': {
            'account_id': {'readonly': False},
            'comment': {'readonly': False},
            'date': {'readonly': False},
            'date_due': {'readonly': False},
            'date_invoice': {'readonly': False},
            'fiscal_position_id': {'readonly': False},
            'name': {'readonly': False},
            'number': {'readonly': False, 'required': False},
            'partner_id': {'readonly': False},
            'partner_shipping_id': {'readonly': False},
            'payment_term_id': {'readonly': False},
            'registration_date': {'readonly': False},
            'type': {'readonly': False},
            'user_id': {'readonly': False},
        },
        'account.payment.term': {},
        'ir.sequence': {'number_next_actual': {'protect_update': 4}},
        'product.category': {},
        'product.product': {
            'company_id': {'readonly': True},
        },
        'product.template': {
            'company_id': {'readonly': True},
        },
        'purchase.order': {
            'name': {'required': False},
        },
        'res.company': {
            'default_picking_type_for_package_preparation_id':
                {'readonly': True},
            'due_cost_service_id': {'readonly': True},
            'internal_transit_location_id': {'readonly': True},
            'paperformat_id': {'readonly': True},
            'of_account_end_vat_statement_interest_account_id':
                {'readonly': True},
            'of_account_end_vat_statement_interest': {'readonly': True},
            'parent_id': {'readonly': True},
            'po_lead': {'readonly': True},
            'project_time_mode_id': {'readonly': True},
            'sp_account_id': {'readonly': True},
        },
        'res.country': {
            'name': {'protect_update': 2},
        },
        'res.country.state': {'name': {'protect_update': 2}},
        'res.currency': {
            'rate_ids': {'protect_update': 2},
            'rounding': {'protect_update': 2},
        },
        'res.partner': {
            'company_id': {'readonly': True},
            'notify_email': {'readonly': True},
            'property_product_pricelist': {'readonly': True},
            'property_stock_customer': {'readonly': True},
            'property_stock_supplier': {'readonly': True},
            'title': {'readonly': True},
        },
        'res.partner.bank': {
            'bank_name': {'readonly': False},
        },
        'res.users': {
            'action_id': {'readonly': True},
            'category_id': {'readonly': True},
            'company_id': {'readonly': True},
            'login_date': {'readonly': True},
            'new_password': {'readonly': True},
            'opt_out': {'readonly': True},
            'password': {'readonly': True},
            'password_crypt': {'readonly': True},
        },
        'sale.order': {
            'name': {'readonly': False, 'required': False},
        },
        'stock.picking.package.preparation': {
            'ddt_number': {'required': False},
        },
    }

    # -----------------------
    # Record cache management
    # -----------------------
    @api.model_cr_context
    def expired_cache(self, channel_id, xmodel, model):
        cache_model = 'QUEUE_SYNC'
        if self.get_struct_model_attr(cache_model, 'XPIRE'):
            self.set_struct_model(cache_model)
            self.CACHE.set_struct_cache(self._cr.dbname, cache_model)
        if self.get_model_attr(channel_id, cache_model, 'XPIRE'):
            self.set_attr(channel_id, cache_model, {})
            self.CACHE.set_model_cache(
                self._cr.dbname, channel_id, cache_model)

    @api.model_cr_context
    def push_id(self, channel_id, xmodel, model, loc_id=None, ext_id=None):
        self.expired_cache(channel_id, xmodel, model)
        cache_model = 'QUEUE_SYNC'
        if loc_id:
            rec_list = self.get_struct_model_attr(
                cache_model, model, default=[])
            if loc_id not in rec_list:
                rec_list.append(loc_id)
                self.set_struct_model_attr(cache_model, model, rec_list)
        if ext_id:
            rec_list = self.get_model_attr(
                channel_id, cache_model, xmodel, default=[])
            if ext_id not in rec_list:
                rec_list.append(ext_id)
                self.set_model_attr(channel_id, cache_model, xmodel, rec_list)

    @api.model_cr_context
    def pop_id(self, channel_id, xmodel, model, loc_id=None, ext_id=None):
        self.expired_cache(channel_id, xmodel, model)
        cache_model = 'QUEUE_SYNC'
        if loc_id:
            rec_list = self.get_struct_model_attr(
                cache_model, model, default=[])
            if loc_id in rec_list:
                rec_list.pop(rec_list.index(loc_id))
                self.set_struct_model_attr(cache_model, model, rec_list)
        if ext_id:
            rec_list = self.get_model_attr(
                channel_id, cache_model, xmodel, default=[])
            if ext_id in rec_list:
                rec_list.pop(rec_list.index(ext_id))
                self.set_model_attr(channel_id, cache_model, xmodel, rec_list)

    @api.model_cr_context
    def id_is_in_cache(
            self, channel_id, xmodel, model, loc_id=None, ext_id=None):
        self.expired_cache(channel_id, xmodel, model)
        cache_model = 'QUEUE_SYNC'
        return ((loc_id and loc_id in self.get_struct_model_attr(
            cache_model, model, default=[])) or
                (ext_id and ext_id in self.get_model_attr(
                    channel_id, cache_model, xmodel, default=[])))

    # -------------------------
    # General purpose functions
    # -------------------------
    @api.model_cr_context
    def lifetime(self, lifetime):
        return self.CACHE.lifetime(self._cr.dbname, lifetime)

    @api.model_cr_context
    def clean_cache(self, channel_id=None, model=None, lifetime=None):
        _logger.info('> clean_cache(%d,%s,%d)' % (
            (channel_id or -1), model, (lifetime or -1)
        ))
        cache = self.CACHE
        if lifetime:
            self.lifetime(lifetime)
        for chn_id in self.get_channel_list():
            if not channel_id or chn_id == channel_id:
                cache.init_channel(self._cr.dbname, chn_id)
        if model:
            cache.init_struct_model(self._cr.dbname, model)
        else:
            cache.init_struct(self._cr.dbname)
        return self.lifetime(0)

    @api.model_cr_context
    def set_loglevel(self, loglevel):
        self.setup_channels(all=True)
        for channel_id in self.get_channel_list():
            self.set_attr(channel_id, 'LOGLEVEL', loglevel)
        return True

    @api.model_cr_context
    def is_struct(self, model):
        return model < 'A' or model > '['

    # ------------------
    # Channel primitives
    # ------------------
    #
    # channel_id
    #    \_______ model
    #    \ ...      \____ LOC_FIELDS
    #               |           \____  field_name
    #               |           \ ...
    #               \____ EXT_FIELDS
    #               \ ...
    #
    @api.model_cr_context
    def get_channel_list(self):
        return self.CACHE.get_channel_list(self._cr.dbname)

    @api.model_cr_context
    def set_channel_base(self, channel_id):
        return self.CACHE.set_channel_base(self._cr.dbname, channel_id)

    @api.model_cr_context
    def get_channel_models(self, channel_id, default=None):
        return self.CACHE.get_channel_models(
            self._cr.dbname, channel_id, default=default)

    @api.model_cr_context
    def set_model(self, channel_id, model):
        if model not in self.get_channel_models(channel_id):
            self.init_model(channel_id, model)

    @api.model_cr_context
    def set_attr(self, channel_id, attrib, value):
        self.set_channel_base(channel_id)
        return self.CACHE.set_attr(self._cr.dbname, channel_id, attrib, value)

    @api.model_cr_context
    def get_attr(self, channel_id, attrib, default=None):
        self.set_channel_base(channel_id)
        return self.CACHE.get_attr(
            self._cr.dbname, channel_id, attrib, default=default)

    @api.model_cr_context
    def get_model_attr(self, channel_id, model, attrib, default=None):
        self.set_model(channel_id, model)
        return self.CACHE.get_model_attr(
            self._cr.dbname, channel_id, model, attrib, default=default)

    @api.model_cr_context
    def set_model_attr(self, channel_id, model, attrib, value):
        self.set_model(channel_id, model)
        return self.CACHE.set_model_attr(
            self._cr.dbname, channel_id, model, attrib, value)

    @api.model_cr_context
    def del_model_attr(self, channel_id, model, attrib):
        return self.CACHE.del_model_attr(
            self._cr.dbname, channel_id, model, attrib)

    @api.model_cr_context
    def get_model_field_attr(self, channel_id, model, field, attrib,
                             default=None):
        # Warning! Hierarchy at this level is not linear
        # self.set_model_attr(channel_id, model, field, attrib)
        return self.CACHE.get_model_field_attr(
            self._cr.dbname, channel_id, model, field, attrib, default=default)

    @api.model_cr_context
    def set_model_field_attr(self, channel_id, model, field, attrib, value):
        # Warning! Hierarchy at this level is not linear
        # self.set_model_attr(channel_id, model, field, attrib)
        return self.CACHE.set_model_field_attr(
            self._cr.dbname, channel_id, model, field, attrib, value)

    @api.model_cr_context
    def init_model(self, channel_id, model):
        self.set_channel_base(channel_id)
        self.set_attr(
            channel_id, model, self.get_attr(channel_id, model) or {})
        self.set_model_attr(channel_id, model, 'LOC_FIELDS', {})
        self.set_model_attr(channel_id, model, 'EXT_FIELDS', {})
        self.set_model_attr(channel_id, model, 'APPLY', {})
        self.set_model_attr(channel_id, model, 'PROTECT', {})
        self.set_model_attr(channel_id, model, 'SPEC', {})
        self.set_model_attr(channel_id, model, 'REQUIRED', {})

    # --------------------------
    # Model structure primitives
    # --------------------------
    @api.model_cr_context
    def model_list(self):
        return self.CACHE.model_list(self._cr.dbname)

    @api.model_cr_context
    def set_struct_model(self, model):
        if model not in self.model_list():
            pass
        self.CACHE.set_struct_model(self._cr.dbname, model)

    @api.model_cr_context
    def set_struct_attr(self, attrib, value):
        self.CACHE.set_struct_model(self._cr.dbname, attrib)
        return self.CACHE.set_struct_attr(
            self._cr.dbname, attrib, value)

    @api.model_cr_context
    def get_struct_attr(self, attrib, default=None):
        return self.CACHE.get_struct_attr(
            self._cr.dbname, attrib, default=default)

    @api.model_cr_context
    def get_struct_model_attr(self, model, attrib, default=None):
        self.set_struct_model(model)
        return self.CACHE.get_struct_model_attr(
            self._cr.dbname, model, attrib, default=default)

    @api.model_cr_context
    def set_struct_model_attr(self, model, attrib, value):
        self.set_struct_model(model)
        return self.CACHE.set_struct_model_attr(
            self._cr.dbname, model, attrib, value)

    @api.model_cr_context
    def get_struct_model_field_attr(self, model, field, attrib, default=None):
        return self.CACHE.get_struct_model_field_attr(
            self._cr.dbname, model, field, attrib, default=default)

    # ----------------
    # Cache management
    # ----------------
    @api.model_cr_context
    def store_model_field(
            self, channel_id, model, loc_name, ext_name, apply, protect, spec,
            required):
        if model == 'res.partner' and loc_name == 'assigned_bank':
            pass
        self.set_model_field_attr(
            channel_id, model, loc_name, 'LOC_FIELDS', ext_name)
        self.set_model_field_attr(
            channel_id, model, ext_name, 'EXT_FIELDS', loc_name)
        if apply:
            self.set_model_field_attr(
                channel_id, model, loc_name, 'APPLY', apply)
        if protect and protect != '0':
            self.set_model_field_attr(
                channel_id, model, loc_name, 'PROTECT', protect)
        if spec:
            self.set_model_field_attr(
                channel_id, model, loc_name, 'SPEC', spec)
        self.set_model_field_attr(
            channel_id, model, loc_name, 'REQUIRED', required)

    @api.model_cr_context
    def store_odoo_model_1_channels(
            self, channel_id, model, skeys, field_uname, ext_ref):
        self.set_model_attr(channel_id, model, '2PULL', True)
        self.set_model_attr(
            channel_id, model, 'MODEL_KEY', field_uname)
        self.set_model_attr(
            channel_id, model, 'SKEYS', skeys)
        self.set_model_attr(
            channel_id, model, 'BIND', model)
        self.set_model_attr(
            channel_id, model, 'KEY_ID', 'id')
        self.set_model_attr(
            channel_id, model, 'EXT_ID', ext_ref)
        self.set_model_attr(
            channel_id, model, 'LAST_REC', {})

    @api.model_cr_context
    def setup_odoo_model(self, channel_id, model, force=None):
        if (not force and
                model in self.get_channel_models(channel_id) and
                self.get_model_attr(channel_id, model, 'XPIRE') and
                self.get_model_attr(channel_id, model, 'LOC_FIELDS')):
            return
        self.init_model(channel_id, model)
        ext_ref = '%s_id' % self.get_attr(channel_id, 'PREFIX')
        skeys = []
        field_uname = False
        if model == 'res.users':
            has_company = False
        else:
            has_company = 'company_id' in self.get_struct_attr(model)
        for nm in ('code', 'acc_number', 'login', 'description', 'name'):
            if (nm in self.get_struct_attr(model) and
                    not self.get_struct_model_field_attr(
                        model, nm, 'readonly')):
                if has_company:
                    skeys.append([nm, 'company_id'])
                else:
                    skeys.append([nm])
                if not field_uname:
                    field_uname = nm
        for field in self.get_struct_attr(model):
            if not self.is_struct(field) or field == 'id':
                continue
            required = self.get_struct_model_field_attr(
                model, field, 'required')
            if field == ext_ref:
                self.store_model_field(
                    channel_id, model, 'id', field, '', False, False, required)
            else:
                self.store_model_field(
                    channel_id, model, field, field, '', False, False,
                    required)
            field_def = self.TABLE_DEF.get(model, {}).get(field, {})
            if 'APPLY' in field_def:
                self.set_model_field_attr(
                    channel_id, model, field, 'APPLY', field_def['APPLY'])
            elif field in (
                    'code', 'acc_number', 'login', 'description', 'name'):
                self.set_model_field_attr(
                    channel_id, model, field, 'APPLY', 'set_tmp_name()')
        if SKEYS.get(model):
            self.store_odoo_model_1_channels(
                channel_id, model, SKEYS[model], field_uname, ext_ref)
        else:
            self.store_odoo_model_1_channels(
                channel_id, model, skeys, field_uname, ext_ref)
        self.CACHE.set_model_cache(self._cr.dbname, channel_id, model)

    @api.model_cr_context
    def setup_channel_model_fields(self, model_rec):
        model = model_rec.name
        channel_id = model_rec.synchro_channel_id.id
        skeys = []
        field_uname = False
        has_company = 'company_id' in self.get_struct_attr(model)
        for nm in ('code', 'acc_number', 'login', 'description', 'name'):
            if nm in self.get_struct_attr(model):
                if has_company:
                    skeys.append([nm, 'company_id'])
                else:
                    skeys.append([nm])
                if not field_uname:
                    field_uname = nm
        for field in self.env[
            'synchro.channel.model.fields'].search(
            [('model_id', '=', model_rec.id)]):
            if field.name:
                loc_name = field.name
            else:
                loc_name = '.%s' % field.counterpart_name
            if field.counterpart_name:
                ext_name = field.counterpart_name
            else:
                ext_name = '.%s' % field.name
            required = self.get_struct_model_field_attr(
                model, loc_name, 'required') or field.required
            self.store_model_field(
                channel_id, model, loc_name, ext_name, field.apply,
                field.protect, field.spec, required)
        # special names
        ext_ref = '%s_id' % self.get_attr(channel_id, 'PREFIX')
        self.set_model_field_attr(
            channel_id, model, 'id', 'LOC_FIELDS', '')
        self.set_model_field_attr(
            channel_id, model, ext_ref, 'LOC_FIELDS', 'id')
        self.set_model_field_attr(
            channel_id, model, 'id', 'EXT_FIELDS', ext_ref)
        if not self.get_model_attr(channel_id, model, 'SKEYS'):
            self.set_model_attr(
                channel_id, model, 'SKEYS', skeys)
        self.set_model_attr(
            channel_id, model, 'MODEL_KEY', field_uname)

    @api.model_cr_context
    def store_model_1_channel(self, channel_id, model, rec):
        if rec.field_2complete:
            self.set_model_attr(channel_id, model, '2PULL', True)
        self.set_model_attr(
            channel_id, model, 'MODEL_KEY', rec.field_uname)
        if rec.search_keys:
            self.set_model_attr(
                channel_id, model, 'SKEYS', eval(rec.search_keys))
        else:
            self.set_model_attr(
                channel_id, model, 'SKEYS', SKEYS.get(model))
        self.set_model_attr(
            channel_id, model, 'BIND', rec.counterpart_name)
        if rec.model_spec:
            self.set_model_attr(
                channel_id, model, 'MODEL_SPEC', rec.model_spec)
        if model == 'res.partner.shipping':
            self.set_model_attr(
                channel_id, model, 'KEY_ID', 'customer_shipping_id')
        else:
            self.set_model_attr(
                channel_id, model, 'KEY_ID', 'id')
        if model == 'res.partner.supplier':
            self.set_model_attr(
                channel_id, model, 'EXT_ID',
                '%s2_id' % self.get_attr(channel_id, 'PREFIX'))
        elif model == 'res.partner.bank.company':
            self.set_model_attr(
                channel_id, model, 'EXT_ID',
                '%s2_id' % self.get_attr(channel_id, 'PREFIX'))
        else:
            self.set_model_attr(
                channel_id, model, 'EXT_ID',
                '%s_id' % self.get_attr(channel_id, 'PREFIX'))
        if model == 'res.partner.invoice':
            self.set_model_attr(
                channel_id, model, 'ID_OFFSET', 200000000)
        elif model == 'res.partner.shipping':
            self.set_model_attr(
                channel_id, model, 'ID_OFFSET', 100000000)
        self.setup_channel_model_fields(rec)

    @api.model_cr_context
    def setup_ext_model(self, channel_id, rec):
        if (channel_id and channel_id == rec.synchro_channel_id.id and
                channel_id in self.get_channel_list()):
            return
        model = rec.name
        if not channel_id:
            channel_id = rec.synchro_channel_id.id
        if self.get_model_attr(channel_id, model, 'XPIRE'):
            return
        channel = self.env['synchro.channel'].browse(channel_id)
        self.setup_1_channel(channel)
        self.init_model(channel_id, model)
        self.store_model_1_channel(channel_id, model, rec)
        self.CACHE.set_model_cache(self._cr.dbname, channel_id, model)

    @api.model_cr_context
    def setup_1_channel(self, channel):
        if self.get_attr(channel.id, 'XPIRE'):
            return
        self.set_channel_base(channel.id)
        self.set_attr(channel.id, 'PRIO', channel.sequence)
        self.set_attr(channel.id, 'OUT_QUEUE', self.get_attr(
            channel.id, 'OUT_QUEUE', default=[]))
        self.set_attr(channel.id, 'IN_QUEUE', self.get_attr(
            channel.id, 'IN_QUEUE', default=[]))
        self.set_attr(channel.id, 'QUEUE_SYNC', self.get_attr(
            channel.id, 'QUEUE_SYNC', default={}))
        self.set_attr(channel.id, 'PREFIX', channel.prefix)
        self.set_attr(channel.id, 'IDENTITY', channel.identity)
        self.set_attr(channel.id, 'METHOD', channel.method)
        ctx = {}
        if channel.company_id:
            ctx['company_id'] = channel.company_id.id
            ctx['country_id'] = channel.company_id.partner_id.country_id.id
        else:
            ctx['company_id'] = self.env.user.company_id.id
            ctx[
                'country_id'] = self.env.user.company_id. \
                partner_id.country_id.id
        ctx['is_company'] = True
        self.set_attr(channel.id, 'CTX', ctx)
        self.set_attr(channel.id, 'CLIENT_KEY', channel.client_key)
        self.set_attr(channel.id,
                      'COUNTERPART_URL', channel.counterpart_url)
        self.set_attr(channel.id,
                      'EXCHANGE_PATH', channel.exchange_path)
        self.set_attr(channel.id, 'PASSWORD', channel.password)
        if channel.product_without_variants:
            self.set_attr(channel.id, 'NO_VARIANTS', True)
        if channel.trace:
            self.set_attr(channel.id, 'LOGLEVEL', 'info')
        else:
            self.set_attr(channel.id, 'LOGLEVEL', 'debug')
        self.CACHE.set_channel_cache(self._cr.dbname, channel.id)

    @api.model_cr_context
    def setup_channels(self, all=None):
        """If channel information are expired, read values from channel table
        and store them into memory"""
        if not len(self.get_channel_list()) or all:
            for channel in self.env['synchro.channel'].search(
                    [], order='sequence'):
                self.setup_1_channel(channel)

    @api.model_cr_context
    def setup_model_structure(self, model, actual_model, ro_fields=None):
        """Store model structure into memory"""
        if not model:
            return
        # cache = self.CACHE
        ro_fields = ro_fields or []
        if self.get_struct_model_attr(model, 'XPIRE'):
            return
        ir_model = self.env['ir.model.fields']
        self.set_struct_model(model)
        for field in ir_model.search([('model', '=', actual_model)]):
            global_def = self.TABLE_DEF.get('base', {}).get(field.name, {})
            field_def = self.TABLE_DEF.get(model, {}).get(field.name, {})
            attrs = {}
            for attr in ('required', 'readonly', 'protect_update'):
                if attr in field_def:
                    attrs[attr] = field_def[attr]
                elif attr in global_def:
                    attrs[attr] = global_def[attr]
                elif attr == 'readonly' and (
                        field.ttype in ('binary', 'reference') or
                        (field.related and not field.required) or
                        field.name in ro_fields):
                    attrs['readonly'] = True
                else:
                    attrs[attr] = field[attr]
            if attrs['required']:
                attrs['readonly'] = False
            if (field.relation in self.SYSTEM_MODEL_ROOT or
                    field.relation in self.SYSTEM_MODELS):
                attrs['readonly'] = True
            self.set_struct_model_attr(
                actual_model, field.name, {
                    'ttype': field.ttype,
                    'relation': field.relation,
                    'required': attrs['required'],
                    'readonly': attrs['readonly'],
                    'protect': attrs['protect_update'],
                })
            if field.relation != actual_model:
                if field.relation and field.relation == (
                        '%s.line' % actual_model):
                    self.set_struct_model_attr(
                        actual_model, 'CHILD_IDS', field.name)
                    self.set_struct_model_attr(
                        actual_model, 'MODEL_CHILD', field.relation)
                elif field.relation and actual_model.startswith(
                        field.relation):
                    self.set_struct_model_attr(
                        actual_model, 'PARENT_ID', field.name)
                # TODO:avoid recursive loop
                # elif field.relation == actual_model:
                #    constraints = ['id', '<>', field.name]
            if field.name == 'original_state':
                self.set_struct_model_attr(
                    actual_model, 'MODEL_STATE', True)
            elif field.name == 'to_delete':
                self.set_struct_model_attr(
                    actual_model, 'MODEL_2DELETE', True)
            elif field.name == 'name':
                self.set_struct_model_attr(
                    actual_model, 'MODEL_WITH_NAME', True)
            elif field.name == 'active':
                self.set_struct_model_attr(
                    actual_model, 'MODEL_WITH_ACTIVE', True)
            elif field.name == 'dim_name':
                self.set_struct_model_attr(
                    actual_model, 'MODEL_WITH_DIMNAME', True)
            elif field.name == 'company_id':
                self.set_struct_model_attr(
                    actual_model, 'MODEL_WITH_COMPANY', True)
            elif field.name == 'country_id':
                self.set_struct_model_attr(
                    actual_model, 'MODEL_WITH_COUNTRY', True)
        self.CACHE.set_struct_cache(self._cr.dbname, model)

    @api.model_cr_context
    def setup_model_in_channels(
            self, channel_id=None, model=None, ext_model=None):
        """Read model value from all active channel model table and store
        them into memory"""
        if model:
            where = [('name', '=', model)]
        elif ext_model:
            where = [('counterpart_name', '=', ext_model)]
        else:
            return
        if channel_id:
            where.append(('synchro_channel_id', '=', channel_id))
        self.setup_channels()
        for rec in self.env['synchro.channel.model'].search(where):
            self.setup_ext_model(False, rec)
        for chn_id in self.get_channel_list():
            if channel_id and chn_id != channel_id:
                continue
            if self.get_attr(chn_id, 'IDENTITY') == 'odoo':
                model = model or ext_model
                self.setup_odoo_model(chn_id, model)

    @api.model_cr_context
    def open(self, channel_id=None, model=None, ext_model=None, cls=None):
        """Setup cache if needed, setup model cache if required and needed"""
        actual_model = self.env[
            'ir.model.synchro'].get_actual_model(model, only_name=True)
        self.setup_model_structure(model, actual_model)
        self.setup_model_in_channels(
            channel_id=channel_id, model=model, ext_model=ext_model)
        self.set_struct_model('QUEUE_SYNC')
        if cls is not None:
            if cls.__class__.__name__ != model:
                raise RuntimeError('Class %s not of declared model %s' % (
                    cls.__class__.__name__, model))
            if hasattr(cls, 'CHILD_IDS'):
                self.set_struct_model_attr(actual_model, 'CHILD_IDS',
                                           getattr(cls, 'CHILD_IDS'))
            if hasattr(cls, 'MODEL_CHILD'):
                self.set_struct_model_attr(actual_model, 'MODEL_CHILD',
                                           getattr(cls, 'MODEL_CHILD'))
            if hasattr(cls, 'PARENT_ID'):
                self.set_struct_model_attr(actual_model, 'PARENT_ID',
                                           getattr(cls, 'PARENT_ID'))
