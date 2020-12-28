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
import itertools

from odoo import api, models
from odoo import release

_logger = logging.getLogger(__name__)
try:
    from clodoo import transodoo
except ImportError as err:
    _logger.error(err)
try:
    from odoo_score import odoo_score
except ImportError as err:
    _logger.error(err)


DEF_SKEYS = {
    'res.partner': [['vat', 'fiscalcode', 'type'],
                    ['vat', 'name', 'type'],
                    ['fiscalcode', 'dim_name', 'type'],
                    # ['rea_code'],
                    ['vat', 'dim_name', 'type'],
                    ['vat', 'type'],
                    ['dim_name', 'type'],
                    ['vat', 'fiscalcode', 'is_company'],
                    ['vat'],
                    ['name', 'is_company']],
    'res.company': [['vat'], ['name']],
    'account.account': [['code', 'company_id'],
                        ['name', 'company_id'],
                        ['dim_name', 'company_id']],
    'account.account.type': [['type'], ['name'], ['dim_name']],
    'account.invoice': [['number', 'company_id'], ['move_name', 'company_id']],
    'account.invoice.line': [['invoice_id', 'sequence'],
                             ['invoice_id', 'name']],
    'product.template': [['name', 'default_code'],
                         ['name', 'barcode'],
                         ['name'],
                         ['default_code'],
                         ['barcode'],
                         ['dim_name']],
    'product.product': [['name', 'default_code'],
                        ['name', 'barcode'],
                        ['name'],
                        ['default_code'],
                        ['barcode'],
                        ['dim_name']],
    'project.project': [['account_analytic_id']],
    'sale.order': [['name']],
    'sale.order.line': [['order_id', 'sequence'], ['order_id', 'name']],
}
# Warning: order is very important!
CANDIDATE_KEYS = ('acc_number', 'login', 'default_code', 'code', 'key',
                  'serial_number', 'description', 'comment', 'name',
                  'dim_name')
SUPPLEMENTAL_KEYS = ('amount', 'sequence')
ANCILLARY_KEYS = ('company_id', 'type_tax_use')
ANCILLARY_LINE_KEYS = (
    'account_id', 'product_id', 'product_qty', 'quantity', 'product_uom_qty',
    'credit', 'debit')

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
        'mail.followers',
        'mail.message',
        'mail.notification',
        'report',
        'res.config',
        'res.font',
        'res.groups',
        'res.request.link',
        'res.users.log',
        'web_tour',
        'workflow',
    ]
    SYSTEM_UNMANAGED = []
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
        cache_model = '_QUEUE_SYNC'
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
        cache_model = '_QUEUE_SYNC'
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
        cache_model = '_QUEUE_SYNC'
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
        cache_model = '_QUEUE_SYNC'
        return ((loc_id and loc_id in self.get_struct_model_attr(
            cache_model, model, default=[])) or
            (ext_id and ext_id in self.get_model_attr(
                channel_id, cache_model, xmodel, default=[])))

    # -------------------------
    # General purpose functions
    # -------------------------
    @api.model
    def is_manageable(self, model):
        return (model not in self.SYSTEM_MODEL_ROOT and
                model not in self.SYSTEM_MODELS and
                model not in self.SYSTEM_UNMANAGED)
    @api.model
    def set_unmanageable(self, model):
        self.SYSTEM_UNMANAGED.append(model)

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

    def get_indexes(self, model):
        query = """select c.name from ir_model m, ir_model_constraint c
        where  c.model = m.id and m.model = '%s'"""
        self._cr.execute(query % model)  # pylint: disable=E8103
        res = []
        for row in self.env.cr.fetchall():
            res.append(row[0])
        return res

    def get_index_fields(self, model, index_name=None):
        # index_name = index_name.replace('.', '_') if index_name else None
        INDEX_FIELDS = """select pgc.conname as constraint_name,
                          ccu.table_name,
                          ccu.column_name,
                          pgc.consrc as definition
        from pg_constraint pgc
        join pg_namespace nsp on nsp.oid = pgc.connamespace
        join pg_class  cls on pgc.conrelid = cls.oid
        left join information_schema.constraint_column_usage ccu
        on pgc.conname = ccu.constraint_name and
        nsp.nspname = ccu.constraint_schema
        where contype ='u' and table_name='%s'
        order by constraint_name,table_name"""
        self._cr.execute(  # pylint: disable=E8103
            INDEX_FIELDS % model.replace('.', '_')
        )
        res = {}
        for row in self.env.cr.fetchall():
            if index_name and index_name != row[0]:
                continue
            if row[0] not in res:
                res[row[0]] = []
            res[row[0]].append(row[2])
        return res

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
    def get_default_keys(self, model):
        skeys = DEF_SKEYS.get(model, [])
        uname = DEF_SKEYS.get(model, [[[]]])[0][0] or False
        is_child_model = self.get_struct_model_attr(model, 'PARENT_ID')
        ancillary = {}
        ancillary_line = {}
        for field in ANCILLARY_KEYS:
            ancillary[field] = field in self.get_struct_attr(model)
        if is_child_model:
            ancillary[self.get_struct_model_attr(
                model, 'PARENT_ID')] = True
            for field in ANCILLARY_LINE_KEYS:
                ancillary_line[field] = field in self.get_struct_attr(model)
        for nm in CANDIDATE_KEYS + SUPPLEMENTAL_KEYS:
            if (nm in self.get_struct_attr(model) and
                    (is_child_model or
                     not self.get_struct_model_field_attr(
                         model, nm, 'readonly'))):
                keys = [nm]
                for kk in ancillary:
                    if ancillary[kk]:
                        keys.append(kk)
                if is_child_model and nm != 'sequence':
                    for kk in ancillary_line:
                        if ancillary_line[kk]:
                            keys.append(kk)
                if self.get_struct_model_attr(model, 'SUPPL_KEY'):
                    keys.append(self.get_struct_model_attr(model, 'SUPPL_KEY'))
                found = False
                for kk in skeys:
                    if not set(keys) - set(kk):
                        found = True
                        break
                if not found:
                    skeys.append(keys)
                if not uname:
                    uname = nm
        return self.get_index_keys(model, uname, skeys)

    def get_index_keys(self, model, uname, skeys):
        for index_name in self.get_indexes(model):
            keys = []
            indexes = self.get_index_fields(model, index_name=index_name)
            if not indexes:
                continue
            for fieldname in indexes[index_name]:
                keys.append(fieldname)
            if not keys:
                # print('@@@ Invalid index %s' % index_name)  # debug
                continue
            if len(keys) == 1 and not uname:
                uname = keys[0]
            found = False
            for kk in skeys:
                if set(keys) == set(kk):
                    found = True
                    # print('@@@ Duplicate search index %s.%s' % (model, kk))  # debug
                    break
            if not found:
                skeys.append(keys)
        return uname, skeys

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

    def store_field_from_rec(self, channel_id, model, field):
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
        apply = field.apply
        if (loc_name in itertools.chain.from_iterable(
                self.get_struct_model_attr(model, 'SKEYS')) and
                loc_name in CANDIDATE_KEYS):
            if not apply:
                apply = 'set_tmp_name()'
            elif apply.find('set_tmp_name()') < 0:
                apply += ',set_tmp_name()'
        self.store_model_field(
            channel_id, model, loc_name, ext_name, apply,
            field.protect, field.spec, required)
        if apply != field.apply:
            field.write({'apply': apply})

    @api.model_cr_context
    def store_odoo_field_from_rec(self, channel_id, model, field):
        if not self.is_struct(field) or field == 'id':
            return
        # diff = False
        ext_ref = '%s_id' % self.get_attr(channel_id, 'PREFIX')
        required = self.get_struct_model_field_attr(
            model, field, 'required')
        if field == ext_ref:
            self.store_model_field(
                channel_id, model, 'id', field, '', False, False, required)
        else:
            ext_odoo_ver = self.get_attr(channel_id, 'ODOO_FVER')
            if ext_odoo_ver:
                ext_name = transodoo.translate_from_to(
                    self.get_attr(channel_id, 'TNL'), model, field,
                    release.major_version, ext_odoo_ver)
            else:
                ext_name = field
            field_def = self.TABLE_DEF.get(model, {}).get(field, {})
            apply = ''
            if 'APPLY' in field_def:
                apply = field_def['APPLY']
            if (field in itertools.chain.from_iterable(
                    self.get_struct_model_attr(model, 'SKEYS')) and
                    field in CANDIDATE_KEYS):
                if not apply:
                    apply = 'set_tmp_name()'
                elif apply.find('set_tmp_name()') < 0:
                    apply += ',set_tmp_name()'
                # diff = True
            if not apply:
                apply = 'odoo_migrate()'
            elif apply.find('odoo_migrate()') < 0:
                apply += ',odoo_migrate()'
            self.store_model_field(
                channel_id, model, field, ext_name, apply, False, False,
                required)
            model_rec = self.env['synchro.channel.model'].search(
                [('name', '=', model),
                 ('synchro_channel_id', '=', channel_id)])
            vals = {
                'name': field,
                'counterpart_name': ext_name,
                'apply': apply,
                'protect': '0',
                'required': required,
                'model_id': model_rec.id,
            }
            self.env['synchro.channel.model.fields'].create(vals)

    @api.model_cr_context
    def setup_channel_model_fields(self, model_rec):
        model = model_rec.name
        channel_id = model_rec.synchro_channel_id.id
        channel = self.env['synchro.channel'].browse(channel_id)
        for field in self.env['synchro.channel.model.fields'].search(
                [('model_id', '=', model_rec.id)]):
            self.store_field_from_rec(channel_id, model, field)
        if channel.identity == 'odoo':
            for field in self.get_struct_attr(model):
                if ((self.is_struct(field) and field != 'id') and
                        not self.get_model_attr(channel_id, model, 'XPIRE') and
                        field not in self.get_model_attr(
                            channel_id, model, 'LOC_FIELDS')):
                    self.store_odoo_field_from_rec(channel_id, model, field)
        # special names
        ext_ref = '%s_id' % self.get_attr(channel_id, 'PREFIX')
        self.set_model_field_attr(
            channel_id, model, 'id', 'LOC_FIELDS', '')
        self.set_model_field_attr(
            channel_id, model, ext_ref, 'LOC_FIELDS', 'id')
        self.set_model_field_attr(
            channel_id, model, 'id', 'EXT_FIELDS', ext_ref)

    @api.model_cr_context
    def store_model_1_channel(self, channel_id, rec):
        model = rec.name
        if rec.field_2complete:
            self.set_model_attr(channel_id, model, '2PULL', True)
        if not self.get_attr(channel_id, 'TNL'):
            tnldict = {}
            transodoo.read_stored_dict(tnldict)
            self.set_attr(channel_id, 'TNL', tnldict)
        # TODO: debug -> minutes=1 production -> minutes=9900
        deltatime = ((self.lifetime(0) / 20) + 1) ** 2
        if (datetime.strptime(rec.write_date, '%Y-%m-%d %H:%M:%S') + timedelta(
                minutes=deltatime)) < datetime.now():
            if not self.get_struct_model_attr(model, 'SKEYS'):
                actual_model = self.env['ir.model.synchro'].get_actual_model(
                    model, only_name=True)
                uname, skeys = self.get_default_keys(actual_model)
                self.set_struct_model_attr(model, 'SKEYS', skeys)
                self.set_struct_model_attr(model, 'MODEL_KEY', uname)
                rec.write({'search_keys': skeys,
                           'field_uname': uname})
                self.env['ir.model.synchro'].logmsg(
                    'debug', '### %(model)s SKEYS=%(skeys)s UNAME=%(uname)s',
                    model=model, ctx={'skeys': skeys, 'uname': uname})
        else:
            self.set_struct_model_attr(model, 'SKEYS', eval(rec.search_keys))
            self.set_struct_model_attr(model, 'MODEL_KEY', rec.field_uname)
        self.set_model_attr(
            channel_id, model, 'BIND', rec.counterpart_name)
        channel = self.env['synchro.channel'].browse(channel_id)
        if rec.model_spec:
            self.set_model_attr(
                channel_id, model, 'MODEL_SPEC', rec.model_spec)
        if channel.identity == 'vg7' and model == 'res.partner.shipping':
            self.set_model_attr(
                channel_id, model, 'KEY_ID', 'customer_shipping_id')
        else:
            self.set_model_attr(channel_id, model, 'KEY_ID', 'id')
        if channel.identity == 'vg7' and model == 'res.partner.supplier':
            self.set_model_attr(
                channel_id, model, 'EXT_ID',
                '%s2_id' % self.get_attr(channel_id, 'PREFIX'))
        elif channel.identity == 'vg7' and model == 'res.partner.bank.company':
            self.set_model_attr(
                channel_id, model, 'EXT_ID',
                '%s2_id' % self.get_attr(channel_id, 'PREFIX'))
        else:
            self.set_model_attr(
                channel_id, model, 'EXT_ID',
                '%s_id' % self.get_attr(channel_id, 'PREFIX'))
        if channel.identity == 'vg7':
            if model == 'res.partner.invoice':
                self.set_model_attr(
                    channel_id, model, 'ID_OFFSET', 200000000)
            elif model == 'res.partner.shipping':
                self.set_model_attr(
                    channel_id, model, 'ID_OFFSET', 100000000)
        self.setup_channel_model_fields(rec)

    @api.model_cr_context
    def setup_ext_model(self, channel_id, rec):
        self.env['ir.model.synchro'].logmsg(
            'any', '$$$>>> setup_ext_model()')
        if (channel_id and channel_id == rec.synchro_channel_id.id and
                channel_id in self.get_channel_list()):
            self.env['ir.model.synchro'].logmsg(
                'any', '$$$>>> ALREADY SET')
            return
        model = rec.name
        if not channel_id:
            channel_id = rec.synchro_channel_id.id
        if self.get_model_attr(channel_id, model, 'XPIRE'):
            self.env['ir.model.synchro'].logmsg(
                'any', '$$$>>> NOT EXPIRED')
            return
        channel = self.env['synchro.channel'].browse(channel_id)
        self.setup_1_channel(channel)
        self.init_model(channel_id, model)
        self.store_model_1_channel(channel_id, rec)
        self.CACHE.set_model_cache(self._cr.dbname, channel_id, model)

    @api.model_cr_context
    def setup_1_channel(self, channel):
        self.env['ir.model.synchro'].logmsg(
            'any', '$$$>>> setup_1_channel()')
        if self.get_attr(channel.id, 'XPIRE'):
            self.env['ir.model.synchro'].logmsg(
                'any', '$$$>>> NOT EXPIRED')
            return
        self.set_channel_base(channel.id)
        self.set_attr(channel.id, 'PRIO', channel.sequence)
        self.set_attr(channel.id, 'OUT_QUEUE', self.get_attr(
            channel.id, 'OUT_QUEUE', default=[]))
        self.set_attr(channel.id, 'IN_QUEUE', self.get_attr(
            channel.id, 'IN_QUEUE', default=[]))
        self.set_attr(channel.id, '_QUEUE_SYNC', self.get_attr(
            channel.id, '_QUEUE_SYNC', default={}))
        self.set_attr(channel.id, 'PREFIX', channel.prefix)
        self.set_attr(channel.id, 'ODOO_FVER', {
            'oe6': '6.1',
            'oe7': '7.0',
            'oe8': '8.0',
            'oe9': '9.0',
            'oe10': '10.0',
            'oe11': '11.0',
            'oe12': '12.0',
            'oe13': '13.0',
            'oe14': '14.0',
        }.get(channel.prefix.split(':')[0], ''))
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
        # if channel.trace:
        #     self.set_attr(channel.id, 'LOGLEVEL', 'info')
        # else:
        #     self.set_attr(channel.id, 'LOGLEVEL', 'debug')
        self.set_attr(channel.id, 'LOGLEVEL', channel.tracelevel)
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
    def setup_model_structure(self, model, actual_model):
        """Store model structure into memory"""
        actual_model = actual_model or model
        model = model or actual_model
        self.env['ir.model.synchro'].logmsg(
            'any', '$$$>>> %(model)s.setup_model_structure(%(amodel)s)',
            model=model, ctx={'amodel': actual_model})
        if not model or self.get_struct_model_attr(model, 'XPIRE'):
            self.env['ir.model.synchro'].logmsg(
                'any', '$$$>>> NOT EXPIRED')
            return
        ir_model = self.env['ir.model.fields']
        self.set_struct_model(actual_model)
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
                        (field.related and not field.required)):
                    attrs['readonly'] = True
                else:
                    attrs[attr] = field[attr]
            if attrs['required']:
                attrs['readonly'] = False
            if not self.is_manageable(model):
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
                elif (actual_model.endswith('.line') and
                      field.relation and
                      actual_model.startswith(field.relation)):
                    self.set_struct_model_attr(
                        actual_model, 'PARENT_ID', field.name)
                elif (field.relation and
                      actual_model.startswith(field.relation)):
                    self.set_struct_model_attr(
                        actual_model, 'SUPPL_KEY', field.name)
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
            self, channel=None, model=None, ext_model=None):
        """Read model value from all active channel model table and store
        them into memory"""
        self.env['ir.model.synchro'].logmsg(
            'any', '$$$>>> %(model)s.setup_model_in_channels(%(xmodel)s)',
            model=model, ctx={'xmodel': ext_model})
        if model:
            domain = [('name', '=', model)]
        elif ext_model:
            domain = [('counterpart_name', '=', ext_model)]
        else:
            self.env['ir.model.synchro'].logmsg(
                'any', '$$$>>> NO MODEL NEITHER EXT_MODEL')
            return
        if channel:
            domain.append(('synchro_channel_id', '=', channel.id))
        recs = self.env['synchro.channel.model'].search(domain)
        if not recs and channel and channel.identity == 'odoo':
            if ext_model:
                if channel:
                    self.env['synchro.channel.model'].build_odoo_synchro_model(
                        channel.id, ext_model)
                else:
                    self.setup_channels(all=True)
                    for channel_id in self.get_channel_list():
                        self.env[
                            'synchro.channel.model'].build_odoo_synchro_model(
                            channel_id, ext_model)
            elif model:
                if channel:
                    self.env['synchro.channel.model'].build_odoo_synchro_model(
                        channel.id, None, model=model)
                else:
                    self.setup_channels(all=True)
                    for channel_id in self.get_channel_list():
                        self.env[
                            'synchro.channel.model'].build_odoo_synchro_model(
                            channel_id, None, model=model)
        for rec in self.env['synchro.channel.model'].search(domain):
            self.setup_ext_model(False, rec)

    @api.model_cr_context
    def open(self, channel=None, model=None, ext_model=None, cls=None):
        """Setup cache if needed, setup model cache if required and needed"""
        self.env['ir.model.synchro'].logmsg(
            'any', '$$$>>> %(model)s.open(%(xmodel)s)',
            model=model, ctx={'xmodel': ext_model})
        ir_synchro_model = self.env['ir.model.synchro']
        if channel and channel.identity == 'odoo':
            if ext_model in ('ir.model', 'ir.module.module') and not model:
                model = ext_model
            elif model in ('ir.model', 'ir.module.module') and not ext_model:
                ext_model = model
        actual_model = model
        if channel and ext_model and not model and channel.identity == 'odoo':
            ext_odoo_ver = ir_synchro_model.get_ext_odoo_ver(channel.prefix)
            if ext_odoo_ver:
                tnldict = ir_synchro_model.get_tnldict(channel.id)
                actual_model = transodoo.translate_from_to(
                    tnldict, 'ir.model', ext_model,
                    ext_odoo_ver, release.major_version,
                    type='model')
                if ext_model == actual_model:
                    ext_model = transodoo.translate_from_to(
                        tnldict, 'ir.model', ext_model,
                        ext_odoo_ver, release.major_version,
                        type='merge')
        elif model:
            actual_model = self.env[
                'ir.model.synchro'].get_actual_model(model, only_name=True)
        if actual_model:
            self.setup_model_structure(model, actual_model)
        self.setup_model_in_channels(
            channel=channel, model=model, ext_model=ext_model)
        self.set_struct_model('_QUEUE_SYNC')
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
