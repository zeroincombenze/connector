# -*- coding: utf-8 -*-
#
# Copyright 2019-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
"""
INTRODUCTION

This software provides to ability of exchange records with different
external partners we call counterparts. The synchro function returns the Odoo
id record or a error code (read below).

Synchro runs 3 steps:
1. Counterpart names are translated into local Odoo names, and the <*2many>
   records are mapped into local records.
   During the mapping process, a new synchro function on <*2many> relation
   model to bind or create a linked record. So synchro is recursive function.
2. After translation and mapping, data is used to binding local record.
   The searching is mainly based on counterpart id (read below) when matched;
   otherwise a complex finding process is engaged depending on the specific
   model structure.
3. If local Odoo record is found, the <write> is engaged otherwise the
   <create> is executed. Because counterpart can ignore the Odoo structure,
   it can issue incomplete or wrong data so the <create> can fail and breaks
   recursive chain. In order to minimize the errors, the <create> is splitted
   into a simple create followed by a write function. The <create> uses the
   minimal data required by Odoo while the <write> uses the full data supplied
   by the counterpart. In this way, the <create> should terminate quite ever
   with success and return a valid id.


EXTERNAL REFERENCE

On every Odoo record there is an id field to link external record, which is
a unique key to avoid synchronization troubles.
Odoo's models and counterpart tables can have different relationships:

* One to one: this relationship just requires the field mapping
* Many (Odoo) to one (partner): it managed like previous case because
  external ids never conflicts
* One (Odoo) to many (partner): it requires sub models (w/o records) and/or
  more external id on the actual record.

Imagine this scenario: Odoo exchanges "res.partner" with a counterpart called
vg7 which have 2 tables, named "customer" and "supplier". A one Odoo record
may have to link to customer record and/or the supplier record.
Also imagine that the external customer table contains shipping data which
are in a separate "res.partner" records of Odoo.
So we meet some conflicts. The first one when both "customer" and "supplier"
can have the same id (because on the counterpart there are 2 different tables)
or when a partner is both customer and supplier at the same time.
We can solve this conflict adding a new field on the actual "res.partner"
record, and we use a "res.partner.supplier" sub-model.
We meet another conflict when we write two "res.partner" records, one with the
customer data and the other one with the shipping data. Both records refer to
the same id of counterpart record, but we cannot use the same id due unique key
constraint.
We solve this conflict adding a bias value (default is 1000000000) to the
shipping Odoo's record.
At the last but no least we need of a preprocessing function to recognize
a customer record from a supplier record and to extract shipping data from the
customer record.

In this software we use the follow terms and structures:
+---------------+-------------+----------------------+----------------------+
| prefix     (1)| vg7         | vg7                  | vg7                  |
| bind       (2)| customer    |                      | supplier             |
| actual_model  | res.partner | res.partner          | res.partner          |
| xmodel     (3)| res.partner | res.partner.shipping | res,partner.supplier |
| loc_ext_id (4)| vg7_id      | vg7_id               | vg72_id              |
| ext_key_id (5)| id          | id                   | id                   |
| offset     (6)| 0           | 100000000            | 0                    |
+---------------+-------------+----------------------+----------------------+
(1) Prefix of every field supplied by the counterpart (this is just an example)
(2) Name of external counterpart table
(3) Odoo model, sub model of actual model
(4) Odoo field, unique key, with external partner id; default is "{prefix}_id"
(5) External partner field with the external id; default is "id"
(6) Offset to store external id, when does not exist external counterpart table

During the pre-processing to extract the shipping data from the customer data,
the shipping data is stored in the cache and then retrieved after the customer
record is written.


EXCHANGE MODE AND STRUCTURED MODELS

Data may be exchanged with counterpart in two ways:
1. Push mode: counterpart sends data to Odoo. It prefixes its dictionary name
2. Pull mode: Odoo gets data from the counterpart.

Parent/child models like invoice and sale order are managed in 3 ways:
A. Parent without child reference. After the parent record is written, children
   must be sent by the counterpart (push mode) or must be get from the
   counterpart (pull mode).
B. Parent contains "line_ids" field with list of children ids. In this case
   "line _ids" is extracted from the parent record during pre-processing and
   the list of children is stored in the cache.
   After the parent record is written, "line_ids" is retrieved and every id in
   the list is used to get data from the counterpart (only pull mode).
C. Header contains "line_ids" with dictionary data and operation is <create>.
   In this case data are enough to create children records too. "line_ids"
   field is changed adding "(0, 0" prefix that is the way used by Odoo itself
   to create new parent/child records.


CACHE

Data stored in cache:
- 'vg7:shipping': sub-model res.partner.shipping
- 'vg7:billing': sub-model res.partner.invoice
- '_queue': queue reocrds
- '__{{model}}': full data of model to write the created record (read above)


RETURN CODES

Return code:
    -1: error creating record
    -2: error writing record
    -3: record with passed id does not exist
    -4: unmodifiable record
    -5: invalid structure header/details
    -6: unrecognized channel
    -7: no data supplied
    -8: unrecognized external table
    -9: Unaccettable burst record
"""
import logging
import os
# from datetime import datetime, timedelta
import csv

import requests
from odoo import api, fields, models
from odoo import release

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
    from clodoo import transodoo
except ImportError as err:
    _logger.error(err)
try:
    import oerplib
except ImportError as err:
    _logger.error(err)


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
                "CREATE UNIQUE INDEX %s on %s (%s_id) where %s_id<>0 and %s_id<>null" %
                (index_name, table, prefix, prefix, prefix)
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
        elif model == 'res.partner.bank':
            if spec == 'id_odoo':
                xmodel = 'res.partner.bank.company'
        return xmodel

    @api.model
    def get_actual_model(self, model, only_name=False):
        actual_model = model
        if model in ('res.partner.shipping',
                     'res.partner.invoice',
                     'res.partner.supplier'):
            actual_model = 'res.partner'
        elif model == 'res.partner.bank.company':
            actual_model = 'res.partner.bank'
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
        elif xmodel == 'res.partner.bank.company':
            return 'id_odoo'
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

    def get_tnldict(self, channel_id):
        cache = self.env['ir.model.synchro.cache']
        tnldict = cache.get_attr(channel_id, 'TNL')
        if not tnldict:
            tnldict = {}
            transodoo.read_stored_dict(tnldict)
            cache.set_attr(channel_id, 'TNL', tnldict)
        return tnldict

    def get_ext_odoo_ver(self, prefix):
        return {
            'oe7': '7.0',
            'oe8': '8.0',
            'oe10': '10.0',
            'oe7:': '7.0',
            'oe8:': '8.0',
            'oe10:': '10.0',
        }.get(prefix, '')

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
                if (cache.get_struct_model_field_attr(
                        actual_model, field, 'ttype') == 'many2one'):
                    if rec[field] and vals[field] == rec[field].id:
                        del vals[field]
                elif vals[field] == rec[field]:
                    del vals[field]
        return vals

    def set_state_to_draft(self, model, rec, vals):
        self.logmsg(1, '>>> set_state_to_draft(%s,%s)' % (
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
            if 'state' in vals:
                del vals['state']
        elif model == 'stock.picking.package.preparation':
            if rec:
                self.logmsg(1, '>>> unlink(%s,%s)' % (model, rec.id))
                try:
                    rec.unlink()
                except IOError:
                    errc = -2
        return vals, errc

    def set_actual_state(self, model, rec):
        self.logmsg(1, '>>> set_actual_state(%s,%s)' % (
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
                _logger.error('Unauthorized state change of %s.%s' % (
                    model, rec.id))
                return -4
            elif rec.original_state == 'open':
                rec.action_invoice_open()
                if rec.name and rec.name.startswith('Unknown'):
                    rec.write({'name': rec.number})
            elif rec.original_state == 'cancel':
                rec.action_invoice_cancel()
        elif model == 'sale.order':
            # Please, dO not remove this write: set default values in header
            rec.write({})
            if rec.state == rec.original_state:
                return rec.id
            elif rec.state != 'draft':
                _logger.error('Unauthorized state change of %s.%s' % (
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
        # cache = self.env['ir.model.synchro.cache']
        vals = self.get_counterpart_response(
            channel_id,
            model,
            self.get_actual_ext_id_value(channel_id, model, vg7_id))
        if not vals:
            return False
        cls = self.env[model]
        return self.generic_synchro(cls,
                                     vals,
                                     channel_id=channel_id,
                                     jacket=True)

    def create_new_ref(
            self, channel_id, actual_model, key_name, value, ext_value,
            ctx=None, spec=None):
        self.logmsg(1, '>>> create_new_ref(%s,%s,%s,%s)' % (
                    actual_model, key_name, value, (ext_value or -1)))
        ctx = ctx or {}
        cache = self.env['ir.model.synchro.cache']
        xmodel = self.get_xmodel(actual_model, spec)
        loc_ext_id = self.get_loc_ext_id_name(channel_id, xmodel)
        cls = self.env[xmodel]
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
                vals['name'] = 'Unknown %s' % ext_value
            else:
                vals['name'] = '%s=%s' % (key_name, value)
        elif (key_name != 'code' and
              cache.get_struct_model_attr(actual_model, 'code')):
            if ext_value:
                vals['name'] = 'Unknown %s' % ext_value
            else:
                vals['code'] = '%s=%s' % (key_name, value)
        if actual_model == 'res.partner' and spec in ('delivery', 'invoice'):
            vals['type'] = spec
        try:
            new_value = self.synchro(cls, vals, disable_post=True)
            if new_value > 0:
                in_queue = cache.get_attr(channel_id, 'IN_QUEUE')
                in_queue.append([xmodel, new_value])
                cache.set_attr(channel_id, 'IN_QUEUE', in_queue)
            else:
                new_value = False
        except BaseException:
            _logger.info('### Failed %s.synchro(%s)' % (xmodel, vals))
            new_value = False
        return new_value

    def do_search(self, channel_id, actual_model, req_domain,
                  only_id=None, spec=None):

        def exec_search(cls, domain, has_sequence):
            if has_sequence:
                return cls.search(domain, order='sequence,id')
            else:
                return cls.search(domain)

        cache = self.env['ir.model.synchro.cache']
        maybe_dif = False
        has_sequence = cache.get_struct_model_attr(actual_model, 'sequence')
        cls = self.env[actual_model]
        if only_id:
            self.logmsg(channel_id,
                        '>>> %s.search(%s)' % (actual_model, req_domain))
            rec = exec_search(cls, req_domain, has_sequence)
            return rec, maybe_dif
        domain = [x for x in req_domain]
        if actual_model == 'res.partner' and spec in ('delivery', 'invoice'):
            domain.append(['type', '=', spec])
        self.logmsg(channel_id,
                    '>>> %s.search(%s)' % (actual_model, domain))
        rec = exec_search(cls, domain, has_sequence)
        if not rec and cache.get_struct_model_attr(actual_model, 'active'):
            domain.append(('active', '=', False))
            rec = exec_search(cls, domain, has_sequence)
        if not rec and actual_model == 'res.partner':
            domain = [x for x in req_domain]
            self.logmsg(channel_id,
                        '>>> %s.search(%s)' % (actual_model, domain))
            rec = exec_search(cls, domain, has_sequence)
        if not rec:
            if (actual_model in ('res.partner',
                                 'product.product',
                                 'product.template')):
                domain = []
                do_query = False
                for cond in req_domain:
                    if cond[0] == 'company_id':
                        do_query = True
                    else:
                        domain.append(cond)
                if do_query and domain:
                    rec = exec_search(cls, domain, has_sequence)
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
        cache = self.env['ir.model.synchro.cache']
        ext_key_id = cache.get_model_attr(
            channel_id, actual_model, 'KEY_ID', default='id')
        key_name = cache.get_model_attr(
            channel_id, actual_model, 'MODEL_KEY', default='name')
        if not key_name:
            return False
        xmodel = self.get_xmodel(actual_model, spec)
        loc_ext_id = self.get_loc_ext_id_name(channel_id, xmodel)
        if mode == 'tnl':
            translation_model = self.env['synchro.channel.domain.translation']
            domain = [('model', '=', actual_model),
                      ('key', '=', name),
                      ('ext_value', 'ilike', self.dim_text(value))]
            rec = translation_model.search(domain)
            if not rec:
                return rec
            value = rec[0].odoo_value
            mode = 'ilike'
        domain = [(name, mode, value)]
        if name not in (ext_key_id, loc_ext_id):
            if (cache.get_struct_model_attr(
                    actual_model, 'MODEL_WITH_COMPANY') and
                    ctx.get('company_id')):
                domain.append(('company_id', '=', ctx['company_id']))
            if (cache.get_struct_model_attr(
                    actual_model, 'MODEL_WITH_COUNTRY') and
                    ctx.get('country_id')):
                domain.append(('country_id', '=', ctx['country_id']))
        rec, maybe_dif = self.do_search(
            channel_id, actual_model, domain, spec=spec)
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
        if len(value.split('.')) == 2:
            try:
                return self.env.ref(value).id
            except BaseException:
                pass
        cache = self.env['ir.model.synchro.cache']
        key_name = cache.get_model_attr(
            channel_id, actual_model, 'MODEL_KEY', default='name')
        if not key_name:
            return False
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
            _logger.info('>>> return %s # get_foreign_text()' % new_value)
        return new_value

    def get_foreign_ref(self, channel_id, actual_model, value_id, is_foreign,
                        ctx=None, spec=None):
        cache = self.env['ir.model.synchro.cache']
        loc_ext_id = self.get_loc_ext_id_name(channel_id, actual_model)
        new_value = False
        rec = False
        ext_value = value_id
        if is_foreign:
            if not value_id or value_id < 1:
                return new_value
            if cache.get_struct_model_attr(actual_model, loc_ext_id):
                if spec:
                    value_id = self.get_loc_ext_id_value(
                        channel_id, actual_model, value_id, spec=spec)
                domain = [(loc_ext_id, '=', value_id)]
                rec, maybe_dif = self.do_search(
                    channel_id, actual_model, domain, only_id=True)
        else:
            domain = [('id', '=', value_id)]
            rec, maybe_dif = self.do_search(
                channel_id, actual_model, domain, only_id=True)
        if rec:
            if len(rec) > 1:
                self.logmsg(channel_id,
                            '### NO SINGLETON %s.%s' % (actual_model,
                                                        value_id))
            new_value = rec[0].id
        xmodel = self.get_xmodel(actual_model, spec)
        if not new_value:
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
            _logger.info('>>> return %s # get_foreign_ref())' % new_value)
        return new_value

    def get_foreign_value(self, channel_id, xmodel, value, name, is_foreign,
                          ctx=None, ttype=None, spec=None, fmt=None):
        self.logmsg(
            channel_id, '>>> %s.get_foreign_value(%s,%s,%s,%s,%s)' % (
                xmodel, name, value, is_foreign, ttype, spec))
        if not value:
            return value
        cache = self.env['ir.model.synchro.cache']
        actual_model = self.get_actual_model(xmodel, only_name=True)
        relation = cache.get_struct_model_field_attr(
            actual_model, name, 'relation')
        if not relation:
            raise RuntimeError('No relation for field %s of %s' % (name,
                                                                   xmodel))
        tomany = True if ttype in ('one2many', 'many2many') else False
        cache.open(channel_id=channel_id, model=relation)
        if isinstance(value, basestring):
            new_value = self.get_foreign_text(
                channel_id, relation, value, is_foreign,
                ctx=ctx, spec=spec)
            if tomany and new_value:
                new_value = [new_value]
        elif isinstance(value, (list, tuple)):
            new_value = []
            for loc_id in value:
                new_id = self.get_foreign_ref(
                    channel_id, relation, loc_id, is_foreign,
                    ctx=ctx, spec=spec)
                if new_id:
                    new_value.append(new_id)
        else:
            new_value = self.get_foreign_ref(
                channel_id, relation, value, is_foreign,
                ctx=ctx, spec=spec)
            if tomany and new_value:
                new_value = [new_value]
        if fmt == 'cmd' and new_value and tomany:
            new_value = [(6, 0, new_value)]
        if not new_value:
            _logger.error(
                '### no value (%s) returned from %s!' % (new_value, xmodel))
        elif tomany:
            _logger.info('>>> return %s # get_foreign_value(%s)' % (
                new_value, relation))
        else:
            _logger.info('>>> return %s # get_foreign_value(%s)' % (
                new_value, relation))
        return new_value

    def name_from_ref(self, channel_id, xmodel, ext_ref):
        cache = self.env['ir.model.synchro.cache']
        pfx_depr = '%s_' % cache.get_attr(channel_id, 'PREFIX')
        pfx_ext = '%s:' % cache.get_attr(channel_id, 'PREFIX')
        identity = cache.get_attr(channel_id, 'IDENTITY')
        ext_odoo_ver = self.get_ext_odoo_ver(pfx_ext)
        if identity == 'odoo':
            tnldict = self.get_tnldict(channel_id)
        else:
            tnldict = {}
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
            _logger.warning('Deprecated field name %s!' % ext_ref)
        elif ext_ref.startswith(pfx_ext):
            # Case #3 - field like <vg7:order_id>: both name and value are
            #           of counterpart refs
            is_foreign = True
            ext_name = ext_ref[len(pfx_ext):]
            if ext_name == ext_key_id:
                loc_name = loc_ext_id
            elif identity == 'odoo':
                loc_name = transodoo.translate_from_to(
                    tnldict, xmodel, ext_name,
                    ext_odoo_ver, release.major_version)
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
            # return '', '', ''
            cache.open(channel_id=channel_id, model=actual_model)
        default = cache.get_model_field_attr(
            channel_id, xmodel, loc_name or '.%s' % ext_name, 'APPLY',
            default='')
        if not default:
            default = cache.get_model_field_attr(
                channel_id, actual_model, loc_name or '.%s' % ext_name,
                'APPLY', default='')
        if default.endswith('()'):
            apply4 = ''
            for fct in default.split(','):
                if not fct.startswith('not') or is_foreign:
                    apply4 = '%s,%s' % (apply4, 'apply_%s' % default[:-2])
            if apply4.startswith(','):
                apply4 = apply4[1:]
            default = False
        elif default:
            apply4 = 'apply_set_value'
        else:
            apply4 = ''
        if ttype == 'boolean':
            default = os0.str2bool(default, True)
        spec = cache.get_model_field_attr(
            channel_id, xmodel, loc_name or '.%s' % ext_name, 'SPEC',
            default='')
        return default, apply4, spec

    def map_to_internal(self, channel_id, xmodel, vals, disable_post):

        def rm_ext_value(vals, loc_name, ext_name, ext_ref, is_foreign):
            if (is_foreign or loc_name != ext_name) and ext_ref in vals:
                if loc_name and loc_name not in vals and vals[ext_ref]:
                    vals[loc_name] = vals[ext_ref]
                del vals[ext_ref]
            return vals

        def do_apply(channel_id, vals, loc_name, ext_ref, loc_ext_id,
                     apply4, default, ctx=None):
            ir_apply = self.env['ir.model.synchro.apply']
            src = ext_ref
            for fct in apply4.split(','):
                if hasattr(ir_apply, fct):
                    vals = getattr(ir_apply, fct)(channel_id,
                                                  vals,
                                                  loc_name,
                                                  src,
                                                  loc_ext_id,
                                                  default=default)
                    self.logmsg(channel_id,
                                '>>> %s=%s(%s,%s,%s,%s)' % (
                                    vals.get(loc_name),
                                    fct,
                                    loc_name,
                                    src,
                                    loc_ext_id,
                                    default))
                    src = loc_name
            return vals

        def do_apply_n_clean(channel_id, vals, loc_name, ext_name,
                             ext_ref, loc_ext_id, apply4, default, is_foreign,
                             ctx=None):
            vals = do_apply(channel_id, vals, loc_name, ext_ref, loc_ext_id,
                            apply4, default, ctx=ctx)
            vals = rm_ext_value(vals, loc_name, ext_name, ext_ref, is_foreign)
            return vals

        def priority_fields(channel_id, vals, loc_ext_id, xmodel):
            cache = self.env['ir.model.synchro.cache']
            child_ids = cache.get_struct_model_attr(
                actual_model, 'CHILD_IDS', default=False)
            fields = vals.keys()
            list_1 = []
            list_2 = []
            list_3 = []
            list_6 = []
            list_9 = []
            for ext_ref in fields:
                ext_name, loc_name, is_foreign = \
                    self.name_from_ref(channel_id, xmodel, ext_ref)
                if loc_name in (loc_ext_id, 'id'):
                    list_1.append(ext_ref)
                elif loc_name in ('country_id', 'company_id'):
                    list_2.append(ext_ref)
                elif loc_name in ('partner_id', 'street', child_ids):
                    list_3.insert(0, ext_ref)
                elif loc_name in ('is_company',
                                  'product_uom',
                                  'partner_invoice_id',
                                  'partner_shipping_id',
                                  'electronic_invoice_subjected'):
                    list_9.append(ext_ref)
                else:
                    list_6.append(ext_ref)
            return list_1 + list_2 + list_3 + list_6 + list_9

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

        cache = self.env['ir.model.synchro.cache']
        actual_model = self.get_actual_model(xmodel, only_name=True)
        loc_ext_id = self.get_loc_ext_id_name(channel_id, xmodel)
        ext_key_id = cache.get_model_attr(
            channel_id, xmodel, 'KEY_ID', default='id')
        child_ids = cache.get_struct_model_attr(
            actual_model, 'CHILD_IDS', default=False)
        vals = check_4_double_field_id(vals)
        field_list = priority_fields(channel_id, vals, loc_ext_id, xmodel)
        ctx = cache.get_attr(channel_id, 'CTX')
        ctx['ext_key_id'] = ext_key_id
        ref_in_queue = False
        for ext_ref in field_list:
            if not cache.is_struct(ext_ref):
                continue
            ext_name, loc_name, is_foreign = self.name_from_ref(
                channel_id, xmodel, ext_ref)
            default, apply4, spec = self.get_default_n_apply(
                channel_id, xmodel, loc_name, ext_name, is_foreign,
                ttype=cache.get_struct_model_field_attr(
                    actual_model, ext_name, 'ttype'))
            if not loc_name or not cache.get_struct_model_attr(
                    actual_model, loc_name):
                if is_foreign and apply4:
                    vals = do_apply(
                        channel_id, vals, loc_name, ext_ref, loc_ext_id,
                        apply4, default, ctx=ctx)
                else:
                    self.logmsg(
                        channel_id,
                        '### Field <%s> does not exist in model %s' %
                        (ext_ref, xmodel))
                vals = rm_ext_value(vals, loc_name, ext_name, ext_ref,
                                    is_foreign)
                continue
            elif ext_ref not in vals:
                if is_foreign and apply4:
                    vals = do_apply_n_clean(
                        channel_id, vals,
                        loc_name, ext_name, ext_ref, loc_ext_id,
                        apply4, default, is_foreign, ctx=ctx)
                if loc_name in vals and not vals[loc_name]:
                    del vals[loc_name]
                continue
            elif (isinstance(vals[ext_ref], basestring) and
                  not vals[ext_ref].strip()):
                vals[ext_ref] = vals[ext_ref].strip()
                if is_foreign and apply4:
                    vals = do_apply_n_clean(
                        channel_id, vals,
                        loc_name, ext_name, ext_ref, loc_ext_id,
                        apply4, default, is_foreign, ctx=ctx)
                continue
            elif not vals[ext_ref]:
                if is_foreign and apply4:
                    vals = do_apply_n_clean(
                        channel_id, vals,
                        loc_name, ext_name, ext_ref, loc_ext_id,
                        apply4, default, is_foreign, ctx=ctx)
                continue
            if (cache.get_struct_model_field_attr(
                    actual_model, loc_name, 'ttype') in ('many2one',
                                                         'one2many',
                                                         'many2many'
                                                         'integer') and
                    isinstance(vals[ext_ref], basestring) and (
                            vals[ext_ref].isdigit() or vals[ext_ref] == '-1')):
                vals[ext_ref] = int(vals[ext_ref])
            elif (cache.get_struct_model_field_attr(
                    actual_model, loc_name, 'ttype') == 'boolean' and
                    isinstance(vals[ext_ref], basestring)):
                vals[ext_ref] = os0.str2bool(vals[ext_ref], True)
            if loc_name == child_ids:
                vals = rm_ext_value(vals, loc_name, ext_name, ext_ref,
                                    is_foreign)
                continue
            elif is_foreign:
                # Field like <vg7_id> with external ID in local DB
                if loc_name == loc_ext_id:
                    vals[ext_ref] = self.get_loc_ext_id_value(
                            channel_id, xmodel, vals[ext_ref])
                    vals = rm_ext_value(vals, loc_name, ext_name, ext_ref,
                                        is_foreign)
                    if xmodel == actual_model:
                        if cache.id_is_in_cache(
                                channel_id, xmodel, actual_model,
                                ext_id=vals[loc_name]):
                            ref_in_queue = True
                            self.logmsg(channel_id,
                                        'Found current id in queue!')
                        else:
                            cache.push_id(channel_id, xmodel, actual_model,
                                    ext_id=vals[loc_name])
                    continue
                # If counterpart partner supplies both
                # local and external values, just process local value
                elif loc_name in vals:
                    del vals[ext_ref]
                    continue
            elif ext_ref == 'id':
                if xmodel == actual_model:
                    if cache.id_is_in_cache(
                            channel_id, xmodel, actual_model,
                            loc_id=vals[ext_ref]):
                        ref_in_queue = True
                        self.logmsg(channel_id,
                                    'Found current id in queue!')
                    else:
                        cache.push_id(channel_id, xmodel, actual_model,
                                      loc_id=vals[ext_ref])
                continue
            if cache.get_struct_model_field_attr(
                    actual_model, loc_name, 'ttype') in (
                    'many2one', 'one2many', 'many2many'):
                if ref_in_queue and loc_name not in (
                        'country_id', 'company_id'):
                    if (loc_name in vals and (
                            not vals[loc_name] or
                            (isinstance(vals[loc_name], basestring) and
                             not vals[loc_name].isdigit()))):
                        del vals[loc_name]
                else:
                    vals[loc_name] = self.get_foreign_value(
                        channel_id, xmodel, vals[ext_ref], loc_name, is_foreign,
                        ctx=ctx,
                        ttype=cache.get_struct_model_field_attr(
                            actual_model, loc_name, 'ttype'),
                        spec=spec, fmt='cmd')
            vals = do_apply_n_clean(
                channel_id, vals,
                loc_name, ext_name, ext_ref, loc_ext_id,
                apply4, default, is_foreign, ctx=ctx)
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
        ctx.update(cache.get_attr(channel_id, 'CTX'))
        if 'ext_key_id'in ctx:
            del ctx['ext_key_id']
        cache.set_attr(channel_id, 'CTX', ctx)
        return vals, ref_in_queue

    def set_default_values(self, cls, channel_id, xmodel, vals):
        # self.logmsg(channel_id,
        #             '>>> %s.set_default_values()' % xmodel)
        actual_model = self.get_actual_model(xmodel, only_name=True)
        ir_apply = self.env['ir.model.synchro.apply']
        cache = self.env['ir.model.synchro.cache']
        loc_ext_id = self.get_loc_ext_id_name(channel_id, xmodel)
        for field in cache.get_struct_attr(actual_model).keys():
            if not cache.is_struct(field):
                continue
            ext_name, loc_name, is_foreign = \
                self.name_from_ref(channel_id, xmodel, field)
            if loc_name not in vals:
                if loc_name in cache.get_model_attr(channel_id,
                                                    xmodel, 'LOC_FIELDS'):
                    ttype = cache.get_struct_model_field_attr(
                        actual_model, loc_name, 'ttype')
                    ext_name = cache.get_model_field_attr(
                        channel_id, xmodel, loc_name, 'LOC_FIELDS')
                    default, apply4, spec = self.get_default_n_apply(
                        channel_id, xmodel, loc_name, ext_name, is_foreign,
                        ttype=ttype)
                    required = (cache.get_struct_model_field_attr(
                        actual_model, field, 'required') or
                                cache.get_model_field_attr(
                                    channel_id, xmodel, loc_name, 'REQUIRED'))
                    if required or ext_name.startswith('.'):
                        fcts = apply4.split(',')
                        if required:
                            if (ttype == 'char' and
                                    'apply_set_tmp_name' not in fcts):
                                fcts.append('apply_set_tmp_name')
                            elif (loc_name in ('country_id', 'company_id') and
                                  'apply_set_global' not in fcts):
                                fcts.append('apply_set_global')
                        src = field
                        for fct in fcts:
                            if hasattr(ir_apply, fct):
                                vals = getattr(ir_apply, fct)(
                                    channel_id,
                                    vals,
                                    loc_name,
                                    src,
                                    loc_ext_id,
                                    default=default,
                                    ctx=cache.get_attr(channel_id, 'CTX'))
                                self.logmsg(channel_id,
                                            '>>> %s = apply(%s,%s,%s,%s)' % (
                                                vals.get(loc_name),
                                                fct,
                                                loc_name,
                                                src,
                                                default))
                                src = field
        if hasattr(cls, 'assure_values'):
            vals = cls.assure_values(vals, None)
        return vals

    def bind_record(self, channel_id, xmodel, vals, constraints, ctx=None):

        def add_constraints(domain, constraints):
            for constr in constraints:
                add_domain = False
                if constr[0] in vals:
                    constr[0] = vals[constr[0]]
                    add_domain = True
                if constr[-1] in vals:
                    constr[-1] = vals[constr[-1]]
                    add_domain = True
                if add_domain:
                    domain.append(constr)
            return domain

        _logger.info(
            '> bind_record(%s,%s)' % (xmodel, constraints))  # debug

        ctx = ctx or {}
        actual_model = self.get_actual_model(xmodel, only_name=True)
        spec = self.get_spec_from_xmodel(xmodel)
        spec = spec if spec != 'supplier' else ''
        if actual_model == 'res.partner' and spec in ('delivery', 'invoice'):
            ctx['type'] = spec
        cache = self.env['ir.model.synchro.cache']
        loc_ext_id = self.get_loc_ext_id_name(channel_id, xmodel)
        use_sync = cache.get_struct_model_attr(actual_model, loc_ext_id)
        rec = False
        candidate = False
        if loc_ext_id in vals and use_sync:
            domain = [
                (loc_ext_id, '=', self.get_loc_ext_id_value(
                    channel_id, xmodel, vals[loc_ext_id]))]
            # domain = add_constraints(domain, constraints)
            rec, maybe_dif = self.do_search(
                channel_id, actual_model, domain, only_id=True)
            if len(rec) > 1:
                self.logmsg(channel_id,
                            '### WRONG INDEX %s' % loc_ext_id)
        if not rec:
            for keys in cache.get_model_attr(channel_id, xmodel, 'SKEYS'):
                domain = []
                if isinstance(keys, basestring):
                    keys = [keys]
                for key in keys:
                    if key not in vals:
                        if (key == 'dim_name' and vals.get('name')):
                            domain.append(('dim_name',
                                          '=',
                                          self.dim_text(vals['name'])))
                        elif key in ctx:
                            domain.append((key, '=', ctx[key]))
                        else:
                            domain = []
                            break
                    elif xmodel == 'account.tax' and key == 'amount':
                        if vals[key]:
                            domain.append((key, '=', os0.b(vals[key])))
                        else:
                            domain = []
                            break
                    else:
                        domain.append((key, '=', os0.b(vals[key])))
                if domain:
                    domain = add_constraints(domain, constraints)
                    if loc_ext_id and use_sync:
                        domain.append('|')
                        domain.append((loc_ext_id, '=', False))
                        domain.append((loc_ext_id, '=', 0))
                    rec, maybe_dif = self.do_search(
                        channel_id, actual_model, domain, spec=spec)
                    if rec:
                        break
                    if maybe_dif and not candidate:
                        candidate = rec
        if not rec and candidate:
            rec = candidate
        if rec:
            if len(rec) > 1:
                self.logmsg(channel_id,
                            '### synchro error: multiple ids=%s' % rec)
                return rec[0].id, rec[0]
            else:
                self.logmsg(channel_id,
                            '%s=%s.bind(%s)' % (rec.id, xmodel, channel_id))
            return rec.id, rec
        return -1, None

    def get_xmlrpc_response(
            self, channel_id, xmodel, ext_id=False, select=None, mode=None):

        def default_params():
            endpoint = ''
            db = 'demo'
            login = 'admin'
            passwd = 'admin'
            protocol = 'xmlrpc'
            port = 8069
            return protocol, endpoint, port, db, login, passwd

        def parse_endpoint(endpoint, login=None, port=None):
            protocol, url, def_port, db, user, passwd = default_params()
            login = login or user
            port = port or def_port
            if endpoint:
                if len(endpoint.split('@')) == 2:
                    login = endpoint.split('@')[0]
                    endpoint = endpoint.split('@')[1]
                if len(endpoint.split(':')) == 2:
                    port = int(endpoint.split(':')[1])
                    endpoint = endpoint.split(':')[0]
            return protocol, endpoint, port, login

        def xml_connect(endpoint, protocol=None, port=None):
            cnx = cache.get_attr(channel_id, 'CNX')
            if not cnx:
                prot, endpoint, def_port, login = parse_endpoint(endpoint)
                protocol = protocol or prot
                port = port or def_port
                try:
                    cnx = oerplib.OERP(server=endpoint,
                                       protocol=protocol,
                                       port=port)
                    cache.set_attr(channel_id, 'CNX', cnx)
                except BaseException:  # pragma: no cover
                    cnx = False
            return cnx

        def xml_login(cnx, endpoint,
                      db=None, login=None, passwd=None):
            session = cache.get_attr(channel_id, 'SESSION')
            if not session:
                login = login or self.env.user.login
                prot, endpoint, port, user = parse_endpoint(endpoint)
                db = db or 'demo'
                passwd = passwd or 'admin'
                login = login or user
                try:
                    session = cnx.login(database=db,
                                        user=login,
                                        passwd=passwd)
                    cache.set_attr(channel_id, 'SESSION', session)
                except BaseException:  # pragma: no cover
                    session = False
            return cnx, session

        def connect_params():
            protocol, endpoint, port, db, login, passwd = default_params()
            endpoint = cache.get_attr(channel_id, 'COUNTERPART_URL')
            db = cache.get_attr(channel_id, 'CLIENT_KEY')
            passwd = cache.get_attr(channel_id, 'PASSWORD')
            protocol, endpoint, port, login = parse_endpoint(endpoint)
            return protocol, endpoint, port, db, login, passwd

        def rpc_session():
            cnx = cache.get_attr(channel_id, 'CNX')
            session = cache.get_attr(channel_id, 'SESSION')
            tnldict = self.get_tnldict(channel_id)
            if cnx and session:
                return cnx, session, tnldict
            prot, endpoint, port, db, login, passwd = connect_params()
            if not endpoint:
                _logger.error(
                    'Channel %s without connection parameters!' % channel_id)
                return False, False, tnldict
            cnx, session = xml_login(
                xml_connect(endpoint, protocol=prot, port=port),
                endpoint,
                db=db,
                login=login,
                passwd=passwd)
            if not cnx:
                self.logmsg(channel_id,
                            'Not response from %s' % endpoint)
            elif not session:
                self.logmsg(channel_id,
                            'Login response error (%s,%s,%s)' %
                            (db, login, passwd))
            return cnx, session, tnldict

        def browse_rec(cache, actual_model, ext_id, tnldict):
            try:
                rec = cnx.browse(actual_model, ext_id)
            except:
                rec = False
            prefix = cache.get_attr(channel_id, 'PREFIX')
            ext_odoo_ver = self.get_ext_odoo_ver(prefix)
            vals = {}
            if rec:
                for field in cache.get_struct_attr(actual_model):
                    ext_field = transodoo.translate_from_to(
                        tnldict, actual_model, field,
                        release.major_version, ext_odoo_ver)
                    if (field in ('id', 'state') or (
                            hasattr(rec, ext_field) and
                            cache.is_struct(field) and
                            not cache.get_struct_model_field_attr(
                                actual_model, field, 'readonly'))):
                        if isinstance(rec[ext_field], (bool, int, long)):
                            vals[ext_field] = rec[ext_field]
                        elif cache.get_struct_model_field_attr(
                                actual_model, field, 'ttype') == 'many2one':
                            try:
                                vals[ext_field] = rec[ext_field].id
                            except:
                                vals[ext_field] = rec[ext_field]
                        elif cache.get_struct_model_field_attr(
                                    actual_model, field, 'ttype') in (
                                    'one2many', 'many2many'):
                            vals[ext_field] = [x.id for x in rec[ext_field]]
                        elif isinstance(rec[ext_field], basestring):
                            vals[ext_field] = rec[ext_field].encode(
                                'utf-8').decode('utf-8')
                        else:
                            vals[ext_field] = rec[ext_field]
                # if actual_model == 'account.account.type':
                #     vals['%s:type' % prefix] = self.env[
                #         actual_model].cvt_acct_type(
                #         vals, rec, ext_odoo_ver, release.version)
                if vals:
                    vals['id'] = ext_id
            return vals

        self.logmsg(channel_id,
                    '%s.get_xmlrpc_response(%s,ext_id=%s,sel=%s):' % (
                        xmodel, channel_id, ext_id or -1, select
                    ))
        cache = self.env['ir.model.synchro.cache']
        cnx, session, tnldict = rpc_session()
        prefix = cache.get_attr(channel_id, 'PREFIX')
        actual_model = self.get_actual_model(xmodel, only_name=True)
        if ext_id:
            if mode:
                return cnx.search(actual_model, [(mode, '=', ext_id)])
            return browse_rec(cache, actual_model, ext_id, tnldict)
        else:
            try:
                ids = cnx.search(actual_model, [])
            except:
                ids = []
            return ids
        return {}

    def get_json_response(self, channel_id, xmodel, ext_id=False, mode=None):
        self.logmsg(channel_id,
                    '%s.get_json_response(%s, ext_id=%s):' % (
                        xmodel, channel_id, ext_id or -1
                    ))
        cache = self.env['ir.model.synchro.cache']
        endpoint = cache.get_attr(channel_id, 'COUNTERPART_URL')
        if not endpoint:
            _logger.error(
                'Channel %s without connection parameters!' % channel_id)
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
                    'Response error %s (%s,%s,%s,%s)' %
                    (getattr(response, 'status_code', 'N/A'),
                     channel_id,
                     url,
                     cache.get_attr(channel_id, 'CLIENT_KEY'),
                     cache.get_attr(channel_id, 'PREFIX')))
        cache.clean_cache(channel_id=channel_id, model=xmodel)
        return {}

    def get_csv_response(self, channel_id, xmodel, ext_id=False, mode=None):
        self.logmsg(channel_id,
                    '%s.get_csv_response(%s, ext_id=%s):' % (
                        xmodel, channel_id, ext_id or -1
                    ))
        cache = self.env['ir.model.synchro.cache']
        endpoint = cache.get_attr(channel_id, 'EXCHANGE_PATH')
        if not endpoint:
            _logger.error(
                'Channel %s without connection parameters!' % channel_id)
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
        with open(file_csv, 'rb') as fd:
            hdr = False
            reader = csv.DictReader(fd,
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
                for ix, value in enumerate(row):
                    if (isinstance(value, basestring) and
                            value.isdigit() and
                            not value.startswith('0')):
                        value = int(value)
                    elif (isinstance(value, basestring) and
                            value.startswith('[') and
                            value.endswith(']')):
                        value = eval(value)
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
                    if xmodel == 'res.partner.invoice':
                        row_res = row_billing
                    else:
                        row_res['billing'] = row_billing
                if row_shipping:
                    if xmodel == 'res.partner.shipping':
                        for nm in ('customer_shipping_id', 'customer_id'):
                            row_shipping[nm] = row_res[nm]
                        row_res = row_shipping
                    else:
                        row_res['shipping'] = row_shipping
                if row_contact:
                    row_res['contact'] = row_contact
                if ext_id and row_res[ext_key_id] != ext_id:
                    continue
                if ext_id:
                    res = row_res
                    break
                res.append(row_res)
                # res.append(row_res[ext_key_id])
        return res

    def get_counterpart_response(
            self, channel_id, xmodel, ext_id=False, mode=None):
        """Get data from counterpart"""
        cache = self.env['ir.model.synchro.cache']
        cache.open(channel_id=channel_id, model=xmodel)
        method = cache.get_attr(channel_id, 'METHOD')
        if method == 'XML':
            return self.get_xmlrpc_response(
                channel_id, xmodel, ext_id, mode=mode)
        elif method == 'JSON':
            return self.get_json_response(
                channel_id, xmodel, ext_id, mode=mode)
        elif method == 'CSV':
            return self.get_csv_response(
                channel_id, xmodel, ext_id, mode=mode)

    def assign_channel(self, vals, model=None, ext_model=None):
        cache = self.env['ir.model.synchro.cache']
        odoo_prio = 9999
        channel_prio = 9999
        odoo_channel = def_channel = channel_from = False
        channel_ctr = 0
        for channel_id in cache.get_channel_list():
            if channel_from:
                break
            channel_ctr += 1
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
        if not channel_from and channel_ctr < 4:
            cache.setup_channels(all=True)
            return self.assign_channel(vals)
        if not channel_from:
            if channel_prio < odoo_prio:
                channel_from = def_channel
            else:
                channel_from = odoo_channel
        return channel_from

    @api.model
    def synchro_childs(
            self, channel_id, xmodel, actual_model, parent_id, ext_id):
        cache = self.env['ir.model.synchro.cache']
        child_ids = cache.get_struct_model_attr(
            actual_model, 'CHILD_IDS', default=False)
        model_child = cache.get_struct_model_attr(actual_model, 'MODEL_CHILD')
        if not child_ids and not model_child:
            _logger.error('!-5! Invalid structure of %s!' % xmodel)
            return -5
        cache.open(model=model_child)
        # Retrieve header id field
        parent_id_name = cache.get_struct_model_attr(model_child, 'PARENT_ID')
        if not parent_id_name:
            _logger.error('!-5! Invalid structure of %s!' % xmodel)
            return -5
        cls = self.get_actual_model(model_child)
        rec_ids = cache.get_model_attr(channel_id, xmodel,
                                 '__%s_ids' % actual_model)
        cache.del_model_attr(channel_id, xmodel, '__%s_ids' % actual_model)
        if not rec_ids:
            rec_ids = self.get_counterpart_response(channel_id,
                                                    model_child,
                                                    ext_id=ext_id,
                                                    mode=parent_id_name)
        if not rec_ids:
            return ext_id
        ext_key_id = cache.get_model_attr(
            channel_id, model_child, 'KEY_ID', default='id')
        for item in rec_ids:
            if isinstance(item, (int, long)):
                vals = self.get_counterpart_response(
                    channel_id, model_child, ext_id=item)
                if ext_key_id not in vals:
                    self.logmsg(channel_id,
                                'Data received of model %s w/o id' %
                                model_child)
                    continue
            else:
                vals = item
                vals[':%s' % parent_id_name] = parent_id
            try:
                id = self.generic_synchro(cls,
                                           vals,
                                           channel_id=channel_id,
                                           jacket=True)
                if id < 0:
                    self.logmsg(
                        channel_id,
                        'External id %s error pulling from %s' %
                        (item, model_child))
                    return id
                # commit every table to avoid too big transaction
                self.env.cr.commit()       # pylint: disable=invalid-commit
            except BaseException:
                self.logmsg(channel_id,
                            'External id %s error pulling from %s' %
                            (item, model_child))
                return -1
        self.commit(self.env[actual_model], parent_id)
        return ext_id

    @api.model
    def synchro(self, cls, vals, disable_post=None):

        def pop_ref(channel_id, xmodel, actual_model, id, ext_id):
            cache.pop_id(channel_id, xmodel, actual_model,
                         loc_id=id, ext_id=ext_id)

        vals = unicodes(vals)
        xmodel = cls.__class__.__name__
        _logger.info('> %s.synchro(%s,%s)' % (xmodel, vals, disable_post))
        actual_model = self.get_actual_model(xmodel, only_name=True)
        actual_cls = self.get_actual_model(xmodel)
        cache = self.env['ir.model.synchro.cache']
        cache.open(model=xmodel, cls=cls)
        channel_id = self.assign_channel(vals)
        if not channel_id:
            cache.clean_cache()
            _logger.error('!-6! No channel found!')
            return -6
        self.logmsg(channel_id, '### assigned channel is %s' % channel_id)

        if hasattr(actual_cls, 'CONTRAINTS'):
            constraints = actual_cls.CONTRAINTS
        else:
            constraints = []
        has_state = cache.get_struct_model_attr(
            actual_model, 'MODEL_STATE', default=False)
        has_2delete = cache.get_struct_model_attr(
            actual_model, 'MODEL_2DELETE', default=False)
        child_ids = cache.get_struct_model_attr(
            actual_model, 'CHILD_IDS', default=False)
        model_child = cache.get_struct_model_attr(actual_model, 'MODEL_CHILD')
        if child_ids and model_child:
            parent_child_mode = 'A'
        else:
            parent_child_mode = ''
        do_auto_process = True
        if has_2delete or (cache.get_model_attr(channel_id, xmodel, 'BIND') and
                           cache.get_attr(channel_id, 'IDENTITY') == 'vg7'):
            do_auto_process = False
        # Protect against VG7 mistakes
        if cache.get_attr(channel_id, 'IDENTITY') == 'vg7':
            if 'vg7_id' in vals and 'vg7:id' not in vals:
                vals['vg7:id'] = vals['vg7_id']
                del vals['vg7_id']
                _logger.warning('Deprecated field name %s: please use %s!' % (
                    'vg7_id', 'vg7:id'))
            if 'id' in vals:
                del vals['id']
                _logger.warning('Ignored field name %s!' % 'id')
            if xmodel == 'sale.order':
                for nm in ('partner_id', 'partner_shipping_id'):
                    if nm in vals:
                        del vals[nm]
                        _logger.warning('Ignored field name %s!' % nm)
        if (xmodel == 'res.partner' and vals.get('type') and
                cache.get_attr(channel_id, 'IDENTITY') == 'vg7'):
            xmodel = self.get_xmodel(actual_model, vals['type'])
            cache.open(model=xmodel)
        cache.open(channel_id=channel_id, ext_model=xmodel)
        if xmodel == actual_model:
            if hasattr(cls, 'preprocess'):
                vals, spec = cls.preprocess(channel_id, vals)
                if spec:
                    xmodel = self.get_xmodel(actual_model, spec)
                    actual_model = self.get_actual_model(xmodel)
                    cache.open(model=xmodel)
            elif do_auto_process:
                vals, spec = self.preprocess(channel_id, xmodel, vals)
        vals, ref_in_queue = self.map_to_internal(
            channel_id, xmodel, vals, disable_post)
        if child_ids and model_child and child_ids in vals:
            # TODO parent_child_mode = 'C'
            # if isinstance(vals[child_ids], dict):
            #     parent_child_mode = 'C'
            #     for x in vals[child_ids].keys():
            #         if x.find(':') >= 0:
            #             parent_child_mode = 'B'
            #             break
            # elif (isinstance(vals[child_ids], (list, tuple)) and
            #       len(vals[child_ids]) == 1 and
            #       len(vals[child_ids][0] >= 3) and
            #       vals[child_ids][0][0] == 0 and
            #       vals[child_ids][0][1] == 0):
            #     parent_child_mode = 'C'
            #     vals[child_ids] = vals[child_ids][0][2:]
            # else:
            #     parent_child_mode = 'B'
            parent_child_mode = 'B'
            if parent_child_mode == 'B':
                cache.set_model_attr(channel_id, xmodel,
                                     '__%s_ids' % actual_model,
                                     vals[child_ids])
                del vals[child_ids]
        loc_ext_id = self.get_loc_ext_id_name(channel_id, xmodel)
        ext_id = vals.get(loc_ext_id)

        id = -1
        rec = None
        if 'id' in vals:
            id = vals.pop('id')
            rec = actual_cls.search([('id', '=', id)])
            if not rec or rec.id != id:
                _logger.error('!-3! ID %s does not exist in %s' %
                              (id, xmodel))
                pop_ref(channel_id, xmodel, actual_model, id, ext_id)
                return -3
            id = rec.id
            self.logmsg(channel_id, '### synchro: found id=%s.%s' % (
                actual_model, id))
        if id < 0:
            id, rec = self.bind_record(channel_id, xmodel, vals, constraints)
        if has_state:
            vals, erc = self.set_state_to_draft(xmodel, rec, vals)
            if erc < 0:
                _logger.error('!%s! Returned error code!' % erc)
                pop_ref(channel_id, xmodel, actual_model, id, ext_id)
                return erc
            # TODO: Workaround
            if xmodel == 'stock.picking.package.preparation':
                id = -1
        elif has_2delete:
            vals['to_delete'] = False
        self.drop_invalid_fields(xmodel, vals)
        do_write = True
        if id > 0 and parent_child_mode == 'C':
            parent_child_mode = 'B'
            cache.set_model_attr(channel_id, xmodel,
                                 '__%s_ids' % actual_model,
                                 vals[child_ids])
            del vals[child_ids]
        if id < 1:
            if (has_state or has_2delete or not ext_id or
                    parent_child_mode == 'C'):
                min_vals = vals
                do_write = False
            else:
                min_vals = {loc_ext_id: ext_id}
                for nm in ('name', 'type', 'parent_id'):
                    if vals.get(nm):
                        min_vals[nm] = vals[nm]
                do_write = True
                min_vals = self.set_default_values(
                    cls, channel_id, xmodel, min_vals)
                if not min_vals or min_vals == vals:
                    min_vals = vals
                    do_write = False
            if not do_write:
                vals = self.set_default_values(cls, channel_id, xmodel, vals)
            if vals:
                try:
                    id = actual_cls.create(min_vals).id
                    if not do_write and min_vals != vals:
                        self.logmsg(channel_id,
                                    '>>> %s=%s.min_create(%s)' % (
                                        id, actual_model, min_vals))
                    else:
                        self.logmsg(channel_id,
                            '>>> %s=%s.create(%s)' % (id, actual_model, vals))
                except BaseException, e:
                    _logger.error('!-1! %s creating %s' % (e, xmodel))
                    pop_ref(channel_id, xmodel, actual_model, id, ext_id)
                    # Try to open new transaction
                    self.env.cr.rollback()  # pylint: disable=invalid-commit
                    return -1
        if id > 0 and do_write:
            try:
                rec = actual_cls.with_context(
                    {'lang': self.env.user.lang}).browse(id)
            except IOError:
                _logger.error('Error reading %s ID=%s' %
                              (actual_model, id))
                rec = None
            if rec:
                if vals:
                    vals = self.drop_protected_fields(
                        channel_id, xmodel, vals, rec)
                if hasattr(cls, 'assure_values'):
                    vals = actual_cls.assure_values(vals, rec)
                if vals:
                    try:
                        rec.write(vals)
                        self.logmsg(channel_id,
                                    '>>> synchro: %s.write(%s)' % (
                                        actual_model, vals))
                    except BaseException, e:
                        _logger.error('%s writing %s ID=%s' %
                                      (e, actual_model, id))
                        pop_ref(channel_id, xmodel, actual_model, id, ext_id)
                        # Try to open new transaction
                        self.env.cr.rollback() # pylint: disable=invalid-commit
                        return -2
                elif do_write:
                    self.logmsg(channel_id,
                                '### Nothing to update(%s.%s)' % (
                                    actual_model, id))
                if (do_write and
                        rec and child_ids and
                        hasattr(rec, child_ids)):
                    for num, line in enumerate(rec[child_ids]):
                        seq = num + 1
                        if not hasattr(line, 'to_delete'):
                            child_vals = {}
                        else:
                            child_vals = {'to_delete': True}
                        if actual_model == 'account.payment.term':
                            vals['sequence'] = seq
                        if child_vals:
                            try:
                                line.write(child_vals)
                            except BaseException:
                                # Try to open new transaction
                                self.env.cr.rollback() # pylint: disable=invalid-commit

        # commit to avoid lost data in recursive write
        self.env.cr.commit()   # pylint: disable=invalid-commit
        done_post = False
        if id > 0 and not disable_post and xmodel == actual_model:
            if hasattr(cls, 'postprocess'):
                done_post = cls.postprocess(channel_id, id, vals)
            elif do_auto_process:
                done_post = self.postprocess(channel_id, xmodel, id, vals)
            self.synchro_queue(channel_id)
        if parent_child_mode in ('A', 'B') and not done_post:
            self.synchro_childs(channel_id, xmodel, actual_model, id, ext_id)
        pop_ref(channel_id, xmodel, actual_model, id, ext_id)
        _logger.info('!%s! Returned ID of %s' % (id, xmodel))
        return id

    @api.model
    def commit(self, cls, loc_id, ext_id=None):
        xmodel = cls.__class__.__name__
        actual_model = self.get_actual_model(xmodel, only_name=True)
        _logger.info('> %s.commit(%s,%s)' % (xmodel, loc_id, ext_id or -1))
        cache = self.env['ir.model.synchro.cache']
        _logger.info('>>> cache.open(model=%s, cls=%s)' % (xmodel, cls))    ##debug
        cache.open(model=xmodel, cls=cls)
        has_state = cache.get_struct_model_attr(
            actual_model, 'MODEL_STATE', default=False)
        child_ids = cache.get_struct_model_attr(
            actual_model, 'CHILD_IDS', default=False)
        model_child = cache.get_struct_model_attr(actual_model, 'MODEL_CHILD')
        if not has_state and not child_ids and not model_child:
            _logger.error('!-5! Invalid structure of %s!' % xmodel)
            return -5
        cache.open(model=model_child)
        # Retrieve header id field
        parent_id = cache.get_struct_model_attr(model_child, 'PARENT_ID')
        if not parent_id:
            _logger.error('!-5! Invalid structure of %s!' % xmodel)
            return -5
        if (not loc_id or loc_id < 1) and ext_id:
            loc_id = self.bind_record(
                1,
                xmodel,
                {'id': ext_id},
                [], False,)
        try:
            rec_2_commit = self.get_actual_model(xmodel).browse(loc_id)
        except:
            _logger.error('!-3! Errore retriving %s.%s!' % (xmodel, loc_id))
            return -3
        if cache.get_struct_model_attr(model_child, 'MODEL_2DELETE'):
            cls = self.get_actual_model(model_child)
            for rec in cls.search([(parent_id, '=', loc_id),
                                        ('to_delete', '=', True)]):
                rec.unlink()
        loc_id = self.set_actual_state(xmodel, rec_2_commit)
        if loc_id < 0:
            _logger.error('!%s! Committed ID' % loc_id)
        else:
            _logger.info('!%s! Committed ID' % loc_id)
        return loc_id

    @api.model
    def generic_synchro(self, cls, vals, disable_post=None, jacket=None,
                        channel_id=None):
        cache = self.env['ir.model.synchro.cache']
        if hasattr(cls, 'synchro'):
            if jacket:
                return cls.synchro(self.jacket_vals(
                    cache.get_attr(channel_id, 'PREFIX'),
                    vals), disable_post=disable_post)
            else:
                return cls.synchro(vals, disable_post=disable_post)
        else:
            if jacket:
                return self.synchro(cls, self.jacket_vals(
                    cache.get_attr(channel_id, 'PREFIX'),
                    vals), disable_post=disable_post)
            else:
                return self.synchro(cls, vals, disable_post=disable_post)

    @api.model
    def jacket_vals(self, prefix, vals):
        jvals = {}
        for name in vals:
            if name.startswith(prefix):
                jvals[name] = vals[name]
            elif name.startswith(':'):
                jvals[name[1:]] = vals[name]
            else:
                jvals['%s:%s' % (prefix, name)] = vals[name]
        return jvals

    @api.model
    def preprocess(self, channel_id, xmodel, vals):
        _logger.info(
            '> preprocess(%s,%s)' % (xmodel, vals))
        actual_model = self.get_actual_model(xmodel, only_name=True)
        cache = self.env['ir.model.synchro.cache']
        cache.open(model=xmodel)
        child_ids = cache.get_struct_model_attr(
            actual_model, 'CHILD_IDS', default=False)
        min_vals = {}
        loc_id = False
        ext_id = False
        loc_ext_id = False
        stored_field = '__%s' % xmodel
        for ext_ref in vals:
            ext_name, loc_name, is_foreign = self.name_from_ref(
                channel_id, xmodel, ext_ref)
            if ext_name == 'id':
                ext_id = vals[ext_ref]
                loc_ext_id = loc_name
            elif loc_id == 'id':
                loc_id = vals[ext_ref]
            if ext_ref == child_ids:
                pass
            elif (not cache.get_struct_model_field_attr(
                    actual_model, loc_name, 'ttype') in (
                    'many2one', 'one2many', 'many2many') or
                    cache.get_struct_model_field_attr(
                        actual_model, loc_name, 'required')):
                min_vals[ext_ref] = vals[ext_ref]
        if (ext_id and
                loc_ext_id in cache.get_struct_attr(actual_model) and
                not self.env[actual_model].search(
                    [(loc_ext_id, '=', ext_id)]) or
                loc_id and not self.env[actual_model].search(
                    [('id', '=', loc_id)])):
            cache.set_model_attr(
                channel_id, xmodel, stored_field, vals)
            vals = min_vals
        return vals, ''

    @api.model
    def postprocess(self, channel_id, model, parent_id, vals):
        _logger.info(
            '> postprocess(%s,%s,%s)' % (parent_id, model, vals))  # debug
        cache = self.env['ir.model.synchro.cache']
        cache.open(model=model)
        cls = self.env[model]
        stored_field = '__%s' % model
        done = False
        if cache.get_model_attr(channel_id, model, stored_field):
            vals = cache.get_model_attr(channel_id, model, stored_field)
            cache.del_model_attr(channel_id, model, stored_field)
            self.generic_synchro(cls, vals, disable_post=True)
            done = True
        return done

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
            if not loc_id or loc_id < 1:
                _logger.errore('> invalid queue(%s,%s)?' % (xmodel, loc_id))
                return
            _logger.info('> queued_pull(%s,%s)?' % (xmodel, loc_id))
            rec = self.get_actual_model(xmodel).browse(loc_id)
            loc_ext_id = self.get_loc_ext_id_name(channel_id, xmodel)
            if hasattr(rec, loc_ext_id):
                # commit previous record
                # self.env.cr.commit()  # pylint: disable=invalid-commit
                self.pull_1_record(
                    channel_id, xmodel, getattr(rec, loc_ext_id))

    @api.multi
    def pull_recs_2_complete(self, only_model=None):
        _logger.info('> pull_recs_2_complete(%s)' % only_model)
        cache = self.env['ir.model.synchro.cache']
        cache.open()
        cache.setup_channels(all=True)
        for channel_id in cache.get_channel_list():
            for xmodel in cache.get_channel_models(channel_id):
                if not cache.is_struct(xmodel):
                    continue
                actual_model = self.get_actual_model(xmodel, only_name=True)
                if not cache.get_struct_model_attr(
                        actual_model, 'MODEL_WITH_NAME'):
                    continue
                if only_model and xmodel == only_model:
                    continue
                self.logmsg(channel_id, '### Pulling %s' % xmodel)
                cls = self.env[xmodel]
                recs = cls.search([('name', 'like', 'Unknown ')])

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
                    for vals in datas:
                        if not vals:
                            continue
                        cls.synchro(self.jacket_vals(
                            cache.get_attr(channel_id, 'PREFIX'),
                            vals))
                        # commit every table to avoid too big transaction
                        # self.env.cr.commit()   # pylint: disable=invalid-commit
            _logger.info('Channel %s successfuly pulled' % channel_id)

    @api.multi
    def pull_full_records(self, force=None, only_model=None,
                          only_complete=None, select=None):
        """Called by import wizard
        @only_complete: import only records which name starting with 'Unknown'
        """
        _logger.info('> pull_full_records(%s,%s,%s)' % (
            force, only_model, select))
        if not select:
            if force:
                select = 'all'
            elif only_complete:
                select = 'upd'
            else:
                select = 'new'
        cache = self.env['ir.model.synchro.cache']
        cache.open()
        cache.setup_channels(all=True)
        local_ids = []
        for channel_id in cache.get_channel_list().copy():
            if (not cache.get_attr(channel_id, 'COUNTERPART_URL') and
                    not cache.get_attr(channel_id, 'EXCHANGE_PATH')):
                continue
            identity = cache.get_attr(channel_id, 'IDENTITY')
            if identity == 'odoo':
                if only_model:
                    model_list = [only_model]
                else:
                    model_list = self.env[
                        'ir.model.synchro.cache'].TABLE_DEF.keys()
            else:
                domain = [('synchro_channel_id', '=', channel_id)]
                if only_model:
                    domain.append(('name', '=', only_model))
                model_list = [x.name for x in self.env[
                    'synchro.channel.model'].search(domain,
                        order='sequence')]
            ctr = 0
            for xmodel in model_list:
                cache.open(model=xmodel)
                actual_model = self.get_actual_model(xmodel, only_name=True)
                if (only_complete and
                        not cache.get_struct_model_attr(
                            actual_model, 'MODEL_WITH_NAME')):
                    continue
                if (identity != 'odoo' and not only_complete and
                        not cache.get_model_attr(
                            channel_id, xmodel, '2PULL', default=False)):
                    self.logmsg(channel_id,
                                '### Model %s not pullable' % xmodel)
                    continue
                self.logmsg(channel_id, '### Pulling %s' % xmodel)
                cls = self.env[xmodel]
                datas = self.get_counterpart_response(
                    channel_id, xmodel)
                if not datas:
                    continue
                if not isinstance(datas, (list, tuple)):
                    datas = [datas]
                if len(datas) and isinstance(datas[0], (int, long)):
                    datas.sort()
                ext_key_id = cache.get_model_attr(
                    channel_id, xmodel, 'KEY_ID', default='id')
                loc_ext_id = self.get_loc_ext_id_name(channel_id,
                                                      xmodel)
                for item in datas:
                    if not item:
                        continue
                    if isinstance(item, (int, long)):
                        vals = {}
                        ext_id = item
                    else:
                        vals = item
                        if isinstance(vals[ext_key_id], (int, long)):
                            ext_id = vals[ext_key_id]
                        else:
                            ext_id = int(vals[ext_key_id])
                    if (select == 'new' and
                            cls.search([(loc_ext_id, '=', ext_id)])):
                        continue
                    elif (select == 'upd' and
                          not cls.search([(loc_ext_id, '=', ext_id)])):
                        continue
                    if not vals:
                        vals = self.get_counterpart_response(
                            channel_id, xmodel, ext_id=ext_id)
                    if ext_key_id not in vals:
                        self.logmsg(channel_id,
                                    'Data received of model %s w/o id' %
                                    xmodel)
                        continue
                    try:
                        ctr += 1
                        id = self.generic_synchro(cls,
                                                   vals,
                                                   channel_id=channel_id,
                                                   jacket=True)
                        if id < 0:
                            self.logmsg(
                                channel_id,
                                'External id %s error pulling from %s' %
                                (ext_id, xmodel))
                            continue
                        # commit every table to avoid too big transaction
                        self.env.cr.commit()   # pylint: disable=invalid-commit
                        if id not in local_ids:
                            local_ids.append(id)
                        # cache.set_loglevel('debug')
                    except BaseException:
                        self.logmsg(channel_id,
                                    'External id %s error pulling from %s' %
                                    (ext_id, xmodel))
            _logger.info('%s record successfuly pulled from channel %s' % (
                ctr, channel_id))
        return local_ids

    @api.model
    def pull_1_record(self, channel_id, xmodel, ext_id, disable_post=None):
        _logger.info('> pull_1_record(%s,%s,%s)' % (
            channel_id, xmodel, ext_id))
        vals = self.get_counterpart_response(channel_id, xmodel, ext_id)
        if not vals:
            return
        if isinstance(vals, (list, tuple)):
            vals = vals[0]
        cache = self.env['ir.model.synchro.cache']
        ext_key_id = cache.get_model_attr(
            channel_id, xmodel, 'KEY_ID', default='id')
        if ext_key_id not in vals:
            self.logmsg(channel_id,
                        'Data received of model %s w/o id' %
                        xmodel)
            return
        cls = self.env[xmodel]
        return self.generic_synchro(cls, vals, disable_post=disable_post,
                                    jacket=True, channel_id=channel_id)

    @api.multi
    def pull_record(self, cls, channel_id=None):
        """Button synchronize at record UI page"""
        cache = self.env['ir.model.synchro.cache']
        for rec in cls:
            model = cls.__class__.__name__
            cache.open(model=model, cls=cls)
            if not cache.is_struct(model):
                continue
            cache.setup_channels(all=True)
            for channel_id in cache.get_channel_list().copy():
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
                        self.pull_1_record(channel_id, xmodel, ext_id)
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
                                self.pull_1_record(
                                    channel_id, xmodel, ext_id)

    @api.model
    def trigger_one_record(self, ext_model, prefix, ext_id):
        _logger.info('> trigger_one_record(%s,%s,%s)' % (
            ext_model, ext_id or -1, prefix))
        if not prefix:
            return
        cache = self.env['ir.model.synchro.cache']
        # cache.open(ext_model=ext_model)
        channel_id = self.assign_channel({'%s:' % prefix: ''})
        if not channel_id:
            cache.clean_cache()
            _logger.error('!-6! No channel found!')
            return -6
        self.logmsg(channel_id, '### assigned channel is %s' % channel_id)
        cache.open(channel_id=channel_id, ext_model=ext_model)
        # identity = cache.get_attr(channel_id, 'IDENTITY')
        for model in cache.get_channel_models(channel_id):
            if not cache.is_struct(model):
                continue
            if ext_model != cache.get_model_attr(channel_id, model, 'BIND'):
                continue
            self.logmsg(
                channel_id, '### Pulling %s.%s' % (model, ext_id))
            return self.pull_1_record(channel_id, model, ext_id)
        return -8


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
