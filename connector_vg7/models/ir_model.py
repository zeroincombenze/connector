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
import os
from datetime import datetime, timedelta
import csv

import requests
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
    'account.invoice': (['number'], ['move_name']),
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


class IrModelSynchro(models.Model):
    _name = 'ir.model.synchro'
    _inherit = 'ir.model'

    LOGLEVEL = 'debug'


    def _build_unique_index(self, model, prefix):
        '''Build unique index on table to <vg7>_id for performance'''
        if isinstance(model, (list, tuple)):
            table = model[0].replace('.', '_')
        else:
            table = model.replace('.', '_')
        index_name = '%s_unique_%s' % (table, prefix)
        self._cr.execute(                               # pylint: disable=E8103
            "SELECT indexname FROM pg_indexes WHERE indexname = '%s'" %
            index_name
        )
        if not self._cr.fetchone():
            self._cr.execute(                           # pylint: disable=E8103
                "CREATE UNIQUE INDEX %s on %s (%s_id) where %s_id<>0" %
                (index_name, table, prefix, prefix)
            )

    def wep_text(self, text):
        if text:
            return unidecode(text).strip()
        return text

    def dim_text(self, text):
        text = self.wep_text(text)
        if text:
            res = ''
            for ch in text:
                if ch.isalnum():
                    res += ch.lower()
            text = res
        return text

    def logmsg(self, channel_id, msg):
        cache = self.env['ir.model.synchro.cache']
        if isinstance(channel_id, basestring):
            loglevel = channel_id
        elif channel_id:
            loglevel = cache.get_attr(channel_id, 'LOGLEVEL', default='debug')
            self.LOGLEVEL = loglevel
        else:
            loglevel = self.LOGLEVEL
        if loglevel == 'warning':
            _logger.warning(msg)
        elif loglevel == 'info':
            _logger.info(msg)
        else:
            _logger.debug(msg)

    @api.model
    def get_xmodel(self, model, spec):
        xmodel = model
        if model == 'res.partner':
            if spec == 'delivery':
                xmodel = 'res.partner.shipping'
            elif spec == 'invoice':
                xmodel = 'res.partner.invoice'
            elif spec == 'supplier':
                xmodel = 'res.partner.supplier'
        return xmodel

    @api.model
    def get_actual_model(self, model, only_name=False):
        actual_model = model
        if model in ('res.partner.shipping',
                     'res.partner.invoice',
                     'res.partner.supplier'):
            actual_model = 'res.partner'
        if only_name:
            return actual_model
        return self.env[actual_model]

    @api.model
    def get_spec_from_xmodel(self, xmodel):
        if xmodel == 'res.partner.shipping':
            return 'delivery'
        elif xmodel == 'res.partner.invoice':
            return 'invoice'
        elif xmodel == 'res.partner.supplier':
            return 'supplier'
        return ''

    @api.model
    def get_loc_ext_id_name(self, channel_id, model, spec=None):
        cache = self.env['ir.model.synchro.cache']
        xmodel = self.get_xmodel(model, spec) if spec else model
        cache.open(model=xmodel)
        return cache.get_model_attr(
            channel_id, xmodel, 'EXT_ID',
            default='%s_id' % cache.get_attr(channel_id, 'PREFIX'))

    @api.model
    def get_loc_ext_id_value(self, channel_id, model, ext_id, spec=None):
        cache = self.env['ir.model.synchro.cache']
        xmodel = self.get_xmodel(model, spec) if spec else model
        cache.open(model=xmodel)
        offset = cache.get_model_attr(
            channel_id, xmodel, 'ID_OFFSET', default=0)
        if ext_id < offset:
            return ext_id + offset
        return ext_id

    @api.model
    def get_actual_ext_id_value(self, channel_id, model, ext_id, spec=None):
        cache = self.env['ir.model.synchro.cache']
        xmodel = self.get_xmodel(model, spec) if spec else model
        cache.open(model=xmodel)
        offset = cache.get_model_attr(
            channel_id, xmodel, 'ID_OFFSET', default=0)
        if ext_id > offset:
            return ext_id - offset
        return ext_id


    def drop_fields(self, model, vals, to_delete):
        for name in to_delete:
            if isinstance(vals, (list, tuple)):
                del vals[vals.index(name)]
            else:
                del vals[name]
        return vals

    def drop_invalid_fields(self, xmodel, vals):
        cache = self.env['ir.model.synchro.cache']
        actual_model = self.get_actual_model(xmodel, only_name=True)
        if isinstance(vals, (list, tuple)):
            to_delete = list(set(vals) - set(
                cache.get_struct_attr(actual_model).keys()))
        else:
            to_delete = list(set(vals.keys()) - set(
                cache.get_struct_attr(actual_model).keys()))
        return self.drop_fields(xmodel, vals, to_delete)

    def drop_protected_fields(self, channel_id, xmodel, vals, rec):
        cache = self.env['ir.model.synchro.cache']
        actual_model = self.get_actual_model(xmodel, only_name=True)
        for field in vals.copy():
            protect = max(
                int(cache.get_struct_model_field_attr(
                    actual_model, field, 'protect', default='0')),
                int(cache.get_model_field_attr(
                    channel_id, xmodel, field, 'PROTECT', default='0')))
            if (protect == 3 or
                    (protect == 2 and rec[field]) or
                    (protect == 1 and not vals[field])):
                del vals[field]
            elif isinstance(vals[field], (basestring, int, long, bool)):
                if ((cache.get_struct_model_field_attr(
                    actual_model, field, 'ttype') == 'many2one' and vals[
                        field] == rec[field].id) or
                        vals[field] == rec[field]):
                    del vals[field]
        return vals

    def set_state_to_draft(self, model, rec, vals):
        self.logmsg(1, '>>> set_state_to_draft(%s,%d)' % (
                    model, (rec and rec.id or -1)))
        errc = 0
        if 'state' in vals:
            vals['original_state'] = vals['state']
        elif rec:
            vals['original_state'] = rec.state
        if model == 'account.invoice':
            if rec:
                rec.set_defaults()
                rec.compute_taxes()
                rec.write({})
                if rec.state == 'paid':
                    return vals, -4
                elif rec.state == 'open':
                    rec.action_invoice_cancel()
                    rec.action_invoice_draft()
                elif rec.state == 'cancel':
                    rec.action_invoice_draft()
            # vals['state'] = 'draft'
            if 'state' in vals:
                del vals['state']
        elif model == 'sale.order':
            if rec:
                rec.set_defaults()
                rec._compute_tax_id()
                rec.write({})
                if rec.invoice_count > 0 or rec.ddt_ids:
                    return vals, -4
                if rec.state == 'done':
                    return vals, -4
                elif rec.state == 'sale':
                    rec.action_cancel()
                    rec.action_draft()
                elif rec.state == 'cancel':
                    rec.action_draft()
            # vals['state'] = 'draft'
            if 'state' in vals:
                del vals['state']
        elif model == 'stock.picking.package.preparation':
            if rec:
                self.logmsg(1, '>>> unlink(%s,%d)' % (model, rec.id))
                try:
                    rec.unlink()
                except IOError:
                    errc = -2
        return vals, errc

    def set_actual_state(self, model, rec):
        self.logmsg(1, '>>> set_actual_state(%s,%d)' % (
                    model, (rec and rec.id)))
        if not rec:
            return -3
        cache = self.env['ir.model.synchro.cache']
        if model == 'account.invoice':
            rec.compute_taxes()
            # Please, dO not remove this write: set default values in header
            rec.write({})
            if rec.state == rec.original_state:
                return rec.id
            elif rec.state != 'draft':
                _logger.error('Unauthorized state change of %s.%d' % (
                    model, rec.id))
                return -4
            elif rec.original_state == 'open':
                rec.action_invoice_open()
            elif rec.original_state == 'cancel':
                rec.action_invoice_cancel()
        elif model == 'sale.order':
            # Please, dO not remove this write: set default values in header
            rec.write({})
            if rec.state == rec.original_state:
                return rec.id
            elif rec.state != 'draft':
                _logger.error('Unauthorized state change of %s.%d' % (
                    model, rec.id))
                return -4
            elif rec.original_state == 'sale':
                rec._compute_tax_id()
                if cache.get_struct_model_attr('sale.order.line', 'agents'):
                    rec._compute_commission_total()
                rec.action_confirm()
            elif rec.original_state == 'cancel':
                rec.action_cancel()
        elif model == 'stock.picking.package.preparation':
            rec.set_done()
        return rec.id

    def sync_rec_from_counterpart(self, channel_id, model, vg7_id):
        if not vg7_id:
            _logger.error('Invalid id %s for the counterpart request' % vg7_id)
            return False
        cache = self.env['ir.model.synchro.cache']
        data = self.get_counterpart_response(
            channel_id,
            model,
            self.get_actual_ext_id_value(channel_id, model, vg7_id))
        if not data:
            return False
        ir_model = self.env[model]
        if hasattr(ir_model, 'synchro'):
            id = ir_model.synchro(self.jacket_vals(
                cache.get_attr(channel_id, 'PREFIX'),
                data), disable_post=True)
        else:
            id = self.synchro(ir_model, self.jacket_vals(
                cache.get_attr(channel_id, 'PREFIX'),
                data), disable_post=True)
        return id

    def create_new_ref(
            self, channel_id, actual_model, key_name, value, ext_value,
            ctx=None, spec=None):
        self.logmsg(1, '>>> create_new_ref(%s,%s,%s,%d)' % (
                    actual_model, key_name, value, (ext_value or -1)))
        ctx = ctx or {}
        cache = self.env['ir.model.synchro.cache']
        xmodel = self.get_xmodel(actual_model, spec)
        loc_ext_id = self.get_loc_ext_id_name(channel_id, xmodel)
        ir_model = self.env[xmodel]
        vals = {key_name: value}
        if ext_value:
            vals[loc_ext_id] = self.get_loc_ext_id_value(
                    channel_id, actual_model, ext_value, spec=spec)
        if (key_name != 'company_id' and
                cache.get_struct_model_attr(
                    actual_model, 'MODEL_WITH_COMPANY') and
                ctx.get('company_id')):
            vals['company_id'] = ctx['company_id']
        if (key_name != 'country_id' and
                cache.get_struct_model_attr(
                    actual_model, 'MODEL_WITH_COUNTRY') and
                ctx.get('country_id')):
            vals['country_id'] = ctx['country_id']
        if (key_name != 'name' and
                cache.get_struct_model_attr(actual_model, 'name')):
            if ext_value:
                vals['name'] = 'Unknown %d' % ext_value
            else:
                vals['name'] = '%s=%s' % (key_name, value)
        elif (key_name != 'code' and
              cache.get_struct_model_attr(actual_model, 'code')):
            if ext_value:
                vals['name'] = 'Unknown %d' % ext_value
            else:
                vals['code'] = '%s=%s' % (key_name, value)
        if actual_model == 'res.partner' and spec in ('delivery', 'invoice'):
            vals['type'] = spec
        try:
            new_value = self.synchro(ir_model, vals, disable_post=True)
            in_queue = cache.get_attr(channel_id, 'IN_QUEUE')
            in_queue.append([xmodel, new_value])
            cache.set_attr(channel_id, 'IN_QUEUE', in_queue)
        except BaseException:
            _logger.info('### Failed %s.synchro(%s)' % (xmodel, vals))
            new_value = -1
        return new_value

    def do_search(self, channel_id, actual_model, req_where,
                  only_id=None, spec=None):

        def exec_search(ir_model, where, has_sequence):
            if has_sequence:
                return ir_model.search(where, order='sequence,id')
            else:
                return ir_model.search(where)

        cache = self.env['ir.model.synchro.cache']
        maybe_dif = False
        has_sequence = cache.get_struct_model_attr(actual_model, 'sequence')
        ir_model = self.env[actual_model]
        if only_id:
            self.logmsg(channel_id,
                        '>>> %s.search(%s)' % (actual_model, req_where))
            rec = exec_search(ir_model,req_where, has_sequence)
            return rec, maybe_dif
        where = [x for x in req_where]
        if actual_model == 'res.partner' and spec in ('delivery', 'invoice'):
            where.append(['type', '=', spec])
        self.logmsg(channel_id,
                    '>>> %s.search(%s)' % (actual_model, where))
        rec = exec_search(ir_model, where, has_sequence)
        if not rec and cache.get_struct_model_attr(actual_model, 'active'):
            where.append(('active', '=', False))
            rec = exec_search(ir_model, where, has_sequence)
        if not rec and actual_model == 'res.partner':
            where = [x for x in req_where]
            self.logmsg(channel_id,
                        '>>> %s.search(%s)' % (actual_model, where))
            rec = exec_search(ir_model, where, has_sequence)
        if not rec:
            if (actual_model in ('res.partner',
                                 'product.product',
                                 'product.template')):
                where = []
                do_query = False
                for cond in req_where:
                    if cond[0] == 'company_id':
                        do_query = True
                    else:
                        where.append(cond)
                if do_query and where:
                    rec = exec_search(ir_model, where, has_sequence)
        if rec:
            if len(rec) > 1:
                maybe_dif = True
            rec = rec[0]
        return rec, maybe_dif

    def get_rec_by_reference(
            self, channel_id, actual_model, name, value,
            ctx=None, mode=None, spec=None):
        mode = mode or '='
        ctx = ctx or {}
        self.logmsg(1, '>>> get_rec_by_reference(%s,%s %s %s)' % (
                    actual_model, name, mode, value))
        cache = self.env['ir.model.synchro.cache']
        ext_key_id = cache.get_model_attr(
            channel_id, actual_model, 'KEY_ID', default='id')
        key_name = cache.get_model_attr(
            channel_id, actual_model, 'MODEL_KEY', default='name')
        xmodel = self.get_xmodel(actual_model, spec)
        loc_ext_id = self.get_loc_ext_id_name(channel_id, xmodel)
        if mode == 'tnl':
            translation_model = self.env['synchro.channel.domain.translation']
            where = [('model', '=', actual_model),
                     ('key', '=', name),
                     ('ext_value', 'ilike', self.dim_text(value))]
            rec = translation_model.search(where)
            if not rec:
                return rec
            value = rec[0].odoo_value
            mode = 'ilike'
        where = [(name, mode, value)]
        if name not in (ext_key_id, loc_ext_id):
            if (cache.get_struct_model_attr(
                    actual_model, 'MODEL_WITH_COMPANY') and
                    ctx.get('company_id')):
                where.append(('company_id', '=', ctx['company_id']))
            if (cache.get_struct_model_attr(
                    actual_model, 'MODEL_WITH_COUNTRY') and
                    ctx.get('country_id')):
                where.append(('country_id', '=', ctx['country_id']))
        rec, maybe_dif = self.do_search(
            channel_id, actual_model, where, spec=spec)
        if not rec and mode != 'tnl' and isinstance(value, basestring):
            rec = self.get_rec_by_reference(
                channel_id, actual_model, name, value,
                ctx=ctx, mode='tnl', spec=spec)
        if not rec:
            if mode == '=' and name == key_name:
                return self.get_rec_by_reference(
                    channel_id, actual_model, name, value,
                    ctx=ctx, mode='ilike', spec=spec)
            elif (name in ('code', 'description') and
                  cache.get_struct_model_attr(
                      actual_model, 'MODEL_WITH_NAME')):
                return self.get_rec_by_reference(
                    channel_id, actual_model, 'name', value,
                    ctx=ctx, mode=mode, spec=spec)
        return rec

    def get_foreign_text(self, channel_id, actual_model, value, is_foreign,
                         ctx=None, spec=None):
        self.logmsg(channel_id, '>>> get_foreign_text(%s,%s,%s,%s)' % (
                    actual_model, value, is_foreign, spec))
        cache = self.env['ir.model.synchro.cache']
        key_name = cache.get_model_attr(
            channel_id, actual_model, 'MODEL_KEY', default='name')
        new_value = False
        rec = self.get_rec_by_reference(
            channel_id, actual_model, key_name, value, ctx=ctx, spec=spec)
        if rec:
            new_value = rec[0].id
        if not new_value:
            new_value = self.create_new_ref(
                channel_id, actual_model, key_name, value, False,
                ctx=ctx, spec=spec)
        if not new_value:
            _logger.error('>>> return %s # get_foreign_text()' % new_value)
        else:
            _logger.info('>>> return %d # get_foreign_text()' % new_value)
        return new_value

    def get_foreign_ref(self, channel_id, actual_model, value_id, is_foreign,
                        ctx=None, spec=None):
        self.logmsg(channel_id, '>>> get_foreign_ref(%s,%d,%s,%s)' % (
                    actual_model, value_id, is_foreign, spec))
        cache = self.env['ir.model.synchro.cache']
        loc_ext_id = self.get_loc_ext_id_name(channel_id, actual_model)
        new_value = False
        rec = False
        ext_value = value_id
        if is_foreign:
            if cache.get_struct_model_attr(actual_model, loc_ext_id):
                if spec:
                    value_id = self.get_loc_ext_id_value(
                        channel_id, actual_model, value_id, spec=spec)
                where = [(loc_ext_id, '=', value_id)]
                rec, maybe_dif = self.do_search(
                    channel_id, actual_model, where, only_id=True)
        else:
            where = [('id', '=', value_id)]
            rec, maybe_dif = self.do_search(
                channel_id, actual_model, where, only_id=True)
        if not rec and is_foreign and ext_value != value_id:
            where = [(loc_ext_id, '=', ext_value)]
            rec, maybe_dif = self.do_search(
                channel_id, actual_model, where, only_id=True)
        if rec:
            new_value = rec.id
        if not new_value:
            xmodel = self.get_xmodel(actual_model, spec)
            if xmodel:
                new_value = self.sync_rec_from_counterpart(
                    channel_id, xmodel, value_id)
        if not new_value:
            new_value = self.create_new_ref(
                channel_id, xmodel, loc_ext_id, new_value, ext_value,
                ctx=ctx, spec=spec)
        if not new_value:
            _logger.error('>>> return %s # get_foreign_ref()' % new_value)
        else:
            _logger.info('>>> return %d # get_foreign_ref())' % new_value)
        return new_value

    def get_foreign_value(self, channel_id, xmodel, value, name, is_foreign,
                          ctx=None, ttype=None, spec=None, format=None):
        self.logmsg(
            channel_id, '>>> get_foreign_value(%s,%s,%s,%s,%s,%s)' % (
                xmodel, name, value, is_foreign, ttype, spec))
        if not value:
            return value
        cache = self.env['ir.model.synchro.cache']
        cache.open(model=xmodel)
        actual_model = self.get_actual_model(xmodel, only_name=True)
        relation = cache.get_struct_model_field_attr(
            actual_model, name, 'relation')
        if not relation:
            raise RuntimeError('No relation for field %s of %s' % (name,
                                                                   xmodel))
        tomany = True if ttype in ('one2many', 'many2many') else False
        if isinstance(value, basestring):
            new_value = self.get_foreign_text(
                channel_id, relation, value, is_foreign,
                ctx=ctx, spec=spec)
            if tomany and new_value:
                new_value = [new_value]
        elif isinstance(value, (list, tuple)):
            new_value = []
            for id in value:
                new_id = self.get_foreign_ref(
                    channel_id, relation, id, is_foreign,
                    ctx=ctx, spec=spec)
                if new_id:
                    new_value.append(new_id)
        else:
            new_value = self.get_foreign_ref(
                channel_id, relation, value, is_foreign,
                ctx=ctx, spec=spec)
            if tomany and new_value:
                new_value = [new_value]
        if format == 'cmd' and new_value and tomany:
            new_value = [(6, 0, new_value)]
        if not new_value:
            _logger.error(
                '### no value (%s) returned from %s!' % (new_value, xmodel))
        elif tomany:
            _logger.info('>>> return %s # get_foreign_value(%s)' % (
                new_value, relation))
        else:
            _logger.info('>>> return %d # get_foreign_value(%s)' % (
                new_value, relation))
        return new_value

    def names_from_ref(self, channel_id, xmodel, ext_ref):
        cache = self.env['ir.model.synchro.cache']
        pfx_depr = '%s_' % cache.get_attr(channel_id, 'PREFIX')
        pfx_ext = '%s:' % cache.get_attr(channel_id, 'PREFIX')
        loc_ext_id = self.get_loc_ext_id_name(channel_id, xmodel)
        ext_key_id = cache.get_model_attr(
            channel_id, xmodel, 'KEY_ID', default='id')
        if ext_ref == loc_ext_id:
            # Case #1 - field is external id like <vg7_id>
            is_foreign = True
            loc_name = ext_name = ext_ref
        elif ext_ref.startswith(pfx_depr):
            # Case #2 - (deprecated) field like <vg7_order_id>:
            #           local name is odoo but value id is of counterpart ref
            is_foreign = True
            loc_name = ext_ref[len(pfx_depr):]
            if loc_name == 'id':
                loc_name = ext_name = ext_ref
            else:
                ext_name = cache.get_model_field_attr(
                    channel_id, xmodel, loc_name, 'LOC_FIELDS', default='')
                if ext_name.startswith('.'):
                        ext_name = ''
            _logger.warning('Deprecate field name %s!' % ext_ref)
        elif ext_ref.startswith(pfx_ext):
            # Case #3 - field like <vg7:order_id>: both name and value are
            #           of counterpart refs
            is_foreign = True
            ext_name = ext_ref[len(pfx_ext):]
            if ext_name == ext_key_id:
                loc_name = loc_ext_id
            else:
                loc_name = cache.get_model_field_attr(
                    channel_id, xmodel, ext_name, 'EXT_FIELDS', default='')
            if loc_name.startswith('.'):
                loc_name = ''
        else:
            # Case #4 - field and value are Odoo
            is_foreign = False
            ext_name = loc_name = ext_ref
        return ext_name, loc_name, is_foreign

    def get_default_n_apply(self, channel_id, xmodel, loc_name, ext_name,
                            is_foreign, ttype=None):
        cache = self.env['ir.model.synchro.cache']
        actual_model = self.get_actual_model(xmodel, only_name=True)
        if not cache.get_attr(channel_id, actual_model):
            return '', ''
        default = cache.get_model_field_attr(
            channel_id, xmodel, loc_name or '.%s' % ext_name, 'APPLY',
            default='')
        if not default:
            default = cache.get_model_field_attr(
                channel_id, actual_model, loc_name or '.%s' % ext_name,
                'APPLY', default='')
        if default.endswith('()'):
            apply = ''
            for fct in default.split(','):
                if not fct.startswith('not') or is_foreign:
                    apply = '%s,%s' % (apply, 'apply_%s' % default[:-2])
            if apply.startswith(','):
                apply = apply[1:]
            default = False
        elif default:
            apply = 'apply_set_value'
        else:
            apply = ''
        if ttype == 'boolean':
            default = os0.str2bool(default, True)
        spec = cache.get_model_field_attr(
            channel_id, xmodel, loc_name or '.%s' % ext_name, 'SPEC',
            default='')
        return default, apply, spec

    def map_to_internal(self, channel_id, xmodel, vals):

        def rm_ext_value(vals, loc_name, ext_name, ext_ref, is_foreign):
            if (is_foreign or loc_name != ext_name) and ext_ref in vals:
                if loc_name and loc_name not in vals:
                    vals[loc_name] = vals[ext_ref]
                del vals[ext_ref]
            return vals

        def do_apply(channel_id, vals, loc_name, ext_ref, loc_ext_id,
                    apply, default):
            ir_apply = self.env['ir.model.synchro.apply']
            for fct in apply.split(','):
                if hasattr(ir_apply, fct):
                    vals = getattr(ir_apply, fct)(channel_id,
                                              vals,
                                              loc_name,
                                              ext_ref,
                                              loc_ext_id,
                                              default=default)
                    self.logmsg(channel_id,
                                '>>> %s=%s(%s,%s,%s,%s)' % (
                                    vals.get(loc_name),
                                    fct,
                                    loc_name,
                                    ext_ref,
                                    loc_ext_id,
                                    default))
            return vals

        def do_apply_n_clean(channel_id, vals, loc_name, ext_name,
                             ext_ref, loc_ext_id, apply, default, is_foreign):
            vals = do_apply(channel_id, vals, loc_name, ext_ref, loc_ext_id,
                            apply, default)
            vals = rm_ext_value(vals, loc_name, ext_name, ext_ref, is_foreign)
            return vals

        def priority_fields(channel_id, vals):
            field_list = []
            last_fields = []
            for ext_ref in vals.keys():
                ext_name, loc_name, is_foreign = \
                    self.names_from_ref(channel_id, xmodel, ext_ref)
                if loc_name in ('is_company', 'country_id', 'company_id',
                                'street'):
                    field_list.insert(0, ext_ref)
                elif loc_name in ('product_uom',
                                  'partner_invoice_id',
                                  'partner_shipping_id',
                                  'electronic_invoice_subjected'):
                    last_fields.append(ext_ref)
                else:
                    field_list.append(ext_ref)
            return field_list + last_fields

        def check_4_double_field_id(vals):
            for nm, nm_id in (('vg7:country', 'vg7:country_id'),
                              ('vg7:region', 'vg7:region_id'),
                              ('vg7_um', 'vg7:um_id'),
                              ('vg7:tax_id', 'vg7:tax_code_id'),
                              ('vg7:payment', 'vg7:payment_id')):
                if (not vals.get(nm_id) and vals.get(nm)):
                    vals[nm_id] = vals[nm]
                    self.logmsg(
                        channel_id,
                        '### Field <%s> renamed as <%s>' %
                        (nm, nm_id))
                elif (vals.get(nm_id) and vals.get(nm)):
                    self.logmsg(
                        channel_id,
                        '### Field <%s> overtaken by <%s>' %
                        (nm, nm_id))
                    del vals[nm]
            return vals

        vals = check_4_double_field_id(vals)
        field_list = priority_fields(channel_id, vals)

        cache = self.env['ir.model.synchro.cache']
        loc_ext_id = self.get_loc_ext_id_name(channel_id, xmodel)
        actual_model = self.get_actual_model(xmodel, only_name=True)
        ctx = {
            'company_id': cache.get_attr(channel_id, 'COMPANY_ID'),
            'country_id': cache.get_attr(channel_id, 'COUNTRY_ID'),
            'is_company': True,
            'ext_key_id': cache.get_model_attr(
                channel_id, xmodel, 'KEY_ID', default='id'),
        }
        for ext_ref in field_list:
            if (isinstance(vals[ext_ref], basestring) and
                    not vals[ext_ref].strip()):
                del vals[ext_ref]
                continue
            ext_name, loc_name, is_foreign = self.names_from_ref(
                channel_id, xmodel, ext_ref)
            default, apply, spec = self.get_default_n_apply(
                channel_id, xmodel, loc_name, ext_name, is_foreign,
                ttype=cache.get_struct_model_field_attr(
                    xmodel, ext_name, 'ttype'))
            if not loc_name or not cache.get_struct_model_attr(
                    actual_model, loc_name):
                if is_foreign and apply:
                    vals = do_apply(
                        channel_id, vals, loc_name, ext_ref, loc_ext_id,
                        apply, default)
                else:
                    self.logmsg(
                        channel_id,
                        '### Field <%s> does not exist in model %s' %
                        (ext_ref, xmodel))
                vals = rm_ext_value(vals, loc_name, ext_name, ext_ref,
                                    is_foreign)
                continue
            if (cache.get_struct_model_field_attr(
                    actual_model, loc_name, 'ttype') in ('many2one',
                                                         'integer') and
                    isinstance(vals[ext_ref], basestring) and
                    vals[ext_ref].isdigit()):
                vals[ext_ref] = int(vals[ext_ref])
            elif (cache.get_struct_model_field_attr(
                    actual_model, loc_name, 'ttype') == 'boolean' and
                    isinstance(vals[ext_ref], basestring)):
                vals[ext_ref] = os0.str2bool(vals[ext_ref], True)
            if is_foreign:
                # Field like <vg7_id> with external ID in local DB
                # if loc_ext_ref in cache.get_struct_attr(actual_model):
                if loc_name == loc_ext_id:
                    vals[ext_ref] = self.get_loc_ext_id_value(
                            channel_id, xmodel, vals[ext_ref])
                    vals = rm_ext_value(vals, loc_name, ext_name, ext_ref,
                                        is_foreign)
                    continue
                # If counterpart partner supplies both
                # local and external values, just process local value
                elif loc_name in vals:
                    del vals[ext_ref]
                    continue
            if cache.get_struct_model_field_attr(
                    actual_model, loc_name, 'ttype') in (
                    'many2one', 'one2many', 'many2many'):
                vals[loc_name] = self.get_foreign_value(
                    channel_id, xmodel, vals[ext_ref], loc_name, is_foreign,
                    ctx=ctx,
                    ttype=cache.get_struct_model_field_attr(
                        actual_model, loc_name, 'ttype'),
                    spec=spec, format='cmd')
            vals = do_apply_n_clean(
                channel_id, vals,
                loc_name, ext_name, ext_ref, loc_ext_id,
                apply, default, is_foreign)
            if (loc_name in vals and
                    vals[loc_name] is False and
                    cache.get_struct_model_field_attr(
                        actual_model, loc_name, 'ttype') != 'boolean'):
                del vals[loc_name]
            if loc_name in ctx and vals.get(loc_name):
                ctx[loc_name] = vals[loc_name]

        for loc_name in ctx:
            if (loc_name not in vals and
                    loc_name in cache.get_struct_attr(actual_model)):
                vals[loc_name] = ctx[loc_name]
        self.logmsg(channel_id,
                    '### return %s  # map_to_internal' % vals)
        return vals

    def set_default_values(self, channel_id, xmodel, vals):
        self.logmsg(channel_id,
                    '>>> %s.set_default_values()' % xmodel)
        actual_model = self.get_actual_model(xmodel, only_name=True)
        ir_apply = self.env['ir.model.synchro.apply']
        cache = self.env['ir.model.synchro.cache']
        loc_ext_id = self.get_loc_ext_id_name(channel_id, xmodel)
        for ext_ref in cache.get_model_attr(channel_id, xmodel, 'APPLY'):
            ext_name, loc_name, is_foreign = \
                self.names_from_ref(channel_id, xmodel, ext_ref)
            if loc_name not in vals:
                if loc_name in cache.get_model_attr(channel_id,
                                                    xmodel, 'LOC_FIELDS'):
                    ext_name = cache.get_model_field_attr(
                        channel_id, xmodel, loc_name, 'LOC_FIELDS')
                    default, apply, spec = self.get_default_n_apply(
                        channel_id, xmodel, loc_name, ext_name, is_foreign,
                        ttype=cache.get_struct_model_field_attr(
                            xmodel, loc_name, 'ttype'))
                    required = (cache.get_struct_model_field_attr(
                        actual_model, ext_ref, 'required') or
                                cache.get_model_field_attr(
                                    channel_id, xmodel, loc_name, 'REQUIRED'))
                    if (required or ext_name[0] == '.'):
                        for fct in apply.split(','):
                            if hasattr(ir_apply, fct):
                                vals = getattr(ir_apply, fct)(
                                    channel_id,
                                    vals,
                                    loc_name,
                                    ext_ref,
                                    loc_ext_id,
                                    default=default)
                                self.logmsg(channel_id,
                                            '>>> %s = apply(%s,%s,%s,%s)' % (
                                                vals.get(loc_name),
                                                fct,
                                                loc_name,
                                                ext_ref,
                                                default))
        return vals

    def bind_record(self, channel_id, xmodel, vals, constraints, ctx=None):

        def add_constraints(where, constraints):
            for constr in constraints:
                add_where = False
                if constr[0] in vals:
                    constr[0] = vals[constr[0]]
                    add_where = True
                if constr[-1] in vals:
                    constr[-1] = vals[constr[-1]]
                    add_where = True
                if add_where:
                    where.append(constr)
            return where

        _logger.info(
            '> bind_record(%s,%s)' % (xmodel, constraints))  # debug

        ctx = ctx or {}
        actual_model = self.get_actual_model(xmodel, only_name=True)
        spec = self.get_spec_from_xmodel(xmodel)
        spec = spec if spec != 'supplier' else ''
        if actual_model == 'res.partner' and spec in ('delivery' 'invoice'):
            ctx['type'] = spec
        cache = self.env['ir.model.synchro.cache']
        loc_ext_id = self.get_loc_ext_id_name(channel_id, xmodel)
        use_sync = cache.get_struct_model_attr(actual_model, loc_ext_id)
        rec = False
        candidate = False
        if loc_ext_id in vals and use_sync:
            where = [
                (loc_ext_id, '=', self.get_loc_ext_id_value(
                    channel_id, xmodel, vals[loc_ext_id]))]
            # where = add_constraints(where, constraints)
            rec, maybe_dif = self.do_search(
                channel_id, actual_model, where, only_id=True)
        if not rec:
            for keys in cache.get_model_attr(channel_id, xmodel, 'SKEYS'):
                where = []
                if isinstance(keys, basestring):
                    keys = [keys]
                for key in keys:
                    if key not in vals:
                        if (key == 'dim_name' and vals.get('name')):
                            where.append(('dim_name',
                                          '=',
                                          self.dim_text(vals['name'])))
                        elif key in ctx:
                            where.append((key, '=', ctx[key]))
                        else:
                            where = []
                            break
                    else:
                        where.append((key, '=', os0.b(vals[key])))
                if where:
                    where = add_constraints(where, constraints)
                    # if spec:
                    #     where.append(('type', '=', spec))
                    if loc_ext_id and use_sync:
                        where.append('|')
                        where.append((loc_ext_id, '=', False))
                        where.append((loc_ext_id, '=', 0))
                    rec, maybe_dif = self.do_search(
                        channel_id, actual_model, where, spec=spec)
                    if rec:
                        break
                    if maybe_dif and not candidate:
                        candidate = rec
        if not rec and candidate:
            rec = candidate
        if rec:
            self.logmsg(channel_id,
                        '### synchro: found id=%d' % rec.id)
            return rec.id, rec
        return -1, None

    def get_xmlrpc_response(self, channel_id, xmodel, ext_id=False):

        def cnx(endpoint):
            cnx = cache.get_attr(channel_id, 'CNX')
            if not cnx:
                try:
                    cnx = oerplib.OERP(server=endpoint,
                                       protocol='xmlrpc')
                    cache.set_attr(channel_id, 'CNX', cnx)
                except BaseException:  # pragma: no cover
                    cnx = False
            return cnx

        def browse_rec(cache, actual_model, ext_id):
            try:
                rec = cnx.browse(actual_model, ext_id)
            except:
                rec = False
            data = {}
            if rec:
                for field in cache.get_struct_attr(actual_model):
                    if (hasattr(rec, field) and
                        cache.is_struct(field) and
                            not cache.get_struct_model_field_attr(
                                actual_model, field, 'readonly')):
                        if isinstance(rec[field], (bool, int, long)):
                            data['%s:%s' % (prefix, field)] = rec[field]
                        elif cache.get_struct_model_field_attr(
                                actual_model, field, 'ttype') == 'many2one':
                            try:
                                data['%s:%s' % (prefix, field)] = rec[field].id
                            except:
                                data['%s:%s' % (prefix, field)] = rec[field]
                        elif cache.get_struct_model_field_attr(
                                    actual_model, field, 'ttype') in (
                                    'one2many', 'many2many'):
                            value = []
                            # TODO: how to get tomany values?
                            # for id in rec[field]:
                            #     value.append(id)
                            data['%s:%s' % (prefix, field)] = value
                        else:
                            data['%s:%s' % (prefix, field)] = rec[field]
                if data:
                    data['id'] = ext_id
            return data

        cache = self.env['ir.model.synchro.cache']
        endpoint = cache.get_attr(channel_id, 'COUNTERPART_URL')
        if not endpoint:
            _logger.error(
                'Channel %d without connection parameters!' % channel_id)
            return False
        if len(endpoint.split('@')) > 1:
            login = endpoint.split('@')[0]
            endpoint = endpoint.split('@')[1]
        else:
            login = self.env.user.login
        cnx = cnx(endpoint)
        if not cnx:
            self.logmsg(channel_id,
                        'Not response from %s' % endpoint)
        database = cache.get_attr(channel_id, 'CLIENT_KEY')
        passwd = cache.get_attr(channel_id, 'PASSWORD')
        session = cnx.login(database=database,
                            user=login,
                            passwd=passwd)
        if not session:
            self.logmsg(channel_id,
                        'Logion response error (%s,%s,%s)' %
                        (database, login, passwd))
        prefix = cache.get_attr(channel_id, 'PREFIX')
        actual_model = self.get_actual_model(xmodel, only_name=True)
        if ext_id:
            return browse_rec(cache, actual_model, ext_id)
        else:
            try:
                ids = cnx.search(actual_model, [])
            except:
                ids = []
            if not ids:
                return ids
            datas = []
            for id in ids:
                datas.append([browse_rec(cache, actual_model, id)])
            return datas
        return {}

    def get_json_response(self, channel_id, xmodel, ext_id=False):
        cache = self.env['ir.model.synchro.cache']
        endpoint = cache.get_attr(channel_id, 'COUNTERPART_URL')
        if not endpoint:
            _logger.error(
                'Channel %d without connection parameters!' % channel_id)
            return False
        ext_model = cache.get_model_attr(channel_id, xmodel, 'BIND')
        if not ext_model:
            _logger.error('Model %s not managed by external partner!' % xmodel)
            return False
        if not ext_id:
            url = os.path.join(endpoint, ext_model)
        else:
            url = os.path.join(endpoint, ext_model, str(ext_id))
        headers = {'Authorization': 'access_token %s' %
                   cache.get_attr(channel_id, 'CLIENT_KEY')}
        self.logmsg(channel_id,
                    '>>> vg7_requests(%s,%s)' % (url, headers))
        try:
            response = requests.get(url, headers=headers, verify=False)
        except BaseException:
            response = False
        if response:
            datas = response.json()
            return datas
        self.logmsg(channel_id,
                    'Response error %s (%d,%s,%s,%s)' %
                    (getattr(response, 'status_code', 'N/A'),
                     channel_id,
                     url,
                     cache.get_attr(channel_id, 'CLIENT_KEY'),
                     cache.get_attr(channel_id, 'PREFIX')))
        cache.clean_cache(channel_id=channel_id, model=xmodel)
        return {}

    def get_csv_response(self, channel_id, xmodel, ext_id=False):
        cache = self.env['ir.model.synchro.cache']
        endpoint = cache.get_attr(channel_id, 'EXCHANGE_PATH')
        if not endpoint:
            _logger.error(
                'Channel %d without connection parameters!' % channel_id)
            return False
        ext_model = cache.get_model_attr(channel_id, xmodel, 'BIND')
        ext_key_id = cache.get_model_attr(
            channel_id, xmodel, 'KEY_ID', default='id')
        if not ext_model:
            _logger.error('Model %s not managed by external partner!' % xmodel)
            return False
        file_csv = os.path.expanduser(
            os.path.join(endpoint, ext_model + '.csv'))
        self.logmsg(channel_id,
                    '>>> csv_requests(%s)' % file_csv)
        res = []
        if not os.path.isfile(file_csv):
            return res
        with open(file_csv, 'rb') as f:
            hdr = False
            reader = csv.DictReader(f,
                                    fieldnames=[],
                                    restkey='undef_name')
            for line in reader:
                row = line['undef_name']
                if not hdr:
                    row_id = 0
                    hdr = row
                    continue
                row_id += 1
                row_res = {ext_key_id: row_id}
                row_billing = {}
                row_shipping = {}
                row_contact = {}
                for ix,value in enumerate(row):
                    if (isinstance(value, basestring) and
                            value.isdigit() and
                            not value.startswith('0')):
                        value = int(value)
                    if hdr[ix] == ext_key_id:
                        if not value:
                            continue
                        row_id = value
                    if hdr[ix].startswith('billing_'):
                        row_billing[hdr[ix]] = value
                    elif hdr[ix].startswith('shipping_'):
                        row_shipping[hdr[ix]] = value
                    elif hdr[ix].startswith('contact_'):
                        row_contact[hdr[ix]] = value
                    else:
                        row_res[hdr[ix]] = value
                if row_billing:
                    row_res['billing'] = row_billing
                if row_shipping:
                    row_res['shipping'] = row_shipping
                if row_contact:
                    row_res['contact'] = row_contact
                if ext_id and row_res[ext_key_id] != ext_id:
                    continue
                if ext_id:
                    res = row_res
                    break
                res.append(row_res)
        return res

    def get_counterpart_response(self, channel_id, xmodel, ext_id=False):
        cache = self.env['ir.model.synchro.cache']
        cache.open(model=xmodel)
        method = cache.get_attr(channel_id, 'METHOD')
        if method == 'XML':
            return self.get_xmlrpc_response(channel_id, xmodel, ext_id)
        elif method == 'JSON':
            return self.get_json_response(channel_id, xmodel, ext_id)
        elif method == 'CSV':
            return self.get_csv_response(channel_id, xmodel, ext_id)

    def assign_channel(self, vals):
        cache = self.env['ir.model.synchro.cache']
        odoo_prio = 9999
        channel_prio = 9999
        odoo_channel = def_channel = channel_from = False
        for channel_id in cache.get_channel_list():
            if channel_from:
                break
            pfx_ext = '%s:' % cache.get_attr(channel_id, 'PREFIX')
            pfx_depr = '%s_' % cache.get_attr(channel_id, 'PREFIX')
            if (cache.get_attr(channel_id, 'PRIO') < channel_prio):
                def_channel = channel_id
                channel_prio = cache.get_attr(channel_id, 'PRIO')
            if (cache.get_attr(channel_id, 'IDENTITY') == 'odoo' and
                    cache.get_attr(channel_id, 'PRIO') < odoo_prio):
                odoo_channel = channel_id
                odoo_prio = cache.get_attr(channel_id, 'PRIO')
            for ext_ref in vals:
                if (ext_ref.startswith(pfx_ext) or
                        ext_ref.startswith(pfx_depr)):
                    channel_from = channel_id
                    break
        if not channel_from:
            if channel_prio < odoo_prio:
                channel_from = def_channel
            else:
                channel_from = odoo_channel
        return channel_from

    @api.model
    def synchro(self, cls, vals, disable_post=None):
        vals = unicodes(vals)
        xmodel = cls.__class__.__name__
        ir_model = self.get_actual_model(xmodel)
        _logger.info('> %s.synchro(%s,%s)' % (xmodel, vals, disable_post))
        if 'vg7_id' in vals and 'vg7:id' not in vals:
            vals['vg7:id'] = vals['vg7_id']
            del vals['vg7_id']
            _logger.warning('Deprecate field name %s: please use %s!' % (
                'vg7_id', 'vg7:id'))

        actual_model = self.get_actual_model(xmodel, only_name=True)
        cache = self.env['ir.model.synchro.cache']
        cache.open(model=xmodel, cls=cls)
        if hasattr(cls, 'CONTRAINTS'):
            constraints = cls.CONTRAINTS
        else:
            constraints = []
        has_state = cache.get_struct_model_attr(
            xmodel, 'MODEL_STATE', default=False)
        has_2delete = cache.get_struct_model_attr(
            xmodel, 'MODEL_2DELETE', default=False)
        if has_2delete:
            vals['to_delete'] = False
        lines_of_rec = cache.get_struct_model_attr(
            xmodel, 'LINES_OF_REC', default=False)

        channel_id = self.assign_channel(vals)
        if not channel_id:
            cache.clean_cache()
            _logger.error('!-6! No channel found!')
            return -6
        self.channel_id = channel_id
        if hasattr(self.env[xmodel], 'preprocess'):
            vals, spec = self.env[xmodel].preprocess(channel_id, vals)
            if spec:
                xmodel = self.get_xmodel(actual_model, spec)
                actual_model = self.get_actual_model(xmodel)
                cache.open(model=xmodel)
        vals = self.map_to_internal(channel_id, xmodel, vals)
        id = -1
        rec = None
        if 'id' in vals:
            id = vals.pop('id')
            rec = ir_model.search([('id', '=', id)])
            if not rec or rec.id != id:
                _logger.error('!-3! ID %d does not exist in %s' %
                              (id, xmodel))
                return -3
            id = rec.id
            self.logmsg(channel_id, '### synchro: found id=%s.%d' % (
                actual_model, id))
        if id < 0:
            id, rec = self.bind_record(channel_id, xmodel, vals, constraints)
        if has_state:
            vals, erc = self.set_state_to_draft(xmodel, rec, vals)
            if erc < 0:
                _logger.error('!%d! Returned error code!' % erc)
                return erc
            # TODO: Workaround
            if xmodel == 'stock.picking.package.preparation':
                id = -1

        self.drop_invalid_fields(xmodel, vals)
        if id > 0:
            if actual_model == 'res.partner':
                if ('codice_destinatario' in vals and
                        not vals.get('codice_destinatario')):
                    del vals['codice_destinatario']
            try:
                rec = ir_model.with_context(
                    {'lang': self.env.user.lang}).browse(id)
                vals = self.drop_protected_fields(
                    channel_id, xmodel, vals, rec)
                if vals:
                    if (actual_model == 'res.partner' and
                            vals.get('electronic_invoice_subjected') and
                            not vals.get('codice_destinatario')):
                        vals['codice_destinatario'] = rec.codice_destinatario
                        if not vals['codice_destinatario']:
                            del vals['electronic_invoice_subjected']
                            del vals['codice_destinatario']
                    rec.write(vals)
                    self.logmsg(channel_id,
                                '>>> synchro: %s.write(%s)' % (
                                    actual_model, vals))
                else:
                    self.logmsg(channel_id,
                                '### Nothing to update(%s.%d)' % (
                                    actual_model, id))
                if lines_of_rec and hasattr(rec, lines_of_rec):
                    for line in rec[lines_of_rec]:
                        if not hasattr(line, 'to_delete'):
                            break
                        line.write({'to_delete': True})
            except BaseException, e:
                _logger.error('%s writing %s ID=%d' %
                              (e, actual_model, id))
                return -2
        else:
            vals = self.set_default_values(channel_id, xmodel, vals)
            if vals:
                if (xmodel == 'res.partner' and
                        vals.get('electronic_invoice_subjected') and
                        not vals.get('codice_destinatario')):
                    del vals['electronic_invoice_subjected']
                try:
                    id = ir_model.create(vals).id
                    self.logmsg(
                        channel_id,
                        '>>> synchro: %d=%s.create(%s)' % (id, xmodel, vals))
                except BaseException, e:
                    _logger.error('!-1! %s creating %s' % (e, xmodel))
                    return -1
            else:
                _logger.error('### Missing data to create(%s)!!' % xmodel)
                return -7
        if (id > 0 and not disable_post):
            if hasattr(self.env[xmodel], 'postprocess'):
                self.env[xmodel].postprocess(channel_id, id, vals)
            self.synchro_queue(channel_id)
        _logger.info('!%d! Returned ID of %s' % (id, xmodel))
        return id

    @api.model
    def commit(self, cls, loc_id, ext_id=None):
        xmodel = cls.__class__.__name__
        _logger.info('> %s.commit(%d,%d)' % (xmodel, loc_id, ext_id or -1))
        cache = self.env['ir.model.synchro.cache']
        cache.open(model=xmodel, cls=cls)
        has_state = cache.get_struct_model_attr(
            xmodel, 'MODEL_STATE', default=False)
        lines_of_rec = cache.get_struct_model_attr(
            xmodel, 'LINES_OF_REC', default=False)
        model_line = cache.get_struct_model_attr(xmodel, 'LINE_MODEL')
        if not has_state and not lines_of_rec and not model_line:
            _logger.error('!-5! Invalid structure of %s!' % xmodel)
            return -5
        # Retrieve header id field
        parent_id = cache.get_struct_model_attr(model_line, 'PARENT_ID')
        if not parent_id:
            _logger.error('!-5! Invalid structure of %s!' % xmodel)
            return -5
        if not loc_id and ext_id:
            loc_id = self.bind_record(
                1,
                xmodel,
                {'id': ext_id},
                [], False,)
        try:
            rec_2_commit = self.get_actual_model(xmodel).browse(loc_id)
        except:
            _logger.error('!-3! Errore retriving %s.%d!' % (xmodel, loc_id))
            return -3
        if cache.get_struct_model_attr(model_line, 'MODEL_2DELETE'):
            ir_model = self.get_actual_model(model_line)
            for rec in ir_model.search([(parent_id, '=', loc_id),
                                        ('to_delete', '=', True)]):
                rec.unlink()
        loc_id = self.set_actual_state(xmodel, rec_2_commit)
        if loc_id < 0:
            _logger.error('!%d! Committed ID' % loc_id)
        else:
            _logger.info('!%d! Committed ID' % loc_id)
        return loc_id

    def jacket_vals(self, prefix, data):
        vals = {}
        for name in data:
            if name.startswith(prefix):
                vals[name] = data[name]
            else:
                vals['%s:%s' % (prefix, name)] = data[name]
        return vals

    @api.model
    def synchro_queue(self, channel_id):
        cache = self.env['ir.model.synchro.cache']
        max_ctr = 16
        queue = cache.get_attr(channel_id, 'IN_QUEUE')
        while queue:
            if max_ctr == 0:
                break
            max_ctr -= 1
            item = queue.pop(0)
            xmodel = item[0]
            loc_id = item[1]
            _logger.info('> pulling(%s,%d)?' % (xmodel, loc_id))
            rec = self.get_actual_model(xmodel).browse(loc_id)
            loc_ext_id = self.get_loc_ext_id_name(channel_id, xmodel)
            if hasattr(rec, loc_ext_id):
                # commit previous record
                self.env.cr.commit()  # pylint: disable=invalid-commit
                self.synchro_one_record(
                    channel_id, xmodel, getattr(rec, loc_ext_id))

    @api.multi
    def pull_recs_2_complete(self, only_model=None):
        _logger.info('> pull_recs_2_complete(%s)' % only_model)
        cache = self.env['ir.model.synchro.cache']
        cache.open()
        for channel_id in cache.get_channel_list():
            for xmodel in cache.get_attr_list(channel_id):
                if not cache.is_struct(xmodel):
                    continue
                if not cache.get_struct_model_attr(xmodel, 'MODEL_WITH_NAME'):
                    continue
                if only_model and xmodel == only_model:
                    continue
                self.logmsg(channel_id, '### Pulling %s' % xmodel)
                ir_model = self.env[xmodel]
                recs = ir_model.search([('name', 'like', 'Unknown ')])

                loc_ext_id = self.get_loc_ext_id_name(channel_id, xmodel)
                for rec in recs:
                    id = False
                    if hasattr(rec, loc_ext_id):
                        id = getattr(rec, loc_ext_id)
                    if not id:
                        id = int(rec.name[8:])
                    if not id:
                        continue
                    datas = self.get_counterpart_response(channel_id,
                                                          xmodel,
                                                          id=id)
                    if not datas:
                        continue
                    if not isinstance(datas, (list, tuple)):
                        datas = [datas]
                    for data in datas:
                        if not data:
                            continue
                        ir_model.synchro(self.jacket_vals(
                            cache.get_attr(channel_id, 'PREFIX'),
                            data))
                        # commit every table to avoid too big transaction
                        self.env.cr.commit()   # pylint: disable=invalid-commit
            _logger.info('Channel %d successfuly pulled' % channel_id)

    @api.multi
    def pull_full_records(self,
                          force=None, only_model=None, only_complete=None):
        _logger.info('> pull_full_records(%s,%s)' % (
            force, only_model))
        cache = self.env['ir.model.synchro.cache']
        cache.open()
        for channel_id in cache.get_channel_list():
            where = [('synchro_channel_id', '=', channel_id)]
            if only_model:
                where.append(('name', '=', only_model))
            model_list = [x.name for x in self.env[
                'synchro.channel.model'].search(where,
                    order='sequence')]
            for xmodel in model_list:
                if not cache.is_struct(xmodel):
                    continue
                if (only_complete and
                        not cache.get_struct_model_attr(
                            xmodel, 'MODEL_WITH_NAME')):
                    continue
                cache.open(model=xmodel)
                if (not only_complete and
                        not cache.get_model_attr(
                            channel_id, xmodel, '2PULL', default=False)):
                    self.logmsg(channel_id,
                                '### Model %s not pullable' % xmodel)
                    continue
                self.logmsg(channel_id, '### Pulling %s' % xmodel)
                ir_model = self.env[xmodel]
                datas = self.get_counterpart_response(channel_id, xmodel)
                if not datas:
                    continue
                if not isinstance(datas, (list, tuple)):
                    datas = [datas]
                ext_key_id = cache.get_model_attr(
                    channel_id, xmodel, 'KEY_ID', default='id')
                for data in datas:
                    if not data:
                        continue
                    if ext_key_id not in data:
                        self.logmsg(channel_id,
                                    'Data received of model %s w/o id' %
                                    xmodel)
                        continue
                    if isinstance(data[ext_key_id], (int, long)):
                        id = data[ext_key_id]
                    else:
                        id = int(data[ext_key_id])
                    loc_ext_id = self.get_loc_ext_id_name(channel_id, xmodel)
                    if not force and ir_model.search([(loc_ext_id, '=', id)]):
                        continue
                    try:
                        ir_model.synchro(self.jacket_vals(
                            cache.get_attr(channel_id, 'PREFIX'),
                            data))
                        if hasattr(ir_model, 'synchro'):
                            ir_model.synchro(self.jacket_vals(
                                cache.get_attr(channel_id, 'PREFIX'),
                                data))
                        else:
                            self.synchro(ir_model, self.jacket_vals(
                                cache.get_attr(channel_id, 'PREFIX'),
                                data))
                        # commit every table to avoid too big transaction
                        self.env.cr.commit()   # pylint: disable=invalid-commit
                    except BaseException:
                        self.logmsg(channel_id,
                                    'External id %d error pulling from %s' %
                                    (id, xmodel))
            _logger.info('Channel %d successfuly pulled' % channel_id)

    @api.model
    def synchro_one_record(self, channel_id, xmodel, vg7_id,
                           disable_post=None):
        _logger.info('> synchro_one_record(%s,%d)' % (xmodel, vg7_id))
        data = self.get_counterpart_response(channel_id, xmodel, vg7_id)
        if not data:
            return
        if isinstance(data, (list, tuple)):
            data = data[0]
        cache = self.env['ir.model.synchro.cache']
        ext_key_id = cache.get_model_attr(
            channel_id, xmodel, 'KEY_ID', default='id')
        if ext_key_id not in data:
            self.logmsg(channel_id,
                        'Data received of model %s w/o id' %
                        xmodel)
            return
        ir_model = self.env[xmodel]
        if hasattr(ir_model, 'synchro'):
            ir_model.synchro(self.jacket_vals(
                cache.get_attr(channel_id, 'PREFIX'),
                data), disable_post=disable_post)
        else:
            self.synchro(ir_model, self.jacket_vals(
                cache.get_attr(channel_id, 'PREFIX'),
                data), disable_post=disable_post)

    @api.multi
    def pull_record(self, cls, channel_id=None):
        '''Button synchronize at web page'''
        cache = self.env['ir.model.synchro.cache']
        for rec in cls:
            model = cls.__class__.__name__
            cache.open(model=model, cls=cls)
            if not cache.is_struct(model):
                continue
            for channel_id in cache.get_channel_list():
                identity = cache.get_attr(channel_id, 'IDENTITY')
                loc_ext_id = self.get_loc_ext_id_name(channel_id, model)
                if hasattr(rec, loc_ext_id):
                    xmodel = model
                    ext_id = getattr(rec, loc_ext_id)
                    if identity == 'vg7':
                        if model == 'res.partner':
                            if ext_id > 200000000:
                                xmodel = '%s.invoice' % model
                            elif ext_id > 100000000:
                                xmodel = '%s.shipping' % model
                                cache.open(model=xmodel)
                            ext_id = self.get_actual_ext_id_value(
                                channel_id, xmodel, ext_id)
                    if ext_id and (identity != 'vg7' or
                                   xmodel != 'res.partner.invoice'):
                        self.synchro_one_record(channel_id, xmodel, ext_id)
                    if identity == 'vg7' and model == 'res.partner':
                        xmodel = 'res.partner.supplier'
                        loc_ext_id = self.get_loc_ext_id_name(
                            channel_id, xmodel)
                        if loc_ext_id:
                            ext_id = getattr(rec, loc_ext_id)
                            ext_id = self.get_actual_ext_id_value(
                                channel_id, xmodel, ext_id)
                            if ext_id:
                                cache.open(model=xmodel)
                                self.synchro_one_record(
                                    channel_id, xmodel, ext_id)

    @api.model
    def trigger_one_record(self, ext_model, vg7_id):
        _logger.info('> trigger_one_record(%s,%s)' % (
            ext_model, vg7_id or -1))
        cache = self.env['ir.model.synchro.cache']
        for channel_id in cache.get_channel_list():
            for model in cache.get_attr_list(channel_id):
                if cache.is_struct(model):
                    continue
                if ext_model == cache.get_model_attr(
                        channel_id, model, 'BIND'):
                    self.logmsg(
                        channel_id, '### Pulling %s.%d' % (model, vg7_id))
                    self.synchro_one_record(channel_id, model, vg7_id)


class IrModelSynchroApply(models.Model):
    _name = 'ir.model.synchro.apply'
    _inherit = 'ir.model'


    def apply_set_value(self, channel_id, vals, loc_name,
                            ext_ref, loc_ext_id, default=None):
        if loc_name not in vals:
            if vals.get(ext_ref):
                vals[loc_name] = vals[ext_ref]
            elif default:
                vals[loc_name] = default
        return vals

    def apply_set_tmp_name(self, channel_id, vals, loc_name,
                               ext_ref, loc_ext_id, default=None):
        if loc_name in vals and vals[loc_name]:
            return vals
        if vals.get(ext_ref):
            vals[loc_name] = vals[ext_ref]
        elif default:
            vals[loc_name] = default
        elif loc_ext_id in vals:
            if not isinstance(vals[loc_ext_id], (int, long)):
                vals[loc_ext_id] = int(vals[loc_ext_id])
            if loc_name == 'code':
                vals[loc_name] = '%d' % vals[loc_ext_id]
            else:
                vals[loc_name] = 'Unknown %d' % vals[loc_ext_id]
        else:
            vals[loc_name] = 'Unknown'
        return vals

    def apply_upper(self, channel_id, vals, loc_name,
                        ext_ref, loc_ext_id, default=None):
        if ext_ref in vals:
            if isinstance(vals[ext_ref], basestring):
                vals[loc_name] = vals[ext_ref].upper()
            else:
                vals[loc_name] = vals[ext_ref]
        return vals

    def apply_lower(self, channel_id, vals, loc_name,
                        ext_ref, loc_ext_id, default=None):
        if ext_ref in vals:
            if isinstance(vals[ext_ref], basestring):
                vals[loc_name] = vals[ext_ref].lower()
            else:
                vals[loc_name] = vals[ext_ref]
        return vals

    def apply_bool(self, channel_id, vals, loc_name,
                       ext_ref, loc_ext_id, default=None):
        if ext_ref in vals:
            vals[loc_name] = os0.str2bool(vals.get(ext_ref), False)
        return vals

    def apply_not(self, channel_id, vals, loc_name,
                      ext_ref, loc_ext_id, default=None):
        if ext_ref in vals:
            vals[loc_name] = not os0.str2bool(vals.get(ext_ref), True)
        return vals

    def apply_person(self, channel_id, vals, loc_name,
                         ext_ref, loc_ext_id, default=None):
        '''First name and/or last name'''
        if ext_ref in vals and loc_name != ext_ref:
            vals[loc_name] = vals[ext_ref]
            del vals[ext_ref]
        if 'lastname' in vals and 'firstname' in vals:
            if not vals.get('name'):
                vals['name'] = '%s %s' % (vals['lastname'], vals['firstname'])
                if not vals['name'].strip():
                    vals['name'] = 'Unknown'
                vals['is_company'] = False
            del vals['lastname']
            del vals['firstname']
        return vals

    def apply_vat(self, channel_id, vals, loc_name,
                      ext_ref, loc_ext_id, default=None):
        '''External vat may not contain ISO code'''
        if ext_ref in vals:
            if (isinstance(vals[ext_ref], basestring) and
                    len(vals[ext_ref]) == 11 and
                    vals[ext_ref].isdigit()):
                vals[loc_name] = 'IT%s' % vals[ext_ref]
            else:
                vals[loc_name] = vals[ext_ref]
        return vals

    def apply_street_number(self, channel_id, vals, loc_name,
                                ext_ref, loc_ext_id, default=None):
        '''Street number'''
        if ext_ref in vals:
            if 'street' in vals:
                loc_name = 'street'
            else:
                loc_name = '%s:street' % ext_ref[0:3]
            if loc_name in vals:
                vals[loc_name] = '%s, %s' % (vals[loc_name], vals[ext_ref])
            del vals[ext_ref]
        return vals

    def apply_invoice_number(self, channel_id, vals, loc_name,
                                 ext_ref, loc_ext_id, default=None):
        '''Invoice number'''
        if ext_ref in vals:
            vals['move_name'] = vals[ext_ref]
        return vals

    def apply_journal(self, channel_id, vals, loc_name,
                          ext_ref, loc_ext_id, default=None):
        if 'journal_id' not in vals:
            journal = self.env['account.invoice']._default_journal()
            if journal:
                vals['journal_id'] = journal[0].id
        return vals

    def apply_account(self, channel_id, vals, loc_name,
                          ext_ref, loc_ext_id, default=None):
        if 'journal_id' in vals:
            journal_id = vals['journal_id']
        else:
            journal_id = self.env['account.invoice']._default_journal()
        if 'account_id' not in vals and 'product_id' in vals:
            product = self.env['product.product'].browse(vals['product_id'])
            accounts = product.product_tmpl_id._get_product_accounts()
            if accounts:
                if vals.get('type') in ('in_invoice', 'in_refund'):
                    vals['account_id'] = accounts['expense'].id
                else:
                    vals['account_id'] = accounts['income'].id
            else:
                journal = self.env[
                    'account.journal'].browse(journal_id)
                if vals.get('type') in ('in_invoice', 'in_refund'):
                    vals['account_id'] = journal.default_debit_account_id.id
                else:
                    vals['account_id'] = journal.default_credit_account_id.id
        return vals

    def apply_uom(self, channel_id, vals, loc_name,
                      ext_ref, loc_ext_id, default=None):
        if loc_name not in vals and 'product_id' in vals:
            product = self.env['product.product'].browse(vals['product_id'])
            vals[loc_name] = product.uom_id.id
        elif not vals.get(loc_name):
            vals[loc_name] = self.env.ref('product.product_uom_unit')
        return vals

    def apply_tax(self, channel_id, vals, loc_name,
                      ext_ref, loc_ext_id, default=None):
        if loc_name not in vals and 'product_id' in vals:
            product = self.env['product.product'].browse(vals['product_id'])
            if vals.get('type') in ('in_invoice', 'in_refund'):
                tax = product.supplier_taxes_id
            else:
                tax = product.taxes_id
            if tax:
                vals[loc_name] = [(6, 0, [tax.id])]
        return vals

    def apply_agents(self, channel_id, vals, loc_name,
                         ext_ref, loc_ext_id, default=None):
        def _prepare_line_agents_data(partner):
            rec = []
            for agent in partner.agents:
                rec.append({
                    'agent': agent.id,
                    'commission': agent.commission.id,
                })
            return rec
        if loc_name in vals:
            return vals
        if vals.get('partner_id'):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
        elif vals.get('order_id'):
            partner = self.env[
                'sale.order'].browse(vals['order_id']).partner_id
        elif vals.get('invoice_id'):
            partner = self.env[
                'account.invoice'].browse(vals['invoice_id']).partner_id
        else:
            partner = False
        if not partner:
            return vals
        if hasattr(partner, 'agents') and partner.agents:
            line_agents_data = _prepare_line_agents_data(partner)
            if line_agents_data:
                vals[loc_name] = [
                    (0, 0,
                     line_agent_data) for line_agent_data in line_agents_data]
        return vals

    def apply_partner_info(self, channel_id, vals, loc_name,
                               ext_ref, loc_ext_id, default=None):
        if loc_name in vals:
            return vals
        if vals.get('partner_id'):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
        elif vals.get('order_id'):
            partner = self.env[
                'sale.order'].browse(vals['order_id']).partner_id
        elif vals.get('invoice_id'):
            partner = self.env[
                'account.invoice'].browse(vals['invoice_id']).partner_id
        else:
            return vals
        if loc_name == 'fiscal_position_id':
            partner_nm = 'property_account_position_id'
        elif loc_name in ('pricelist_id',
                          'payment_term_id'):
            partner_nm = 'property_%s' % loc_name
        else:
            partner_nm = loc_name
        if partner_nm in partner:
            try:
                vals[loc_name] = partner[partner_nm].id
            except BaseException:
                vals[loc_name] = partner[partner_nm]
        return vals

    def apply_partner_address(self, channel_id, vals, loc_name,
                                  ext_ref, loc_ext_id, default=None):
        if loc_name in vals:
            return vals
        if 'partner_id' in vals:
            vals[loc_name] = vals['partner_id']
        return vals

    def apply_company_info(self, channel_id, vals, loc_name,
                               ext_ref, loc_ext_id, default=None):
        if loc_name in vals:
            return vals
        company_id = vals.get('company_id')
        if not company_id:
            return vals
        company = self.env[
                'res.company'].with_context(
            {'lang': self.env.user.lang}).browse(company_id)
        if loc_name == 'note':
            partner_nm = 'sale_note'
        else:
            partner_nm = loc_name
        if partner_nm in company:
            try:
                vals[loc_name] = company[partner_nm].id
            except:
                vals[loc_name] = company[partner_nm]
        return vals

    def apply_set_global(self, channel_id, vals, loc_name,
                             ext_ref, loc_ext_id, default=None):
        if loc_name in vals:
            return vals
        cache = self.env['ir.model.synchro.cache']
        ctx = cache.get_attr(channel_id, 'CTX')

        if loc_name in self.CTX_FLDS:
            vals[loc_name] = self.CTX_FLDS[loc_name]
        return vals

    def apply_set_einvoice(self, channel_id, vals, loc_name,
                               ext_ref, loc_ext_id, default=None):
        if vals.get(ext_ref):
            if len(vals[ext_ref]) == 7:
                vals['electronic_invoice_subjected'] = True
            elif len(vals[ext_ref]) == 6:
                vals['ipa_code'] = vals[ext_ref]
                vals['is_pa'] = True
                if loc_name in vals:
                    del vals[loc_name]
        return vals

    def apply_set_is_pa(self, channel_id, vals, loc_name,
                            ext_ref, loc_ext_id, default=None):
        if len(vals.get(ext_ref)) == 6:
            vals['is_pa'] = True
        return vals

    def apply_set_iban(self, channel_id, vals, loc_name,
                           ext_ref, loc_ext_id, default=None):
        if vals.get(ext_ref):
            vals[loc_name] = vals[ext_ref].replace(' ', '')
        elif vals.get('vg7:description'):
            vals[loc_name] = vals['vg7:description']
        elif vals.get('bank_name'):
            vals[loc_name] = vals['bank_name']
        return vals

    def apply_acc_user_type(self, channel_id, vals, loc_name,
                           ext_ref, loc_ext_id, default=None):
        vals[loc_name] = self.env['account.account.type'].search([])[0].id
        return vals


class IrModelSynchroCache(models.Model):
    _name = 'ir.model.synchro.cache'
    # _inherit = 'ir.model.synchro'

    CACHE = odoo_score.SingletonCache()

    TABLE_DEF = {
        'account.account': {
            'user_type_id': {'required': True, 'APPLY': 'acc_user_type()'},
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
            'number': {'readonly': False},
            'partner_id': {'readonly': False},
            'partner_shipping_id': {'readonly': False},
            'payment_term_id': {'readonly': False},
            'registration_date': {'readonly': False},
            'type': {'readonly': False},
            'user_id': {'readonly': False},
        }
    }


    @api.model_cr_context
    def lifetime(self, lifetime):
        cache = self.CACHE
        dbname = self._cr.dbname
        return  cache.lifetime(dbname, lifetime)

    @api.model_cr_context
    def clean_cache(self, channel_id=None, model=None, lifetime=None):
        _logger.info('> clean_cache(%d,%s,%d)' % (
            (channel_id or -1), model, (lifetime or -1)
        ))
        cache = self.CACHE
        dbname = self._cr.dbname
        self.setup_channels()
        if channel_id:
            cache.init_channel(dbname, channel_id)
        if model:
            cache.init_struct_model(dbname, model)
        else:
            cache.init_struct(dbname)
        if lifetime:
            self.lifetime(lifetime)
        return self.lifetime(0)

    @api.model_cr_context
    def set_loglevel(self, loglevel):
        cache = self.CACHE
        self.setup_channels()
        for channel_id in self.get_channel_list():
            self.set_attr(channel_id, 'LOGLEVEL', loglevel)
        return True

    @api.model_cr_context
    def is_struct(self, model):
        return model >= 'a'

    @api.model_cr_context
    def get_channel_list(self):
        cache = self.CACHE
        dbname = self._cr.dbname
        return cache.get_channel_list(dbname)

    @api.model_cr_context
    def get_attr_list(self, channel_id):
        cache = self.CACHE
        dbname = self._cr.dbname
        return cache.get_attr_list(dbname, channel_id)

    @api.model_cr_context
    def get_attr(self, channel_id, attrib, default=None):
        cache = self.CACHE
        dbname = self._cr.dbname
        return cache.get_attr(dbname, channel_id, attrib, default=default)

    @api.model_cr_context
    def get_model_attr(self, channel_id, model, attrib, default=None):
        cache = self.CACHE
        dbname = self._cr.dbname
        return cache.get_model_attr(
            dbname, channel_id, model, attrib, default=default)

    @api.model_cr_context
    def get_model_field_attr(self, channel_id, model, field, attrib,
                             default=None):
        cache = self.CACHE
        dbname = self._cr.dbname
        return cache.get_model_field_attr(
            dbname, channel_id, model, field, attrib, default=default)

    @api.model_cr_context
    def set_channel(self, channel_id):
        cache = self.CACHE
        dbname = self._cr.dbname
        return cache.set_channel(dbname, channel_id)

    @api.model_cr_context
    def set_model(self, channel_id, model):
        self.set_channel(channel_id)
        self.set_attr(
            channel_id, model, self.get_attr(channel_id, model) or {})
        self.set_model_attr(channel_id, model, 'LOC_FIELDS', {})
        self.set_model_attr(channel_id, model, 'EXT_FIELDS', {})
        self.set_model_attr(channel_id, model, 'APPLY', {})
        self.set_model_attr(channel_id, model, 'PROTECT', {})
        self.set_model_attr(channel_id, model, 'SPEC', {})
        self.set_model_attr(channel_id, model, 'REQUIRED', {})

    @api.model_cr_context
    def set_attr(self, channel_id, attrib, value):
        cache = self.CACHE
        dbname = self._cr.dbname
        return cache.set_attr(dbname, channel_id, attrib, value)

    @api.model_cr_context
    def set_model_attr(self, channel_id, model, attrib, value):
        cache = self.CACHE
        dbname = self._cr.dbname
        return cache.set_model_attr(dbname, channel_id, model, attrib, value)

    @api.model_cr_context
    def del_model_attr(self, channel_id, model, attrib):
        cache = self.CACHE
        dbname = self._cr.dbname
        return cache.del_model_attr(dbname, channel_id, model, attrib)

    @api.model_cr_context
    def set_model_field_attr(self, channel_id, model, field, attrib, value):
        cache = self.CACHE
        dbname = self._cr.dbname
        return cache.set_model_field_attr(
            dbname, channel_id, model, field, attrib, value)

    @api.model_cr_context
    def model_list(self):
        cache = self.CACHE
        dbname = self._cr.dbname
        return cache.model_list(dbname)

    @api.model_cr_context
    def get_struct_attr(self, attrib, default=None):
        cache = self.CACHE
        dbname = self._cr.dbname
        return cache.get_struct_attr(dbname, attrib, default=default)

    @api.model_cr_context
    def get_struct_model_attr(self, model, attrib, default=None):
        cache = self.CACHE
        dbname = self._cr.dbname
        return cache.get_struct_model_attr(
            dbname, model, attrib, default=default)

    @api.model_cr_context
    def get_struct_model_field_attr(self, model, field, attrib, default=None):
        cache = self.CACHE
        dbname = self._cr.dbname
        return cache.get_struct_model_field_attr(
            dbname, model, field, attrib, default=default)

    @api.model_cr_context
    def set_struct_model(self, model):
        cache = self.CACHE
        dbname = self._cr.dbname
        return cache.set_struct_model(dbname, model)

    @api.model_cr_context
    def set_struct_model_attr(self, model, attrib, value):
        cache = self.CACHE
        dbname = self._cr.dbname
        return cache.set_struct_model_attr(dbname, model, attrib, value)

    @api.model_cr_context
    def setup_model_structure(self, model, actual_model, ro_fields=None):
        '''Store model structure in memory'''
        if not model:
            return
        cache = self.CACHE
        ro_fields = ro_fields or []
        if self.get_struct_model_attr(model,
                                      'EXPIRE',
                                      default=datetime.now()) > datetime.now():
            return
        ir_model = self.env['ir.model.fields']
        self.set_struct_model(model)
        self.set_struct_model_attr(
            model, 'EXPIRE', datetime.now() + timedelta(
                seconds=(self.lifetime(0))))
        for field in ir_model.search([('model', '=', actual_model)]):
            def_field = self.TABLE_DEF.get(model, {}).get(field.name, {})
            if 'required' in def_field:
                required = def_field['required']
            else:
                required = field.required
            if 'readonly' in def_field:
                readonly = def_field['readonly']
            else:
                readonly = field.readonly
            readonly = readonly or field.ttype in ('binary', 'reference')
            if field.name in ro_fields:
                readonly = True
            self.set_struct_model_attr(
                actual_model, field.name, {
                    'ttype': field.ttype,
                    'relation': field.relation,
                    'required': required,
                    'readonly': readonly,
                    'protect': field.protect_update,
                })
            if field.relation != actual_model:
                if field.relation and field.relation.startswith(actual_model):
                    self.set_struct_model_attr(
                        actual_model, 'LINES_OF_REC', field.name)
                    self.set_struct_model_attr(
                        actual_model, 'LINE_MODEL', field.relation)
                elif field.relation and actual_model.startswith(
                        field.relation):
                    self.set_struct_model_attr(
                        actual_model, 'PARENT_ID', field.name)
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

    @api.model_cr_context
    def setup_channels(self):
        cache = self.CACHE
        dbname = self._cr.dbname
        channel_ctr = 0
        expired = False
        for channel_id in self.get_channel_list():
            channel_ctr += 1
            if self.get_attr(channel_id,
                             'EXPIRE',
                             default=datetime.now()) <= datetime.now():
                expired = True
                break
        if not expired and channel_ctr > 0:
            return
        for channel in self.env['synchro.channel'].search([]):
            if self.get_attr(
                    channel.id, 'EXPIRE',
                    default=datetime.now()) > datetime.now():
                continue
            self.set_channel(channel.id)
            self.set_attr(
                channel.id, 'EXPIRE', datetime.now() + timedelta(
                    seconds=(self.lifetime(0) * 3)))
            self.set_attr(channel.id, 'PRIO', channel.sequence)
            self.set_attr(channel.id, 'OUT_QUEUE', [])
            self.set_attr(channel.id, 'IN_QUEUE', [])
            self.set_attr(channel.id, 'PREFIX', channel.prefix)
            self.set_attr(channel.id, 'IDENTITY', channel.identity)
            self.set_attr(channel.id, 'METHOD', channel.method)
            self.set_attr(channel.id, 'CTX', {
                'company_id': False,
                'country_id': False,
                'is_company': True,
            })
            if channel.company_id:
                self.set_attr(channel.id,
                              'COMPANY_ID', channel.company_id.id)
            else:
                self.set_attr(channel.id,
                              'COMPANY_ID', self.env.user.company_id.id)
            self.set_attr(channel.id,
                          'COUNTRY_ID',
                          self.env.user.company_id.partner_id.country_id.id)
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

    @api.model_cr_context
    def setup_models_in_channels(self, model):
        if not model:
            return
        cache = self.CACHE
        where = [('name', '=', model)]
        for rec in self.env['synchro.channel.model'].search(where):
            if rec.synchro_channel_id.id not in self.get_channel_list():
                continue
            model = rec.name
            channel_id = rec.synchro_channel_id.id
            if self.get_model_attr(channel_id, model, 'EXPIRE',
                                   default=datetime.now()) > datetime.now():
                continue
            self.set_model(channel_id, model)
            self.set_model_attr(
                channel_id, model, 'EXPIRE', datetime.now() + timedelta(
                    seconds=(self.lifetime(0)) * 2))
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
                self.set_model_attr(channel_id, model, 'SPEC', rec.model_spec)
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
        for channel_id in self.get_channel_list():
            if self.get_attr(channel_id, 'IDENTITY') == 'odoo':
                self.set_odoo_model(channel_id, model)

    @api.model_cr_context
    def setup_channel_model_fields(self, model_rec):
        # cache = self.CACHE
        model = model_rec.name
        channel_id = model_rec.synchro_channel_id.id
        self.set_model(channel_id, model)
        self.set_odoo_model(channel_id, model, force=True)
        skeys = []
        for nm in ('description', 'login', 'code', 'name'):
            if nm in self.get_struct_attr(model):
                skeys.append([nm])
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
            self.set_model_field_attr(
                channel_id, model, loc_name, 'LOC_FIELDS', ext_name)
            self.set_model_field_attr(
                channel_id, model, ext_name, 'EXT_FIELDS', loc_name)
            if field.apply:
                self.set_model_field_attr(
                    channel_id, model, loc_name, 'APPLY', field.apply)
            if field.protect and field.protect != '0':
                self.set_model_field_attr(
                    channel_id, model, loc_name, 'PROTECT', field.protect)
            if field.spec:
                self.set_model_field_attr(
                    channel_id, model, loc_name, 'SPEC', field.spec)
            required = self.get_struct_model_field_attr(
                model, loc_name, 'required') or field.required
            self.set_model_field_attr(
                channel_id, model, loc_name, 'REQUIRED', required)
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

    @api.model_cr_context
    def set_odoo_model(self, channel_id, model, force=None):
        # cache = self.CACHE
        if not force and self.get_attr(channel_id, model):
            return
        identity = self.get_attr(channel_id, 'IDENTITY')
        self.set_model(channel_id, model)
        skeys = []
        for nm in ('description', 'login', 'code', 'name'):
            if nm in self.get_struct_attr(model):
                skeys.append([nm])
        for field in self.get_struct_attr(model):
            if not self.is_struct(field):
                continue
            if identity == 'odoo':
                self.set_model_field_attr(
                    channel_id, model, field, 'LOC_FIELDS', field)
                self.set_model_field_attr(
                    channel_id, model, field, 'EXT_FIELDS', field)
            else:
                self.set_model_field_attr(
                    channel_id, model, field, 'LOC_FIELDS', '.%s' % field)
                self.set_model_field_attr(
                    channel_id, model, '.%s' % field, 'EXT_FIELDS', field)
            self.set_model_field_attr(
                channel_id, model, field, 'PROTECT',
                self.get_struct_model_field_attr(model, field, 'protect'))
            def_field = self.TABLE_DEF.get(model, {}).get(field, {})
            if 'APPLY' in def_field:
                self.set_model_field_attr(
                    channel_id, model, field, 'APPLY', def_field['APPLY'])
        if SKEYS.get(model):
            self.set_model_attr(
                channel_id, model, 'SKEYS', SKEYS[model])
        else:
            self.set_model_attr(channel_id, model, 'SKEYS', skeys)

    @api.model_cr_context
    def open(self, model=None, cls=None):
        cache = self.CACHE
        actual_model = self.env[
            'ir.model.synchro'].get_actual_model(model, only_name=True)
        self.setup_model_structure(model, actual_model)
        self.setup_channels()
        self.setup_models_in_channels(model)
        if cls is not None:
            if cls.__class__.__name__ != model:
                raise RuntimeError('Class %s not of declared model %s' % (
                    cls.__class__.__name__, model))
            if hasattr(cls, 'LINES_OF_REC'):
                self.set_struct_model_attr(actual_model, 'LINES_OF_REC',
                                           getattr(cls, 'LINES_OF_REC'))
            if hasattr(cls, 'LINE_MODEL'):
                self.set_struct_model_attr(actual_model, 'LINE_MODEL',
                                           getattr(cls, 'LINE_MODEL'))
            if hasattr(cls, 'PARENT_ID'):
                self.set_struct_model_attr(actual_model, 'PARENT_ID',
                                           getattr(cls, 'PARENT_ID'))


class IrModelField(models.Model):
    _inherit = 'ir.model.fields'

    protect_update = fields.Selection(
        [('0', 'Always Update'),
         ('1', 'But new value not empty'),
         ('2', 'But current value is empty'),
         ('3', 'Protected field'),
         ],
        string='Protect field against update',
        default='0',
    )

    @api.model_cr_context
    def _auto_init(self):
        res = super(IrModelField, self)._auto_init()

        self._cr.execute("""UPDATE ir_model_fields set protect_update='3'
        where name not like '____id' and model_id in
        (select id from ir_model where model='res.country');
        """)

        self._cr.execute("""UPDATE ir_model_fields set protect_update='3'
        where name not like '____id' and model_id in
        (select id from ir_model where model='res.country.state');
        """)

        self._cr.execute("""UPDATE ir_model_fields set protect_update='0'
        where name not in ('type', 'categ_id', 'uom_id', 'uom_po_id',
        'purchase_method', 'invoice_policy', 'property_account_income_id',
        'taxes_id', 'property_account_expense_id', 'supplier_taxes_id')
        and model_id in
        (select id from ir_model where model='product_product');
        """)

        self._cr.execute("""UPDATE ir_model_fields set protect_update='3'
        where name in ('type', 'categ_id', 'uom_id', 'uom_po_id',
        'purchase_method', 'invoice_policy', 'property_account_income_id',
        'taxes_id', 'property_account_expense_id', 'supplier_taxes_id')
        and model_id in
        (select id from ir_model where model='product_product');
        """)

        self._cr.execute("""UPDATE ir_model_fields set protect_update='0'
        where name like '____id' ;
        """)
        return res
