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


PROTECTION

Every field can be protect against update. There are 4 protection levels:
0 -> 'Always Update': field may be update by counterpart (default)
1 -> 'But new value not empty':
      field may be update only by not null counterpart value
2 -> 'But current value is empty': field may be update only if is null
3 -> 'Protected field': field cannot be update by counterpart
4 -> 'Counter field': field is an integer and value is the max(local,remote)


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
- 'QUEUE_SYNC': queue records
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
   -10: Cannot update record state
  -100: if return code < -100 means error on child records
"""
import logging
import os
from datetime import datetime, timedelta
import time
import csv

import requests
from odoo import api, fields, models, _
from odoo import release

_logger = logging.getLogger(__name__)
try:
    from python_plus import unicodes
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

WORKFLOW = {
    0: {'model': 'ir.module.category', 'only_minimal': True},
    1: {'model': 'ir.module.module'},
    2: {'model': 'res.lang'},
    3: {'model': 'res.country',
        'no_deep_fields': ['country_group_ids', 'state_ids']},
    4: {'model': 'res.country.state'},
    5: {'model': 'res.currency', 'no_deep_fields': ['rate_ids']},
    6: {'model': 'res.groups', 'only_minimal': True},
    7: {'model': 'res.partner', 'select': 'new', 'only_minimal': True,
        'remote_ids': '1-10'},
    8: {'model': 'res.users', 'only_minimal': True,
        'no_deep_fields': ['*', 'partner_id']},
    9: {'model': 'res.company', 'no_deep_fields': ['*', 'partner_id']},
    10: {'model': 'account.account.type'},
    11: {'model': 'account.account',
        'no_deep_fields': ['*', 'company_id', 'user_type_id', 'tag_ids']},
    12: {'model': 'account.tax',
         'no_deep_fields': ['*', 'company_id', 'account_id']},
    13: {'model': 'res.bank'},
    14: {'model': 'ir.sequence'},
    15: {'model': 'account.journal',
         'no_deep_fields': ['*', 'company_id', 'currency_id',
                            'default_credit_account_id',
                            'default_debit_account_id', 'sequence_id']},
    16: {'model': 'account.payment.term'},
    17: {'model': 'account.fiscal.position', 'only_minimal': True},
    18: {'model': 'res.partner',
         'no_deep_fields': ['*', 'company_id', 'category_id', 'country_id',
                           'parent_id', 'state_id']},
    19: {'model': 'res.partner.bank'},
    20: {'model': 'product.uom'},
    21: {'model': 'product.category'},
    22: {'model': 'product.template',
         'no_deep_fields': ['*', 'company_id', 'categ_id',
                            'property_account_expense_id',
                            'property_account_income_id', 'taxes_id',
                            'uom_id', 'uom_po_id']},
    23: {'model': 'product.attribute'},
    24: {'model': 'product.product'},
    25: {'model': 'product.pricelist'},
    26: {'model': 'product.supplierinfo'},
    27: {'model': 'italy.ade.codice.carica'},
    28: {'model': 'italy.ade.invoice.type'},
    29: {'model': 'italy.ade.tax.nature'},
    30: {'model': 'riba.configuration'},
    31: {'model': 'riba.distinta'},
    32: {'model': 'withholding.tax'},
    33: {'model': 'stock.ddt.type'},
    34: {'model': 'stock.picking.carriage_condition'},
    35: {'model': 'stock.picking.goods_description'},
    36: {'model': 'stock.picking.transportation_method'},
    37: {'model': 'stock.picking.transportation_reason'},
    38: {'model': 'stock.location',
         'no_deep_fields': ['*', 'company_id', 'location_id', 'partner_id',
                            'valuation_in_account_id',
                            'valuation_out_account_id']},
    39: {'model': 'stock.warehouse',
         'no_deep_fields': ['*', 'company_id', 'partner_id']},
    40: {'model': 'stock.move',
         'no_deep_fields': ['*', 'company_id', 'partner_id', 'product_id']},
    41: {'model': 'stock.picking',
         'no_deep_fields': ['*', 'company_id', 'move_lines', 'partner_id',
                            'product_id']},
    42: {'model': 'sale.order'},
    43: {'model': 'stock.picking.package.preparation'},
    44: {'model': 'procurement.order'},
    45: {'model': 'purchase.order'},
    46: {'model': 'account.invoice'},
    47: {'model': 'stock.production.lot'},
    48: {'model': 'stock.quant'},
    49: {'model': 'account.move'},
    50: {'model': 'account.full.reconcile'},
    51: {'model': 'account.partial.reconcile'},
    52: {'model': 'fatturapa.attachment.in'},
    53: {'model': 'fatturapa.attachment.out'},
    54: {'model': 'fatturapa.attachments'},
    55: {'model': 'account.analytic.account',
         'no_deep_fields': ['*', 'company_id', 'company_uom_id', 'currency_id',
                            'partner_id', 'tag_ids']},
    56: {'model': 'project.project'},
    57: {'model': 'project.task'},
    58: {'model': 'delivery.carrier'},
    59: {'model': 'res.partner'},
    60: {'model': 'account.account'},
    61: {'model': 'account.tax'},
    62: {'model': 'account.journal'},
    63: {'model': 'account.fiscal.position'},
    64: {'model': 'causale.pagamento'},
    65: {'model': 'account.vat.period.end.statement'},
    66: {'model': 'crm.team'},
    67: {'model': 'crm.lead'},
    68: {'model': 'crm.stage'},
    69: {'model': 'crm.activity'},
    70: {'model': 'stock.location'},
    71: {'model': 'stock.warehouse'},
    72: {'model': 'stock.move'},
    73: {'model': 'stock.picking'},
    74: {'model': 'account.analytic.account'},
    75: {'model': 'res.users'},
    76: {'model': 'mail.mail'},
    77: {'model': 'mail.message'},
}


class IrModelSynchro(models.Model):
    _name = 'ir.model.synchro'
    _inherit = 'ir.model'

    LOGLEVEL = 'debug'
    DEF_INCL_FLDS = [
        'action', 'category_id', 'code', 'company_ids', 'country_id',
        'description', 'default_code', 'journal_id', 'location_id',
        'location_dest_id', 'login', 'name', 'parent_id', 'partner_id',
        'picking_type_id', 'product_id', 'product_uom', 'type', 'user_type_id'
    ]
    DEF_EXCL_FLDS = ['user_ids', 'sale_order_ids', 'meeting_ids']

    def _build_unique_index(self, model, prefix):
        '''Build unique index on table to <vg7>_id for performance'''
        if isinstance(model, (list, tuple)):
            table = model[0].replace('.', '_')
        else:
            table = model.replace('.', '_')
        index_name = '%s_unique_%s' % (table, prefix)
        self._cr.execute(  # pylint: disable=E8103
            "SELECT indexname FROM pg_indexes WHERE indexname = '%s'" %
            index_name
        )
        if not self._cr.fetchone():
            self._cr.execute(  # pylint: disable=E8103
                "CREATE UNIQUE INDEX %s on %s (%s_id) where %s_id<>0 and %s_id is not null" %
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

    def logmsg(self, loglevel, msg, rec=None, model=None, ctx=None):
        # cache = self.env['ir.model.synchro.cache']
        ctx = ctx or {}
        ctx['model'] = ctx.get('model', model or '')
        ctx['id'] = ctx.get('id', rec and rec.id or False)
        if isinstance(loglevel, basestring):
            reqloglevel = loglevel
            curloglevel = self.LOGLEVEL
        else:
            curloglevel = reqloglevel = self.LOGLEVEL
        loglevel2num = {
            'error': '4',
            'info': '3',
            'warning': '2',
            'debug': '1',
            'trace': '0',
        }
        reqloglevel = loglevel2num.get(reqloglevel, '2')
        curloglevel = loglevel2num.get(curloglevel, '3')
        try:
            full_msg = msg % ctx
        except:
            full_msg = msg
        if reqloglevel >= curloglevel:
            _logger.info(full_msg)
        if reqloglevel in ('0', '4'):
            self.env['ir.model.synchro.log'].logger(
                model, rec, full_msg)

    @api.model
    def get_xmodel(self, model, spec):
        xmodel = model
        if model == 'res.partner':
            if spec == 'delivery':
                xmodel = 'res.partner.shipping'
            elif spec in ('invoice', 'supplier'):
                xmodel = '%s.%s' % (model, spec)
        elif model == 'res.partner.bank':
            if spec == 'company':
                xmodel = 'res.partner.bank.company'
        return xmodel

    @api.model
    def get_actual_model(self, model, only_name=False):
        actual_model = model
        if model in ('res.partner.shipping',
                     'res.partner.invoice',
                     'res.partner.supplier',
                     'res.partner.bank.company'):
            actual_model = '.'.join([x for x in model.split('.')[:-1]])
        if only_name:
            return actual_model
        return self.env[actual_model]

    @api.model
    def get_spec_from_xmodel(self, xmodel):
        if xmodel == 'res.partner.shipping':
            return 'delivery'
        elif xmodel in ('res.partner.invoice',
                        'res.partner.supplier',
                        'res.partner.bank.company'):
            return xmodel.split('.')[-1]
        return ''

    @api.model
    def get_loc_ext_id_name(self, channel_id, model, spec=None, force=None):
        cache = self.env['ir.model.synchro.cache']
        xmodel = self.get_xmodel(model, spec)
        cache.open(model=xmodel)
        loc_ext_id_name = cache.get_model_attr(channel_id, xmodel, 'EXT_ID',
            default='%s_id' % cache.get_attr(channel_id, 'PREFIX'))
        if not force and not cache.get_struct_model_attr(
                self.get_actual_model(model, only_name=True), loc_ext_id_name):
            return ''
        return loc_ext_id_name

    @api.model
    def get_loc_ext_id_value(self, channel_id, model, ext_id, spec=None):
        cache = self.env['ir.model.synchro.cache']
        xmodel = self.get_xmodel(model, spec)
        cache.open(model=xmodel)
        offset = cache.get_model_attr(
            channel_id, xmodel, 'ID_OFFSET', default=0)
        if ext_id < offset:
            return ext_id + offset
        return ext_id

    @api.model
    def get_actual_ext_id_value(self, channel_id, model, ext_id, spec=None):
        cache = self.env['ir.model.synchro.cache']
        xmodel = self.get_xmodel(model, spec)
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
            'oe6': '6.1',
            'oe7': '7.0',
            'oe8': '8.0',
            'oe9': '9.0',
            'oe10:': '10.0',
            'oe11:': '11.0',
            'oe12:': '12.0',
            'oe13:': '13.0',
            'oe14:': '14.0',
        }.get(prefix.split(':')[0], '')

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
                    (protect == 4 and rec[field] and
                     int(vals[field]) <= int(rec[field])) or
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
        self.logmsg('debug', '>>> %(model)s.set_state_to_draft(%(id)s)',
            model=model, rec=rec)
        errc = 0
        if 'state' in vals:
            vals['original_state'] = vals['state']
        elif rec:
            vals['original_state'] = rec.state
        if 'state' in vals:
            del vals['state']
        if (rec and rec.state == 'draft' and
                model != 'stock.picking.package.preparation'):
            return vals, errc
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
        elif model == 'purchase.order':
            if rec:
                rec._compute_date_planned()
                rec.write({})
                if rec.invoice_count > 0 or rec.picking_count > 0:
                    return vals, -4
                if rec.state == 'done':
                    return vals, -4
                elif rec.state == 'purchase':
                    rec.button_cancel()
                    rec.button_draft()
                elif rec.state == 'cancel':
                    rec.button_draft()
        elif model == 'stock.picking.package.preparation':
            if rec:
                try:
                    rec.unlink()
                    self.logmsg('debug', '>>> %(model)s.unlink(%(id)s)',
                        model=model, rec=rec)
                except IOError:
                    self.env.cr.rollback()  # pylint: disable=invalid-commit
                    errc = -2
        return vals, errc

    def set_actual_state(self, model, rec):
        self.logmsg('debug', '>>> %(model)s.set_actual_state(%(id)s)',
            model=model, rec=rec)
        if not rec:
            return -3
        cache = self.env['ir.model.synchro.cache']
        if model == 'account.invoice':
            rec.compute_taxes()
            # Please, do not remove this write: set default values in header
            rec.write({})
            if rec.state == rec.original_state:
                return rec.id
            elif rec.state != 'draft':
                self.logmsg('error',
                    '### Unauthorized state change of %(model)s.%(id)s',
                    model=model, rec=rec)
                return -4
            elif rec.original_state in ('open', 'paid'):
                try:
                    rec.action_invoice_open()
                except BaseException, e:
                    self.env.cr.rollback()  # pylint: disable=invalid-commit
                    self.logmsg('error',
                        'Error %(e) in %(model)s.set_actual_state()',
                        model=model, ctx={'e': e})
                    return -10
                if rec.name and rec.name.startswith('Unknown'):
                    rec.write({'name': rec.number})
            elif rec.original_state == 'cancel':
                rec.action_invoice_cancel()
        elif model == 'sale.order':
            # Please, do not remove this write: set default values in header
            rec.write({})
            if rec.state == rec.original_state:
                return rec.id
            elif rec.state != 'draft':
                self.logmsg('error',
                    '### Unauthorized state change of %(model)s.%(id)s',
                    model=model, rec=rec)
                return -4
            elif rec.original_state == 'sale':
                rec._amount_all()
                if cache.get_struct_model_attr('sale.order.line', 'agents'):
                    rec._compute_commission_total()
                try:
                    rec.action_confirm()
                except BaseException, e:
                    self.env.cr.rollback()  # pylint: disable=invalid-commit
                    self.logmsg('error',
                        'Error %(e) in %(model)s.set_actual_state()',
                        model=model, ctx={'e': e})
                    return -10
            elif rec.original_state == 'cancel':
                rec.action_cancel()
        elif model == 'purchase.order':
            # Please, do not remove this write: set default values in header
            rec.write({})
            if rec.state == rec.original_state:
                return rec.id
            elif rec.state != 'draft':
                self.logmsg('error',
                    '### Unauthorized state change of %(model)s.%(id)s',
                    model=model, rec=rec)
                return -4
            elif rec.original_state == 'purchase':
                rec._amount_all()
                try:
                    rec.button_confirm()
                except BaseException, e:
                    self.env.cr.rollback()  # pylint: disable=invalid-commit
                    self.logmsg('error',
                        'Error %(e) in %(model)s.set_actual_state()',
                        model=model, ctx={'e': e})
                    return -10
            elif rec.original_state == 'cancel':
                rec.button_cancel()
        elif model == 'stock.picking.package.preparation':
            try:
                rec.set_done()
            except BaseException, e:
                self.env.cr.rollback()  # pylint: disable=invalid-commit
                self.logmsg('error',
                    'Error %(e) in %(model)s.set_actual_state()',
                    model=model, ctx={'e': e})
                return -10
        return rec.id

    def sync_rec_from_counterpart(self, channel_id, model, vg7_id):
        if not vg7_id:
            self.logmsg('error',
                '### Missing id for %(model)s counterpart request',
                model=model)
            return False
        self.logmsg('debug',
            '>>> %(model)s.sync_rec_from_counterpart(%(id)s)',
            model=model, ctx={'id': vg7_id})
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
        self.logmsg('debug',
            '>>> %(model)s.create_new_ref(%(key)s,%(id)s,%(ext_id)s)',
            model=actual_model,
            ctx={'key': key_name, 'id': value, 'ext_id': ext_value})
        ctx = ctx or {}
        cache = self.env['ir.model.synchro.cache']
        xmodel = self.get_xmodel(actual_model, spec)
        loc_ext_id_name = self.get_loc_ext_id_name(channel_id, xmodel)
        cls = self.env[xmodel]
        vals = {key_name: value}
        if ext_value and loc_ext_id_name:
            vals[loc_ext_id_name] = self.get_loc_ext_id_value(
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
                vals['name'] = u'Unknown %s' % ext_value
            else:
                vals['name'] = u'%s=%s' % (key_name, value)
        elif (key_name != 'code' and
              cache.get_struct_model_attr(actual_model, 'code')):
            if ext_value:
                vals['name'] = u'Unknown %s' % ext_value
            else:
                vals['code'] = u'%s=%s' % (key_name, value)
        if actual_model == 'res.partner' and spec in ('delivery', 'invoice'):
            vals['type'] = spec
        if xmodel == 'stock.picking.goods_description':
            pass
        try:
            new_value = self.generic_synchro(
                cls, vals, disable_post=True, only_minimal=True)
            if new_value > 0:
                in_queue = cache.get_attr(channel_id, 'IN_QUEUE')
                in_queue.append([xmodel, new_value])
                cache.set_attr(channel_id, 'IN_QUEUE', in_queue)
            else:
                new_value = False
        except BaseException:
            self.logmsg('error',
                '### Failed %(model)s.synchro(%(vals)s)',
                model=xmodel, ctx={'vals': vals})
            new_value = False
        return new_value

    def do_search(self, actual_model, req_domain, only_id=None, spec=None):

        def exec_search(cls, domain, has_sequence):
            self.logmsg('debug',
                '>>> %(model)s.do_search(%(domain)s',
                model=cls.__class__.__name__,
                ctx={'domain': domain})
            if has_sequence:
                return cls.search(domain, order='sequence,id')
            else:
                return cls.search(domain)

        cache = self.env['ir.model.synchro.cache']
        cls = self.env[actual_model]
        maybe_dif = False
        has_sequence = cache.get_struct_model_attr(actual_model, 'sequence')
        if (len(req_domain) == 1 and
                not cache.get_struct_model_attr(
                    actual_model, req_domain[0][0])):
            domain = [('model', '=', actual_model),
                      ('ext_id_name', '=', req_domain[0][0]),
                      ('ext_id', req_domain[0][1], req_domain[0][2])]
            rec = self.env['ir.model.synchro.data'].search(domain)
            if rec:
                return cls.browse(rec.res_id), maybe_dif
            return rec, maybe_dif
        if only_id:
            return exec_search(cls, req_domain, has_sequence), maybe_dif
        domain = [x for x in req_domain]
        partner_domain = False
        if actual_model == 'res.partner' and spec in ('delivery', 'invoice'):
            domain.append(['type', '=', spec])
            partner_domain = True
        sale_domain = False
        if actual_model == 'account.tax':
            domain.append(['type_tax_use', '=', 'sale'])
            sale_domain = True
        rec = exec_search(cls, domain, has_sequence)
        if not rec and cache.get_struct_model_attr(actual_model, 'active'):
            domain.append(('active', '=', False))
            rec = exec_search(cls, domain, has_sequence)
        if not rec and (partner_domain or sale_domain):
            domain = [x for x in req_domain]
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
        self.logmsg('debug',
            '>>> %(model)s.get_rec_by_reference(%(name)s,%(id)s,%(m)s)',
            model=actual_model, ctx={'name': name, 'id': value, 'm': mode})
        ctx = ctx or {}
        cache = self.env['ir.model.synchro.cache']
        ext_id_name = cache.get_model_attr(
            channel_id, actual_model, 'KEY_ID', default='id')
        key_name = cache.get_model_attr(
            channel_id, actual_model, 'MODEL_KEY', default='name')
        if not key_name:
            return False
        xmodel = self.get_xmodel(actual_model, spec)
        loc_ext_id_name = self.get_loc_ext_id_name(channel_id, xmodel)
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
        if name not in (ext_id_name, loc_ext_id_name):
            if (cache.get_struct_model_attr(
                    actual_model, 'MODEL_WITH_COMPANY') and
                    ctx.get('company_id')):
                domain.append(('company_id', '=', ctx['company_id']))
            if (cache.get_struct_model_attr(
                    actual_model, 'MODEL_WITH_COUNTRY') and
                    ctx.get('country_id')):
                domain.append(('country_id', '=', ctx['country_id']))
        rec, maybe_dif = self.do_search(actual_model, domain, spec=spec)
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
        self.logmsg('debug',
            '>>> %(model)s.get_foreign_text(%(id)s)',
            model=actual_model, ctx={'id': value})
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
            loglevel = 'error'
        else:
            loglevel = 'info'
        self.logmsg(loglevel, '>>> return %(id)s # get_foreign_text()',
            ctx={'id': new_value})
        return new_value

    def get_foreign_ref(self, channel_id, actual_model, value_id, is_foreign,
                        ctx=None, spec=None):
        """Value is a local ID or an external ID (is_foreign=True)"""
        self.logmsg('debug',
            '>>> %(model)s.get_foreign_ref(%(id)s,spec=%(spec)s)',
            model=actual_model, ctx={'id': value_id, 'spec': spec})
        loc_ext_id_name = self.get_loc_ext_id_name(
            channel_id, actual_model, spec=spec, force=True)
        new_value = False
        if not value_id or value_id < 1:
            return new_value
        ext_value = value_id
        if is_foreign:
            if spec:
                value_id = self.get_loc_ext_id_value(
                    channel_id, actual_model, value_id, spec=spec)
            domain = [(loc_ext_id_name, '=', value_id)]
            rec, maybe_dif = self.do_search(
                actual_model, domain, only_id=True)
        else:
            domain = [('id', '=', value_id)]
            rec, maybe_dif = self.do_search(actual_model, domain, only_id=True)
        if rec:
            if len(rec) > 1:
                self.logmsg('debug', '### NO SINGLETON %(model)s.%(id)s',
                    model=actual_model, ctx={'id': value_id})
            new_value = rec[0].id
        xmodel = self.get_xmodel(actual_model, spec)
        if not new_value:
            if xmodel:
                new_value = self.sync_rec_from_counterpart(
                    channel_id, xmodel, value_id)
        if not new_value:
            new_value = self.create_new_ref(
                channel_id, xmodel, loc_ext_id_name, new_value, ext_value,
                ctx=ctx, spec=spec)
        self.logmsg('info', '>>> return %(id)s # get_foreign_ref()',
            ctx={'id': new_value})
        return new_value

    def get_foreign_value(self, channel_id, xmodel, value, name, is_foreign,
                          ctx=None, ttype=None, spec=None, fmt=None):
        """Value is an external ID or an external text"""
        self.logmsg('debug',
            '>>> %(model)s.get_foreign_value('
            '%(name)s,%(id)s,%(isf)s,%(type)s,%(spec)s)',
            model=xmodel, ctx={'name': name, 'id': value, 'isf': is_foreign,
                               'type': ttype, 'spec': spec})
        if not value:
            return value
        cache = self.env['ir.model.synchro.cache']
        actual_model = self.get_actual_model(xmodel, only_name=True)
        relation = cache.get_struct_model_field_attr(
            actual_model, name, 'relation')
        if not relation:
            raise RuntimeError(_('No relation for field %s of %s' % (name,
                                                                     xmodel)))
        if relation == actual_model and ttype == 'one2many':
            # Avoid recursive request, i.e. res.partner
            return []
        tomany = True if ttype in ('one2many', 'many2many') else False
        cache.open(channel_id=channel_id, model=relation)
        if isinstance(value, basestring):
            new_value = self.get_foreign_text(
                channel_id, relation, value, is_foreign,
                ctx=ctx, spec=spec)
            if not new_value or new_value < 1:
                new_value = False
            elif tomany:
                new_value = [new_value]
        elif isinstance(value, (list, tuple)):
            new_value = []
            for loc_id in value:
                new_id = self.get_foreign_ref(
                    channel_id, relation, loc_id, is_foreign,
                    ctx=ctx, spec=spec)
                if new_id and new_id > 0:
                    new_value.append(new_id)
        else:
            new_value = self.get_foreign_ref(
                channel_id, relation, value, is_foreign,
                ctx=ctx, spec=spec)
            if not new_value or new_value < 1:
                new_value = False
            elif tomany:
                new_value = [new_value]
        if fmt == 'cmd' and new_value and tomany:
            new_value = [(6, 0, new_value)]
        if not new_value:
            loglevel = 'error'
        else:
            loglevel = 'info'
        self.logmsg(loglevel, '>>> return %(id)s # get_foreign_value()',
            model=relation, ctx={'id': new_value})
        return new_value

    def name_from_ref(self, channel_id, xmodel, ext_ref):
        cache = self.env['ir.model.synchro.cache']
        pfx_depr = '%s_' % cache.get_attr(channel_id, 'PREFIX')
        pfx_ext = '%s:' % cache.get_attr(channel_id, 'PREFIX')
        identity = cache.get_attr(channel_id, 'IDENTITY')
        ext_odoo_ver = self.get_ext_odoo_ver(pfx_ext)
        tnldict = self.get_tnldict(channel_id) if identity == 'odoo' else {}
        loc_ext_id_name = self.get_loc_ext_id_name(
            channel_id, xmodel, force=True)
        ext_id_name = cache.get_model_attr(
            channel_id, xmodel, 'KEY_ID', default='id')
        if ext_ref == loc_ext_id_name:
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
            self.logmsg('warning', '### Deprecated field name %(id)s!',
                ctx={'id': ext_ref})

        elif ext_ref.startswith(pfx_ext):
            # Case #3 - field like <vg7:order_id>: both name and value are
            #           of counterpart refs
            is_foreign = True
            ext_name = ext_ref[len(pfx_ext):]
            if ext_name == ext_id_name and loc_ext_id_name:
                loc_name = loc_ext_id_name
            elif identity == 'odoo':
                if ext_odoo_ver:
                    loc_name = transodoo.translate_from_to(
                        tnldict, xmodel, ext_name,
                        ext_odoo_ver, release.major_version)
                else:
                    loc_name = ext_name
            else:
                loc_name = cache.get_model_field_attr(
                    channel_id, xmodel, ext_name, 'EXT_FIELDS', default='')
            if loc_name.startswith('.'):
                loc_name = ''
        else:
            # Case #4 - field and value are Odoo
            is_foreign = False
            if ext_ref.startswith(':'):
                ext_name = loc_name = ext_ref[1:]
            else:
                ext_name = loc_name = ext_ref
        return ext_name, loc_name, is_foreign

    def get_default_n_apply(self, channel_id, xmodel, loc_name, ext_name,
                            is_foreign, ttype=None):
        cache = self.env['ir.model.synchro.cache']
        identity = cache.get_attr(channel_id, 'IDENTITY')
        actual_model = self.get_actual_model(xmodel, only_name=True)
        if not cache.get_attr(channel_id, actual_model):
            cache.open(channel_id=channel_id, model=actual_model)
        default = cache.get_model_field_attr(
            channel_id, xmodel, loc_name or '.%s' % ext_name, 'APPLY',
            default='')
        if not default:
            default = cache.get_model_field_attr(
                channel_id, actual_model, loc_name or '.%s' % ext_name,
                'APPLY', default='')
        if default.endswith('()'):
            apply4 = 'odoo_migrate' if identity == 'odoo' else ''
            for fct in default.split(','):
                if not fct.startswith('not') or is_foreign:
                    apply4 = '%s,%s' % (apply4, 'apply_%s' % default[:-2])
            if apply4.startswith(','):
                apply4 = apply4[1:]
            default = False
        elif default:
            apply4 = 'apply_set_value'
        else:
            apply4 = 'odoo_migrate' if identity == 'odoo' else ''
        if ttype == 'boolean':
            default = os0.str2bool(default, True)
        spec = cache.get_model_field_attr(
            channel_id, xmodel, loc_name or '.%s' % ext_name, 'SPEC',
            default='')
        return default, apply4, spec

    def map_to_internal(self, channel_id, xmodel, vals, disable_post,
                        no_deep_fields=None):

        def rm_ext_value(vals, loc_name, ext_name, ext_ref, is_foreign):
            if (ext_ref in vals and
                    loc_name and loc_name not in vals and
                    (is_foreign or loc_name != ext_name or
                     (ext_ref.startswith(':')))):
                vals[loc_name] = vals[ext_ref]
            if ext_ref in vals and loc_name != ext_ref:
                del vals[ext_ref]
            return vals

        def do_apply(channel_id, vals, loc_name, ext_ref, loc_ext_id_name,
                     apply4, default, xmodel, ctx=None):
            ir_apply = self.env['ir.model.synchro.apply']
            src = ext_ref
            for fct in apply4.split(','):
                if fct == 'odoo_migrate':
                    ext_odoo_ver = self.get_ext_odoo_ver(ext_ref.split(':')[0])
                    tnldict = self.get_tnldict(channel_id)
                    if ext_odoo_ver:
                        vals[loc_name] = os0.u(transodoo.translate_from_to(
                            tnldict, xmodel, vals[ext_ref],
                            ext_odoo_ver, release.major_version,
                            type='value', fld_name=loc_name))
                    else:
                        vals[loc_name] = vals[ext_ref]
                    self.logmsg('debug',
                        '>>> %(loc)s=%(fct)s(%(name)s,%(src)s,%(xid)s,%(d)s)',
                        model=xmodel,
                        ctx={'loc': vals.get(loc_name), 'fct': fct,
                             'name': loc_name, 'src': src,
                             'xid': loc_ext_id_name, 'd': default})
                    src = loc_name
                elif hasattr(ir_apply, fct):
                    vals = getattr(ir_apply, fct)(channel_id,
                        vals,
                        loc_name,
                        src,
                        loc_ext_id_name,
                        default=default)
                    self.logmsg('debug',
                        '>>> %(loc)s=%(fct)s(%(name)s,%(src)s,%(xid)s,%(d)s)',
                        model=xmodel,
                        ctx={'loc': vals.get(loc_name), 'fct': fct,
                             'name': loc_name, 'src': src,
                             'xid': loc_ext_id_name, 'd': default})
                    src = loc_name
            return vals

        def do_apply_n_clean(channel_id, vals, loc_name, ext_name, ext_ref,
                             loc_ext_id_name, apply4, default, is_foreign,
                             xmodel, ctx=None):
            if ext_ref in vals and loc_name:
                vals = do_apply(channel_id, vals, loc_name, ext_ref,
                    loc_ext_id_name, apply4, default, xmodel, ctx=ctx)
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
                    self.logmsg('warning',
                        '### Field <%(nm)s> renamed as <%(new)s>',
                        ctx={'nm': nm, 'new': nm_id})
                elif (vals.get(nm_id) and vals.get(nm)):
                    self.logmsg('warning',
                        '### Field <%(nm)s> overtaken by <%(new)s>',
                        ctx={'nm': nm, 'new': nm_id})
                    del vals[nm]
            return vals

        self.logmsg('debug', '>>> %(model)s.map_to_internal()',
            model=xmodel)
        cache = self.env['ir.model.synchro.cache']
        actual_model = self.get_actual_model(xmodel, only_name=True)
        loc_ext_id_name = self.get_loc_ext_id_name(channel_id, xmodel)
        def_loc_ext_id_name = self.get_loc_ext_id_name(
            channel_id, xmodel, force=True)
        ext_id_name = cache.get_model_attr(
            channel_id, xmodel, 'KEY_ID', default='id')
        child_ids = cache.get_struct_model_attr(
            actual_model, 'CHILD_IDS', default=False)
        vals = check_4_double_field_id(vals)
        field_list = priority_fields(
            channel_id, vals, def_loc_ext_id_name, xmodel)
        ctx = cache.get_attr(channel_id, 'CTX')
        ctx['ext_key_id'] = ext_id_name
        ref_in_queue = False
        for ext_ref in field_list:
            self.logmsg('debug',
                '>>>   for "%(model)s.%(name)s" in field_list:',
                model=xmodel, ctx={'name': ext_ref})
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
                        channel_id, vals, loc_name, ext_ref, loc_ext_id_name,
                        apply4, default, xmodel, ctx=ctx)
                elif loc_name != def_loc_ext_id_name:
                    self.logmsg('warning',
                        '### Field <%(x)s> does not exist in model %(model)s',
                        model=xmodel,
                        ctx={'x': ext_ref})
                vals = rm_ext_value(vals, loc_name, ext_name, ext_ref,
                    is_foreign)
                continue
            elif ext_ref not in vals:
                if is_foreign and apply4:
                    vals = do_apply_n_clean(
                        channel_id, vals,
                        loc_name, ext_name, ext_ref, loc_ext_id_name,
                        apply4, default, is_foreign, xmodel, ctx=ctx)
                if loc_name in vals and not vals[loc_name]:
                    del vals[loc_name]
                continue
            elif (isinstance(vals[ext_ref], basestring) and
                  not vals[ext_ref].strip()):
                vals[ext_ref] = vals[ext_ref].strip()
                if is_foreign and apply4:
                    vals = do_apply_n_clean(
                        channel_id, vals,
                        loc_name, ext_name, ext_ref, loc_ext_id_name,
                        apply4, default, is_foreign, xmodel, ctx=ctx)
                continue
            elif not vals[ext_ref]:
                if is_foreign and apply4:
                    vals = do_apply_n_clean(
                        channel_id, vals,
                        loc_name, ext_name, ext_ref, loc_ext_id_name,
                        apply4, default, is_foreign, xmodel, ctx=ctx)
                continue
            if (cache.get_struct_model_field_attr(
                    actual_model, loc_name, 'ttype') in ('many2one',
                                                         'one2many',
                                                         'many2many',
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
                if loc_name == loc_ext_id_name:
                    vals[ext_ref] = self.get_loc_ext_id_value(
                        channel_id, xmodel, vals[ext_ref])
                    vals = rm_ext_value(vals, loc_name, ext_name, ext_ref,
                        is_foreign)
                    if xmodel == actual_model:
                        if cache.id_is_in_cache(
                                channel_id, xmodel, actual_model,
                                ext_id=vals[loc_name]):
                            ref_in_queue = True
                            self.logmsg('warning',
                                'Found %(model)s.%(id)s in queue!',
                                model=xmodel,
                                ctx={'id': vals[loc_name]})
                        else:
                            cache.push_id(channel_id, xmodel, actual_model,
                                ext_id=vals[loc_name])
                    continue
                # If counterpart partner supplies both
                # local and external values, just process local value
                elif loc_name in vals or loc_name == 'id':
                    del vals[ext_ref]
                    continue
            elif ext_ref == 'id':
                if xmodel == actual_model:
                    if cache.id_is_in_cache(
                            channel_id, xmodel, actual_model,
                            loc_id=vals[ext_ref]):
                        ref_in_queue = True
                        self.logmsg('warning',
                            'Found %(model)s.%(id)s in queue!',
                            model=xmodel,
                            ctx={'id': vals[ext_ref]})
                    else:
                        cache.push_id(channel_id, xmodel, actual_model,
                            loc_id=vals[ext_ref])
                continue
            if cache.get_struct_model_field_attr(
                    actual_model, loc_name, 'ttype') in (
                    'many2one', 'one2many', 'many2many'):
                if (isinstance(no_deep_fields, (list, tuple)) and
                        len(no_deep_fields) and
                        '*' in no_deep_fields):
                    condition = 'include'
                else:
                    condition = 'exclude'
                if (ref_in_queue or (
                        condition == 'include' and
                        loc_name not in no_deep_fields) or (
                        condition == 'exclude' and
                        loc_name in no_deep_fields)):
                    if (loc_name in vals and (
                            not vals[loc_name] or
                            (isinstance(vals[loc_name], basestring) and
                             not vals[loc_name].isdigit()))):
                        del vals[loc_name]
                    del vals[ext_ref]
                else:
                    vals = do_apply(channel_id, vals, ext_ref, ext_ref,
                        loc_ext_id_name, apply4, default, xmodel, ctx=ctx)
                    loc_id = self.get_foreign_value(
                        channel_id, xmodel, vals[ext_ref], loc_name, is_foreign,
                        ctx=ctx,
                        ttype=cache.get_struct_model_field_attr(
                            actual_model, loc_name, 'ttype'),
                        spec=spec, fmt='cmd')
                    if loc_id:
                        if isinstance(loc_id, (tuple, list)):
                            vals[loc_name] = loc_id
                        elif loc_id > 0:
                            vals[loc_name] = loc_id
                    elif loc_name:
                        vals[loc_name] = False
                    vals = rm_ext_value(vals, loc_name, ext_name, ext_ref,
                        is_foreign)
            # elif identity == 'odoo':
            #     tnldict = self.get_tnldict(channel_id)
            #     vals[loc_name] = transodoo.translate_from_to(
            #         tnldict, xmodel, vals[ext_ref],
            #         ext_odoo_ver, release.major_version,
            #         type='value', fld_name=loc_name)
            #     if isinstance(vals[loc_name], list):
            #         del vals[ext_ref]
            #         del vals[loc_name]
            else:
                vals = do_apply_n_clean(
                    channel_id, vals,
                    loc_name, ext_name, ext_ref, loc_ext_id_name,
                    apply4, default, is_foreign, xmodel, ctx=ctx)
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
        if 'ext_key_id' in ctx:
            del ctx['ext_key_id']
        cache.set_attr(channel_id, 'CTX', ctx)
        return vals, ref_in_queue

    def set_default_values(self, cls, channel_id, xmodel, vals):
        actual_model = self.get_actual_model(xmodel, only_name=True)
        ir_apply = self.env['ir.model.synchro.apply']
        cache = self.env['ir.model.synchro.cache']
        loc_ext_id_name = self.get_loc_ext_id_name(channel_id, xmodel)
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
                                    loc_ext_id_name,
                                    default=default,
                                    ctx=cache.get_attr(channel_id, 'CTX'))
                                self.logmsg('debug',
                                    '>>> %(loc)s=%(fct)s(%(name)s,%(src)s,'
                                    '%(xid)s,%(d)s)',
                                    model=xmodel,
                                    ctx={'loc': vals.get(loc_name), 'fct': fct,
                                         'name': loc_name, 'src': src,
                                         'xid': loc_ext_id_name,
                                         'd': default})
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

        self.logmsg('debug', '>>> %(model)s.bind_record(%(x)s)',
            model=xmodel, ctx={'x': constraints})
        ctx = ctx or {}
        actual_model = self.get_actual_model(xmodel, only_name=True)
        spec = self.get_spec_from_xmodel(xmodel)
        spec = spec if spec != 'supplier' else ''
        if actual_model == 'res.partner' and spec in ('delivery', 'invoice'):
            ctx['type'] = spec
        cache = self.env['ir.model.synchro.cache']
        def_loc_ext_id_name = self.get_loc_ext_id_name(
            channel_id, xmodel, force=True)
        loc_ext_id_name = self.get_loc_ext_id_name(channel_id, xmodel)
        if loc_ext_id_name:
            use_sync = cache.get_struct_model_attr(
                actual_model, loc_ext_id_name)
        else:
            use_sync = False
        rec = False
        candidate = False
        if ((loc_ext_id_name in vals and use_sync) or
                (loc_ext_id_name != def_loc_ext_id_name and
                def_loc_ext_id_name in vals)):
            domain = [
                (def_loc_ext_id_name, '=', self.get_loc_ext_id_value(
                    channel_id, xmodel, vals[def_loc_ext_id_name]))]
            rec, maybe_dif = self.do_search(actual_model, domain, only_id=True)
            if len(rec) > 1:
                self.logmsg('warning',
                    '### WRONG INDEX %(model)s.%(id)s',
                    model=actual_model,
                    ctx={'id': loc_ext_id_name})
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
                    if loc_ext_id_name and loc_ext_id_name in vals and use_sync:
                        domain.append('|')
                        domain.append((loc_ext_id_name, '=', False))
                        domain.append((loc_ext_id_name, '=', 0))
                    rec, maybe_dif = self.do_search(
                        actual_model, domain, spec=spec)
                    if rec:
                        break
                    if maybe_dif and not candidate:
                        candidate = rec
        if not rec and candidate:
            rec = candidate
        if rec:
            if len(rec) > 1:
                self.logmsg('warning',
                    '### synchro error: multiple %(model)s.%(id)s',
                    model=actual_model, rec=rec[0])
                return rec[0].id, rec[0]
            else:
                self.logmsg('info',
                    '>>> %(id)s=%(model)s.bind_record()',
                    model=actual_model, rec=rec)
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
                self.logmsg('error',
                    'Channel %(chid)s without connection parameters!',
                    ctx={'chid': channel_id})
                return False, False, tnldict
            cnx, session = xml_login(
                xml_connect(endpoint, protocol=prot, port=port),
                endpoint,
                db=db,
                login=login,
                passwd=passwd)
            if not cnx:
                self.logmsg('warning',
                    'Not response from %(ep)s', ctx={'ep': endpoint})
            elif not session:
                self.logmsg('warning',
                    'Login response error (%(db)s,%(login)s,%(pwd)s)',
                    ctx={'db': db, 'login': login, 'pwd': passwd})
            return cnx, session, tnldict

        def expand_many(rec, ext_field, vals):
            try:
                vals[ext_field] = [x.id for x in rec[ext_field]]
            except BaseException:
                if ext_field in vals:
                    del vals[ext_field]
            return vals

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
                    if ext_odoo_ver:
                        ext_field = transodoo.translate_from_to(
                            tnldict, actual_model, field,
                            release.major_version, ext_odoo_ver)
                    else:
                        ext_field = field
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
                            except BaseException:
                                vals[ext_field] = rec[ext_field]
                        elif cache.get_struct_model_field_attr(
                                actual_model, field, 'ttype') in (
                                'one2many', 'many2many'):
                            vals = expand_many(rec, ext_field, vals)
                        elif isinstance(rec[ext_field], basestring):
                            vals[ext_field] = rec[ext_field].encode(
                                'utf-8').decode('utf-8')
                        else:
                            vals[ext_field] = rec[ext_field]
                if vals:
                    vals['id'] = ext_id
            return vals

        self.logmsg('debug',
            '>>> %(model)s.get_xmlrpc_response(ch=%(chid)s,%(xid)s,%(sel)s):',
            model=xmodel,
            ctx={'chid': channel_id, 'xid': ext_id, 'sel': select})
        cache = self.env['ir.model.synchro.cache']
        cnx, session, tnldict = rpc_session()
        # prefix = cache.get_attr(channel_id, 'PREFIX')
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

        def sort_data(datas):
            # Single record
            if 'id' in datas:
                return datas
            ixs = {}
            for item in datas:
                if isinstance(item, dict):
                    id = item.get('id')
                    if not id:
                        return datas
                    ixs[int(id)] = item
            datas = []
            for id in sorted(ixs.keys()):
                datas.append(ixs[id])
            return datas

        self.logmsg('debug',
            '>>> %(model)s.get_json_response(%(chid)s,%(xid)s):',
            model=xmodel, ctx={'chid': channel_id, 'xid': ext_id})
        cache = self.env['ir.model.synchro.cache']
        endpoint = cache.get_attr(channel_id, 'COUNTERPART_URL')
        if not endpoint:
            self.logmsg('error',
                'Channel %(chid)s without connection parameters!',
                ctx={'chid': channel_id})
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
        self.logmsg('info',
            '>>> %(model)s.vg7_requests(%(url)s,%(hdr)s):',
            model=xmodel, ctx={'url': url, 'hdr': headers})
        try:
            response = requests.get(url, headers=headers, verify=False)
        except BaseException:
            response = False
        if response:
            datas = sort_data(response.json())
            return datas
        self.logmsg('warning',
            'Response error %(sts)s (%(chid)s,%(url)s,%(key)s,%(pfx)s)',
            model=xmodel, ctx={
                'sts': getattr(response, 'status_code', 'N/A'),
                'chid': channel_id,
                'url': url,
                'key': cache.get_attr(channel_id, 'CLIENT_KEY'),
                'pfx': cache.get_attr(channel_id, 'PREFIX'),
            })
        cache.clean_cache(channel_id=channel_id, model=xmodel)
        return {}

    def get_csv_response(self, channel_id, xmodel, ext_id=False, mode=None):
        self.logmsg('debug',
            '>>> %(model)s.get_csv_response(%(chid)s,%(xid)s):',
            model=xmodel, ctx={'chid': channel_id, 'xid': ext_id})
        cache = self.env['ir.model.synchro.cache']
        endpoint = cache.get_attr(channel_id, 'EXCHANGE_PATH')
        if not endpoint:
            self.logmsg('error',
                'Channel %(chid)s without connection parameters!',
                ctx={'chid': channel_id})
            return False
        ext_model = cache.get_model_attr(channel_id, xmodel, 'BIND')
        ext_id_name = cache.get_model_attr(
            channel_id, xmodel, 'KEY_ID', default='id')
        if not ext_model:
            _logger.error('Model %s not managed by external partner!' % xmodel)
            return False
        file_csv = os.path.expanduser(
            os.path.join(endpoint, ext_model + '.csv'))
        self.logmsg('info',
            '>>> %(model)s.csv_requests(%(csv)s)',
            model=xmodel, ctx={'csv': file_csv})
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
                row_res = {ext_id_name: row_id}
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
                    if hdr[ix] == ext_id_name:
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
                if ext_id and row_res[ext_id_name] != ext_id:
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

    def create_ext_id(self, channel_id, actual_model, loc_id, ext_id):
        ext_id_name = self.get_loc_ext_id_name(
            channel_id, actual_model, force=True)
        self.env['ir.model.synchro.data'].create({
            'model': actual_model,
            'ext_id_name': ext_id_name,
            'ext_id': ext_id,
            'res_id': loc_id,
        })

    def assign_channel(self, vals, model=None, ext_model=None):
        cache = self.env['ir.model.synchro.cache']
        odoo_prio = 9999
        channel_prio = 9999
        odoo_channel = def_channel = channel_from = False
        channel_ctr = 0
        if not len(cache.get_channel_list()):
            cache.setup_channels(all=True)
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
#            return self.assign_channel(vals)
        if not channel_from:
            if channel_prio < odoo_prio:
                channel_from = def_channel
            else:
                channel_from = odoo_channel
        return channel_from

    @api.model
    def synchro_childs(
            self, channel_id, xmodel, actual_model, parent_id, ext_id,
            only_minimal=None):
        self.logmsg('debug',
            '>>> %(model)s.synchro_childs(%(chid)s,%(cmodel)s,%(id)s,%(xid)s)',
            model=xmodel, ctx={'chid': channel_id, 'cmodel': actual_model,
                               'id': parent_id, 'xid': ext_id})
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
        ext_id_name = cache.get_model_attr(
            channel_id, model_child, '', default='id')
        for item in rec_ids:
            if isinstance(item, (int, long)):
                vals = self.get_counterpart_response(
                    channel_id, model_child, ext_id=item)
                if ext_id_name not in vals:
                    self.logmsg('debug',
                        'Model %(model)s data received w/o id',
                        model=model_child)
                    continue
            else:
                vals = item
                vals[':%s' % parent_id_name] = parent_id
            try:
                id = self.generic_synchro(cls,
                    vals,
                    channel_id=channel_id,
                    jacket=True,
                    only_minimal=only_minimal)
                if id < 0:
                    self.logmsg('info', 'Error pulling from %(model)s.%(id)s',
                        model=model_child, ctx={'id': item})
                    return id
                # commit every table to avoid too big transaction
                self.env.cr.commit()  # pylint: disable=invalid-commit
            except BaseException, e:
                self.env.cr.rollback()  # pylint: disable=invalid-commit
                self.logmsg('warning',
                    'Error %(e) pulling from %(model)s.%(id)s',
                    model=model_child, ctx={'e': e, 'id': item})
                return -1
        self.commit(self.env[actual_model], parent_id)
        return ext_id

    @api.model
    def synchro(self, cls, vals, disable_post=None, no_deep_fields=None,
                only_minimal=None):

        def pop_ref(channel_id, xmodel, actual_model, id, ext_id):
            cache.pop_id(channel_id, xmodel, actual_model,
                loc_id=id, ext_id=ext_id)

        def protect_against_vg7(xmodel, actual_model, vals):
            # Protect against VG7 mistakes
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
            if xmodel == 'res.partner' and vals.get('type'):
                xmodel = self.get_xmodel(actual_model, vals['type'])
                cache.open(model=xmodel)
            return xmodel, vals

        def browse_from_id(actual_cls, vals):
            id = 0
            rec = None
            if 'id' in vals:
                id = vals.pop('id')
                rec = actual_cls.search([('id', '=', id)])
                if not rec or rec.id != id:
                    _logger.error('!-3! ID %s does not exist in %s' %
                                  (id, xmodel))
                    pop_ref(channel_id, xmodel, actual_model, id, ext_id)
                    return -3, None
                id = rec.id
                self.logmsg('debug',
                    '### synchro: found id=%(model)s.%(id)s',
                    model=actual_model, rec=rec)
            return id, rec

        vals = unicodes(vals)
        saved_vals = vals.copy()
        xmodel = cls.__class__.__name__
        self.logmsg('info', '>>> %(model)s.synchro(%(vals)s,%(x)s)',
            model=xmodel, ctx={'vals': vals, 'x': disable_post})
        actual_model = self.get_actual_model(xmodel, only_name=True)
        actual_cls = self.get_actual_model(xmodel)
        cache = self.env['ir.model.synchro.cache']
        cache.open(model=xmodel, cls=cls)
        channel_id = self.assign_channel(vals)
        identity = cache.get_attr(channel_id, 'IDENTITY')
        no_deep_fields = no_deep_fields or []
        if identity != 'vg7':
            self.DEF_INCL_FLDS = list(
                set(self.DEF_INCL_FLDS) | set(['company_id']))
        else:
            self.DEF_INCL_FLDS = list(
                set(self.DEF_INCL_FLDS) - set(['company_id']))
        if '*' in no_deep_fields:
            no_deep_fields = list(
                set(no_deep_fields) - set(self.DEF_EXCL_FLDS))
            no_deep_fields = list(
                set(no_deep_fields) | set(self.DEF_INCL_FLDS))
        else:
            no_deep_fields = list(
                set(no_deep_fields) | set(self.DEF_EXCL_FLDS))
            no_deep_fields = list(
                set(no_deep_fields) - set(self.DEF_INCL_FLDS))
        if not channel_id:
            cache.clean_cache()
            _logger.error('!-6! No channel found!')
            return -6
        self.logmsg('debug', '### assigned channel is %s' % channel_id)

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
        if cache.get_attr(channel_id, 'IDENTITY') == 'vg7':
            xmodel, vals = protect_against_vg7(xmodel, actual_model, vals)
        cache.open(channel_id=channel_id, ext_model=xmodel)
        spec = ''
        if xmodel == actual_model:
            if hasattr(cls, 'preprocess'):
                vals, spec = cls.preprocess(channel_id, vals)
            elif do_auto_process:
                vals, spec = self.preprocess(channel_id, xmodel, vals)
            if spec:
                xmodel = self.get_xmodel(actual_model, spec)
                actual_model = self.get_actual_model(xmodel)
                cache.open(model=xmodel)
            self.logmsg('debug',
                '>>> %(vals)s,"%(spec)s"=%(model)s.preprocess()',
                model=xmodel, ctx={'vals': vals, 'spec': spec})
        vals, ref_in_queue = self.map_to_internal(
            channel_id, xmodel, vals, disable_post,
            no_deep_fields=no_deep_fields)
        if xmodel == 'ir.module.module':
            return self.manage_module(vals)
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

        def_ext_id_name = self.get_loc_ext_id_name(
            channel_id, xmodel, force=True)
        ext_id = vals.get(def_ext_id_name)
        ext_id_name = self.get_loc_ext_id_name(channel_id, xmodel)
        self.logmsg('debug',
            '>>> child: mode="%s" ids=%s model="%s"' % (
                parent_child_mode, child_ids, model_child))
        loc_id, rec = browse_from_id(actual_cls, vals)
        if loc_id < 0:
            return loc_id
        elif loc_id == 0:
            loc_id, rec = self.bind_record(
                channel_id, xmodel, vals, constraints)
        if ref_in_queue:
            pop_ref(channel_id, xmodel, actual_model, loc_id, ext_id)
            self.logmsg('info',
                '>>> %s.browse(ext_id=%s)  # Record found in cache' % (
                    actual_model, ext_id))
            return loc_id
        if has_state:
            vals, erc = self.set_state_to_draft(xmodel, rec, vals)
            if erc < 0:
                _logger.error('!%s! Returned error code!' % erc)
                pop_ref(channel_id, xmodel, actual_model, loc_id, ext_id)
                return erc
            # TODO: Workaround
            if xmodel == 'stock.picking.package.preparation':
                loc_id = -1
        elif has_2delete:
            vals['to_delete'] = False
        if def_ext_id_name in vals and def_ext_id_name != ext_id_name:
            tmp = vals[def_ext_id_name]
            self.drop_invalid_fields(xmodel, vals)
            vals[def_ext_id_name] = tmp
        else:
            self.drop_invalid_fields(xmodel, vals)
        do_write = True
        if loc_id > 0 and parent_child_mode == 'C':
            parent_child_mode = 'B'
            cache.set_model_attr(channel_id, xmodel,
                '__%s_ids' % actual_model,
                vals[child_ids])
            del vals[child_ids]
        if loc_id < 1:
            if (has_state or has_2delete or not ext_id or
                    parent_child_mode == 'C'):
                min_vals = vals
                do_write = False
                vals = self.set_default_values(cls, channel_id, xmodel, vals)
            else:
                vals = self.set_default_values(cls, channel_id, xmodel, vals)
                min_vals = {def_ext_id_name: ext_id} if vals.get(
                    def_ext_id_name) else {}
                for nm in self.DEF_INCL_FLDS:
                    if vals.get(nm):
                        min_vals[nm] = vals[nm]
                min_vals = self.set_default_values(
                    cls, channel_id, xmodel, min_vals)
                if not min_vals or min_vals == vals:
                    do_write = False
                    min_vals = vals
                else:
                    do_write = True
            if vals:
                if hasattr(actual_cls, 'assure_values'):
                    vals = actual_cls.assure_values(vals, rec)
                if actual_model == 'account.payment.term':
                    vals[child_ids] = {'sequence': 1, 'value': 'balance'}
                try:
                    rec = actual_cls.create(min_vals)
                    loc_id = rec.id
                except BaseException, e:
                    self.env.cr.rollback()  # pylint: disable=invalid-commit
                    self.logmsg('warning',
                        '>>> %s.min_create()  # %s' % (
                            actual_model, e))
                if loc_id < 1 and min_vals != vals:
                    try:
                        min_vals = vals
                        rec = actual_cls.create(vals)
                    except BaseException, e:
                        self.env.cr.rollback()  # pylint: disable=invalid-commit
                        self.logmsg('error', '!-1! %(e)s\nvalues=%(val)s',
                            model=xmodel, ctx={'e': e, 'val': saved_vals})
                        pop_ref(channel_id, xmodel, actual_model, loc_id, ext_id)
                        return -1
                if not ext_id_name:
                    self.create_ext_id(
                        channel_id, actual_model, loc_id, ext_id)
                if only_minimal:
                    do_write = False
                if not do_write and min_vals != vals:
                    self.logmsg('info',
                        '>>> %s=%s.min_create(%s)' % (
                            loc_id, actual_model, min_vals))
                else:
                    self.logmsg('info',
                        '>>> %s=%s.create(%s)' % (loc_id, actual_model, vals))
        if loc_id > 0 and do_write:
            if def_ext_id_name in vals and def_ext_id_name != ext_id_name:
                del vals[def_ext_id_name]
            try:
                rec = actual_cls.with_context(
                    {'lang': self.env.user.lang}).browse(loc_id)
            except BaseException, e:
                self.env.cr.rollback()  # pylint: disable=invalid-commit
                self.logmsg('error', '!-3! %(e)s\nvalues=%(val)s',
                    model=xmodel, ctx={'e': e, 'val': saved_vals})
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
                        self.logmsg('info',
                            '>>> synchro: %s.write(%s)' % (
                                actual_model, vals))
                        self.logmsg('trace', '', model=actual_model, rec=rec)
                    except BaseException, e:
                        self.env.cr.rollback()  # pylint: disable=invalid-commit
                        self.logmsg('error', '!-2! %(e)s\nvalues=%(val)s',
                            model=xmodel, ctx={'e': e, 'val': saved_vals})
                        pop_ref(channel_id, xmodel, actual_model, loc_id, ext_id)
                        return -2
                elif do_write:
                    self.logmsg('debug',
                        '### Nothing to update(%s.%s)' % (
                            actual_model, loc_id))
                    self.logmsg('trace', '', model=actual_model, rec=rec)
                if (do_write and
                        rec and child_ids and
                        hasattr(rec, child_ids)):
                    for num, line in enumerate(rec[child_ids]):
                        self.logmsg('debug',
                            '>>>   for %(n)s,"%(line)s" in '
                            'enumerate(rec.%(ids)s)',
                            ctx={'n': num, 'line': line, 'ids': child_ids})
                        seq = num + 1
                        if not hasattr(line, 'to_delete'):
                            child_vals = {}
                        else:
                            child_vals = {'to_delete': True}
                        if actual_model == 'account.payment.term':
                            child_vals['sequence'] = seq
                        if child_vals:
                            try:
                                line.write(child_vals)
                                self.logmsg('debug',
                                            '>>> line.write(%(vals))',
                                            ctx={'vals': child_vals})
                            except BaseException:
                                self.env.cr.rollback()  # pylint: disable=invalid-commit
                                self.logmsg('error',
                                    '!-2! %(e)s\nvalues=%(val)s',
                                    model=xmodel,
                                    ctx={'e': e, 'val': child_vals})

        # commit to avoid lost data in recursive write
        self.env.cr.commit()  # pylint: disable=invalid-commit
        done_post = False
        if loc_id > 0 and not disable_post and xmodel == actual_model:
            if actual_model == 'res.lang':
                self.manage_language(rec)
            elif hasattr(cls, 'postprocess'):
                done_post = cls.postprocess(channel_id, loc_id, vals)
            elif do_auto_process:
                done_post = self.postprocess(channel_id, xmodel, loc_id, vals)
            self.synchro_queue(channel_id)
        if parent_child_mode in ('A', 'B') and not done_post:
            sts = self.synchro_childs(
                channel_id, xmodel, actual_model, loc_id, ext_id,
                only_minimal=only_minimal)
            if sts < 1:
                pop_ref(channel_id, xmodel, actual_model, loc_id, ext_id)
                return sts - 100
        elif model_child:
            self.logmsg('debug',
                '### No child mode: counterpart must send child records')
        pop_ref(channel_id, xmodel, actual_model, loc_id, ext_id)
        _logger.info('!%s! Returned ID of %s' % (loc_id, xmodel))
        return loc_id

    @api.model
    def commit(self, cls, loc_id, ext_id=None):
        xmodel = cls.__class__.__name__
        actual_model = self.get_actual_model(xmodel, only_name=True)
        self.logmsg('info', '>>> %(model)s.commit(%(id)s,%(x)s)',
            model=xmodel, ctx={'id': loc_id, 'x': ext_id})
        cache = self.env['ir.model.synchro.cache']
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
                [], False, )
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
    def generic_synchro(self, cls, vals, jacket=None, disable_post=None,
                        channel_id=None,
                        only_minimal=None, no_deep_fields=None):
        self.logmsg('debug', '>>> %(model)s.generic_synchro(%(j)s,%(d)s)',
            model=cls.__class__.__name__, ctx={'j': jacket, 'd': disable_post})
        cache = self.env['ir.model.synchro.cache']
        if hasattr(cls, 'synchro'):
            if jacket:
                return cls.synchro(self.jacket_vals(
                    cache.get_attr(channel_id, 'PREFIX'),
                    vals), disable_post=disable_post,
                    only_minimal=only_minimal, no_deep_fields=no_deep_fields)
            else:
                return cls.synchro(vals, disable_post=disable_post,
                    only_minimal=only_minimal, no_deep_fields=no_deep_fields)
        else:
            if jacket:
                return self.synchro(cls, self.jacket_vals(
                    cache.get_attr(channel_id, 'PREFIX'),
                    vals), disable_post=disable_post,
                    only_minimal=only_minimal, no_deep_fields=no_deep_fields)
            else:
                return self.synchro(cls, vals, disable_post=disable_post,
                    only_minimal=only_minimal, no_deep_fields=no_deep_fields)

    @api.model
    def jacket_vals(self, prefix, vals):
        self.logmsg('debug', '>>> jacket_vals(%(pfx)s,%(vals)s)',
            ctx={'pfx': prefix, 'vals': vals})
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
        self.logmsg('debug', '>>> %(model)s.preprocess()', model=xmodel)
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
            elif (loc_name in self.DEF_INCL_FLDS or
                  cache.get_struct_model_field_attr(
                      actual_model, loc_name, 'required') or
                  not cache.get_struct_model_field_attr(
                      actual_model, loc_name, 'ttype') in (
                          'many2one', 'one2many', 'many2many')):
                min_vals[ext_ref] = vals[ext_ref]
        if (ext_id and loc_ext_id and
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
        self.logmsg('debug', '>>> %(model)s.postprocess(%(id)s)',
            model=model, ctx={'id': parent_id})
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
        self.logmsg('info', '>>> synchro_queue()')
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
                self.logmsg('warning',
                    '### invalid queue(%s,%s)?' % (xmodel, loc_id))
                return
            self.logmsg('info', '>>> queued_pull(%s,%s)?' % (xmodel, loc_id))
            rec = self.get_actual_model(xmodel).browse(loc_id)
            loc_ext_id_name = self.get_loc_ext_id_name(channel_id, xmodel)
            if loc_ext_id_name and hasattr(rec, loc_ext_id_name):
                self.pull_1_record(
                    channel_id, xmodel, getattr(rec, loc_ext_id_name))

    @api.model
    def vals_or_id(self, item, ext_key_id):
        if isinstance(item, (int, long)):
            vals = {}
            ext_id = item
        else:
            vals = item
            if isinstance(vals, (list, tuple)):
                vals = vals[0]
            if ext_key_id in vals:
                if isinstance(vals[ext_key_id], (int, long)):
                    ext_id = vals[ext_key_id]
                else:
                    ext_id = int(vals[ext_key_id])
            else:
                ext_id = False
        return ext_id, vals

    @api.multi
    def pull_recs_2_complete(self, only_model=None):
        """Delete records does not exist on counterpart"""

        def get_ext_id(ext_ix, datas):
            if ext_ix < -1:
                return -1, -2
            ext_ix += 1
            if ext_ix < len(datas):
                if isinstance(datas[ext_ix], (int, long)):
                    ext_id = int(datas[ext_ix])
                else:
                    ext_id = int(datas[ext_ix]['id'])
            else:
                ext_id = -1
                ext_ix = -2
            return ext_id, ext_ix

        def get_loc_id(loc_ix, recs, loc_ext_id, channel_id):
            if loc_ix < -1:
                return -1, -2
            loc_ix += 1
            if loc_ext_id and loc_ix < len(recs):
                if isinstance(recs[loc_ix], (int, long)):
                    loc_id = recs[loc_ix]
                else:
                    loc_id = recs[loc_ix][loc_ext_id]
                loc_id = self.get_actual_ext_id_value(
                    channel_id, xmodel, loc_id)
            else:
                loc_id = -1
                loc_ix = -2
            return loc_id, loc_ix

        self.logmsg('info', '>>> pull_recs_2_complete(%(x)s)',
            ctx={'x': only_model})
        cache = self.env['ir.model.synchro.cache']
        cache.open()
        cache.setup_channels(all=True)
        for channel_id in cache.get_channel_list().copy():
            if (not cache.get_attr(channel_id, 'COUNTERPART_URL') and
                    not cache.get_attr(channel_id, 'EXCHANGE_PATH')):
                continue
            identity = cache.get_attr(channel_id, 'IDENTITY')
            if identity == 'odoo':
                model_list = self.env[
                    'ir.model.synchro.cache'].TABLE_DEF.keys()
            else:
                domain = [('synchro_channel_id', '=', channel_id)]
                model_list = [x.name for x in self.env[
                    'synchro.channel.model'].search(domain,
                    order='sequence')]
            ctr = 0
            for xmodel in model_list:
                if not cache.is_struct(xmodel):
                    continue
                cache.open(model=xmodel)
                if (identity != 'odoo' and
                        not cache.get_model_attr(channel_id, xmodel, 'BIND')):
                    continue
                loc_ext_id_name = self.get_loc_ext_id_name(channel_id, xmodel)
                actual_model = self.get_actual_model(xmodel, only_name=True)
                self.logmsg('info', '### Checking %s for unlink' % xmodel)
                cls = self.env[xmodel]
                datas = self.get_counterpart_response(
                    channel_id, xmodel)
                if not datas:
                    continue
                if not isinstance(datas, (list, tuple)):
                    datas = [datas]
                if len(datas) and isinstance(datas[0], (int, long)):
                    datas.sort()
                if loc_ext_id_name:
                    recs = cls.search([(loc_ext_id_name, '!=', False)],
                        order=loc_ext_id_name)
                else:
                    recs = []
                ext_ix = -1
                loc_ix = -1
                ext_id, ext_ix = get_ext_id(ext_ix, datas)
                loc_id, loc_ix = get_loc_id(
                    loc_ix, recs, loc_ext_id_name, channel_id)
                while ext_id > 0 and loc_id > 0:
                    if ((loc_id > 0 and 0 < ext_id < loc_id) or
                            (loc_id < 0 and ext_id > 0) or
                            (cache.get_struct_model_attr(
                                actual_model, 'MODEL_WITH_NAME') and
                             recs[loc_ix].name.startswith('Unknown'))):
                        if (identity == 'odoo' or
                                cache.get_model_attr(
                                    channel_id, xmodel, '2PULL',
                                    default=False)):
                            if isinstance(datas[ext_ix], (int, long)):
                                vals = self.get_counterpart_response(
                                    channel_id, xmodel, id=ext_id)
                            else:
                                vals = datas[ext_ix]
                            if not vals:
                                continue
                            self.generic_synchro(cls, vals,
                                jacket=True,
                                channel_id=channel_id)
                            self.env.cr.commit()  # pylint: disable=invalid-commit
                        ext_id, ext_ix = get_ext_id(ext_ix, datas)
                    elif ((ext_id > 0 and 0 < loc_id < ext_id) or
                          loc_id > 0 and ext_id < 0):
                        if isinstance(recs[ext_ix], (int, long)):
                            rec = cls.browse(loc_id)
                        else:
                            rec = recs[loc_ix]
                        if loc_ext_id_name:
                            rec.write({loc_ext_id_name: False})
                        try:
                            id = rec.id
                            rec.unlink()
                            ctr += 1
                            self.env.cr.commit()  # pylint: disable=invalid-commit
                            self.logmsg('warning',
                                '### Deleted record %s.%d ext=%d' % (
                                    xmodel, id, loc_id))
                        except BaseException, e:
                            self.env.cr.rollback()  # pylint: disable=invalid-commit
                            self.logmsg('error', '!-2! %(e)s',
                                model=xmodel, ctx={'e': e})

                        loc_id, loc_ix = get_loc_id(
                            loc_ix, recs, loc_ext_id_name, channel_id)
                    else:
                        ext_id, ext_ix = get_ext_id(ext_ix, datas)
                        loc_id, loc_ix = get_loc_id(
                            loc_ix, recs, loc_ext_id_name, channel_id)
            _logger.info('%s record successfully unlinked from channel %s' % (
                ctr, channel_id))

    @api.multi
    def pull_full_records(self, force=None, only_model=None,
                          only_complete=None, select=None,
                          only_minimal=None, no_deep_fields=None,
                          remote_ids=None):
        """Called by import wizard
        @only_complete: import only records which name starting with 'Unknown'
        """
        def evaluate_remote_ids(rec_ids):
            remote_ids = rec_ids
            if isinstance(rec_ids, basestring):
                remote_ids = []
                for item in rec_ids.replace(
                        '[', '').replace(']', '').replace(
                        ',', ' ').replace('  ', ' ').split(' '):
                    if item.isdigit():
                        remote_ids.append(eval(item))
                    else:
                        if item.find('-') < 0:
                            continue
                        items = item.split('-')
                        if not items[0].isdigit():
                            if not items[1].isdigit():
                                items[0] = 1
                            else:
                                items[0] = int(items[1]) - 100
                                if items[0] < 1:
                                    item[0] = 1
                        if not items[1].isdigit():
                            items[1] = int(items[0]) + 100
                        item = 'range(%d,%d)' % (int(items[0]),
                                                 int(items[1]) + 1)
                        remote_ids += eval(item)
            return remote_ids

        def update_rec_counter(cur_channel, ext_id, rec_counter, use_workflow,
                               model=None):
            if ext_id > rec_counter:
                rec_counter = ext_id
                if use_workflow:
                    wkf = {'rec_counter': rec_counter}
                    if model:
                        wkf['workflow_model'] = model
                    cur_channel.write(wkf)
            return rec_counter

        self.logmsg('debug',
            '>>> pull_full_records(f=%(f)s,o=%(x)s,sel=%(sel)s)',
            ctx={'f': force, 'x': only_model, 'sel': select})
        use_workflow = False
        if not select:
            if force:
                select = 'all'
                use_workflow = True
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
            rec_counter = 0
            cur_channel = None
            if use_workflow:
                cur_channel = self.env['synchro.channel'].browse(channel_id)
                workflow = cur_channel.import_workflow
                rec_counter = cur_channel.rec_counter
                if workflow not in WORKFLOW:
                    return []
                model_list = [WORKFLOW[workflow]['model']]
                select = WORKFLOW[workflow].get('select', 'all')
                only_minimal = WORKFLOW[workflow].get(
                    'only_minimal', False)
                no_deep_fields = WORKFLOW[workflow].get('no_deep_fields', [])
                remote_ids = WORKFLOW[workflow].get('remote_ids')
                if not remote_ids:
                    remote_ids = '%s-' % (rec_counter + 1)
                self.logmsg('debug',
                    '>>> use_workflow(w=%(w)s,o=%(o)s,nodeep=%(n)s,r=%(r)s)',
                    ctx={'w': workflow, 'o': only_minimal,
                         'n': no_deep_fields, 'r': remote_ids})
            elif identity == 'odoo':
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
                    self.logmsg('info',
                        '### Model %s not pullable' % xmodel)
                    continue
                cls = self.env[xmodel]
                if remote_ids:
                    datas = evaluate_remote_ids(remote_ids)
                else:
                    datas = self.get_counterpart_response(
                        channel_id, xmodel)
                self.logmsg('info',
                    '### Pulling %(model)s(%(d)s)', model=xmodel,
                    ctx={'d': datas})
                if not datas:
                    continue
                if not isinstance(datas, (list, tuple)):
                    datas = [datas]
                if len(datas) and isinstance(datas[0], (int, long)):
                    datas.sort()
                ext_id_name = cache.get_model_attr(
                    channel_id, xmodel, '', default='id')
                ext_id_name = self.get_loc_ext_id_name(channel_id,
                    xmodel)
                for item in datas:
                    if not item:
                        continue
                    ext_id, vals = self.vals_or_id(item, ext_id_name)
                    if ext_id:
                        if ((select == 'new' and ext_id_name and
                             cls.search([(ext_id_name, '=', ext_id)])) or
                                (select == 'upd' and ext_id_name and
                                 not cls.search([(ext_id_name, '=', ext_id)]))):
                            rec_counter = update_rec_counter(
                                cur_channel, ext_id, rec_counter, use_workflow,
                                model=xmodel)
                            continue
                        if use_workflow and ext_id <= rec_counter:
                            continue
                        rec_counter = update_rec_counter(
                            cur_channel, ext_id, rec_counter, use_workflow,
                            model=xmodel)
                    loc_id = self.pull_1_record(
                        channel_id, xmodel, vals or ext_id,
                        only_minimal=only_minimal,
                        no_deep_fields=no_deep_fields)
                    self.logmsg('debug',
                        'WORKFLOW>>> self.pull_1_record('
                        'ch=%s,%s,%s,min=%s,nodeep=%s)' % (
                            channel_id, xmodel, vals or ext_id,
                            only_minimal, no_deep_fields
                        ))
                    rec_counter = update_rec_counter(
                        cur_channel, ext_id, rec_counter, use_workflow)
                    if loc_id < 0:
                        continue
                    ctr += 1
                    if loc_id not in local_ids:
                        local_ids.append(loc_id)
            _logger.info('%s record successfully pulled from channel %s' % (
                ctr, channel_id))
        if use_workflow:
            wkf = {'rec_counter': rec_counter, 'workflow_model': ''}
            if not local_ids or WORKFLOW[workflow].get('remote_ids'):
                wkf = {'import_workflow': workflow + 1, 'rec_counter': 0}
            cur_channel.write(wkf)
            self.logmsg('debug',
                '>>> WORKFLOW(%(w)s,%(c)s)',
                ctx={'w': wkf.get('import_workflow', workflow),
                     'c': wkf['rec_counter']})
        return local_ids

    @api.model
    def pull_1_record(self, channel_id, xmodel, item, disable_post=None,
                      only_minimal=None, no_deep_fields=None):
        self.logmsg('debug', '>>> %(model)s.pull_1_record(%(x)s)',
            model=xmodel, ctx={'x': item})
        cache = self.env['ir.model.synchro.cache']
        ext_id_name = cache.get_model_attr(
            channel_id, xmodel, 'KEY_ID', default='id')
        ext_id, vals = self.vals_or_id(item, ext_id_name)
        if not vals and ext_id:
            vals = self.get_counterpart_response(channel_id, xmodel, ext_id)
        if not vals:
            return
        ext_id, vals = self.vals_or_id(vals, ext_id_name)
        if not ext_id_name:
            self.logmsg('warning',
                'Data received of model %s w/o id' %
                xmodel)
            return
        cls = self.env[xmodel]
        id = self.generic_synchro(cls, vals, disable_post=disable_post,
            jacket=True, channel_id=channel_id,
            only_minimal=only_minimal, no_deep_fields=no_deep_fields)
        if id < 0:
            self.logmsg(
                'warning',
                'External id %s error pulling from %s' %
                (ext_id, xmodel))
            return id
        # commit every table to avoid too big transaction
        self.env.cr.commit()  # pylint: disable=invalid-commit
        return id

    @api.multi
    def pull_record(self, cls, channel_id=None):
        """Button synchronize at record UI page"""
        self.logmsg('debug', '>>> pull_record()')
        cache = self.env['ir.model.synchro.cache']
        for rec in cls:
            model = cls.__class__.__name__
            self.logmsg('info', '>>> %s.pull_record()' % model)
            cache.open(model=model, cls=cls)
            if not cache.is_struct(model):
                continue
            cache.setup_channels(all=True)
            for channel_id in cache.get_channel_list().copy():
                identity = cache.get_attr(channel_id, 'IDENTITY')
                loc_ext_id_name = self.get_loc_ext_id_name(channel_id, model)
                if loc_ext_id_name and hasattr(rec, loc_ext_id_name):
                    xmodel = model
                    ext_id = getattr(rec, loc_ext_id_name)
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
                        loc_ext_id_name = self.get_loc_ext_id_name(
                            channel_id, xmodel)
                        if (loc_ext_id_name and cache.get_struct_model_attr(model,
                                loc_ext_id_name)):
                            ext_id = getattr(rec, loc_ext_id_name)
                            ext_id = self.get_actual_ext_id_value(
                                channel_id, xmodel, ext_id)
                            if ext_id:
                                cache.open(model=xmodel)
                                self.pull_1_record(
                                    channel_id, xmodel, ext_id)

    @api.model
    def trigger_one_record(self, ext_model, prefix, ext_id):
        self.logmsg('debug', '>>> trigger_one_record(%(xm)s,%(xid)s,%(pfx)s)',
            ctx={'xm': ext_model, 'xid': ext_id, 'pfx': prefix})
        if not prefix:
            return
        cache = self.env['ir.model.synchro.cache']
        # cache.open(ext_model=ext_model)
        channel_id = self.assign_channel({'%s:' % prefix: ''})
        if not channel_id:
            cache.clean_cache()
            _logger.error('!-6! No channel found!')
            return -6
        self.logmsg('debug', '### assigned channel is %(chid)s',
            ctx={'chid': channel_id})
        cache.open(channel_id=channel_id, ext_model=ext_model)
        for model in cache.get_channel_models(channel_id):
            if not cache.is_struct(model):
                continue
            if ext_model != cache.get_model_attr(channel_id, model, 'BIND'):
                continue
            self.logmsg('info', '### Pulling %(model)s.%(id)s',
                model=model, ctx={'id': ext_id})
            return self.pull_1_record(channel_id, model, ext_id)
        return -8

    def manage_module(self, vals):
        if 'name' not in vals:
            self.logmsg('error', 'Invalid module name')
            return -7
        if vals.get('state', 'installed') != 'installed':
            self.logmsg('error',
                'Module %s is not installed on counterpart' % vals['name'])
            return -4
        module_model = self.env['ir.module.module']
        module_ids = module_model.search([('name', '=', vals['name'])])
        if not module_ids:
            self.logmsg('error', 'Module %s does not exist' % vals['name'])
            return -3
        module = module_ids[0]
        if module.state == 'uninstalled':
            try:
                module_model.execute('button_immediate_install', module_ids)
                time.sleep(len(module.dependencies_id) + 3)
            except BaseException:
                self.logmsg('error',
                    'Module %s not installable' % vals['name'])
                return -4
            module = module_model.browse(module_ids[0])
        if module.state != 'installed':
            self.logmsg('error',
                'Module %s not installed' % vals['name'])
            return -4
        self.logmsg('info',
            '>>> %s.install(%s)' % ('ir.module.module', module.name))
        self.logmsg('trace', '', model='ir.module.module', rec=module)
        return module.id

    def manage_language(self, lang_rec):
        if lang_rec.code:
            lang_model = self.env['base.language.install']
            vals = {
                'lang': lang_rec.code,
                'overwite': True
            }
            lang_model.create(vals).lang_install()
        return


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


class IrModelSynchroLog(models.Model):
    _name = 'ir.model.synchro.log'
    _order = 'timestamp desc'

    timestamp = fields.Datetime('Timestamp', copy=False)
    model = fields.Char('Model')
    res_id = fields.Integer('Model ID')
    errmsg = fields.Char('Error message', copy=False)

    def logger(self, xmodel, rec, errmsg):
        now = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        errmsg = errmsg or _('No Error')
        res_id = rec and rec.id or False
        self.create({
            'timestamp': now,
            'model': xmodel or '',
            'res_id': res_id,
            'errmsg': errmsg,
        })
        if rec and hasattr(rec, 'timestamp') and hasattr(rec, 'errmsg'):
            rec.write({'timestamp': now, 'errmsg': errmsg})
        self.env.cr.commit()  # pylint: disable=invalid-commit

    def purge_log(self):
        for day in (15, 8, 7, 5, 3, 2, 1):
            last = (datetime.today() - timedelta(day)).strftime(
                '%Y-%m-%d %H:%M:%S')
            domain = [('timestamp', '>=', last)]
            nrecs = self.search_count(domain)
            domain = [('timestamp', '<', last)]
            if nrecs < 10000:
                break
        max_recs_per_session = 1000
        for rec in self.search(domain, order='timestamp desc'):
            rec.unlink()
            max_recs_per_session -= 1
            if not max_recs_per_session:
                break
