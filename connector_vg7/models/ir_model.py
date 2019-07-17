# -*- coding: utf-8 -*-
# Copyright 2019 Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
# Return code:
# -1: error creating record
# -2: error writing record
# -3: record with passed id does not exist
# -4: unmodificable record
# -5: invalid structure header/details
# -6: unrecognized channel
# -7: no data supplied
#
import os
from datetime import datetime,timedelta
import requests
import json
import logging
from os0 import os0
from odoo import fields, models, api
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

try:
    from unidecode import unidecode
except ImportError as err:
    _logger.debug(err)


EXPIRATION_TIME = 3


class IrModelSynchro(models.Model):
    _name = 'ir.model.synchro'
    _inherit = 'ir.model'

    CONTEXT_FIELDS = {'company_id': False,
                      'country_id': False,
                      'is_company': True,
    }
    STRUCT = {}
    MANAGED_MODELS = {}
    LOGLEVEL = 'info'
    SKEYS = {
        'res.country.state': (['country_id', 'code'],),
        'res.partner': (['name', 'vat'], ['vat'],),
        'res.company': (['vat'],),
        'account.account.type': (['type'],),
        'product.template': (['name', 'default_code'],),
        'product.product': (['name', 'default_code'],),
    }

    def _build_unique_index(self, model, prefix):
        '''Build unique index on table to <vg7>_id for performance'''
        if isinstance(model, (list, tuple)):
            table = model[0].replace('.', '_')
        else:
            table = model.replace('.', '_')
        index_name = '%s_unique_%s' % (table, prefix)
        self._cr.execute(
            "SELECT indexname FROM pg_indexes WHERE indexname = '%s'" %
            index_name
        )
        if not self._cr.fetchone():
            self._cr.execute(
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
        if channel_id:
            loglevel = self.MANAGED_MODELS[channel_id]['LOGLEVEL']
        else:
            loglevel = self.LOGLEVEL
        if loglevel == 'info':
            _logger.info(msg)
        else:
            _logger.debug(msg)

    def tnl_2_loc_set_value(self, vals, loc_name, ext_ref, default=None):
        vals[loc_name] = default
        if loc_name != ext_ref:
            del vals[ext_ref]
        return vals

    def tnl_2_loc_upper(self, vals, loc_name, ext_ref, default=None):
        vals[loc_name] = vals[ext_ref].upper()
        if loc_name != ext_ref:
            del vals[ext_ref]
        return vals

    def tnl_2_loc_lower(self, vals, loc_name, ext_ref, default=None):
        vals[loc_name] = vals[ext_ref].lower()
        if loc_name != ext_ref:
            del vals[ext_ref]
        return vals

    def tnl_2_loc_bool(self, vals, loc_name, ext_ref, default=None):
        vals[loc_name] = os0.str2bool(vals[ext_ref], False)
        if loc_name != ext_ref:
            del vals[ext_ref]
        return vals

    def tnl_2_loc_not(self, vals, loc_name, ext_ref, default=None):
        vals[loc_name] = not os0.str2bool(vals[ext_ref], True)
        if loc_name != ext_ref:
            del vals[ext_ref]
        return vals

    def tnl_2_loc_person(self, vals, loc_name, ext_ref, default=None):
        '''First name and/or last name'''
        if loc_name != ext_ref:
            vals[loc_name] = vals[ext_ref]
            del vals[ext_ref]
        if 'lastname' in vals and 'firstname' in vals:
            if not vals.get('name'):
                vals['name'] = '%s %s' % (vals['lastname'], vals['firstname'])
                vals['is_company'] = False
            del vals['lastname']
            del vals['firstname']
        return vals

    def tnl_2_loc_vat(self, vals, loc_name, ext_ref, default=None):
        '''External vat may not contain ISO code'''
        if len(vals[ext_ref]) == 11 and vals[ext_ref].isdigit():
            vals[loc_name] = 'IT%s' % vals[ext_ref]
        else:
            vals[loc_name] = vals[ext_ref]
        if loc_name != ext_ref:
            del vals[ext_ref]
        return vals

    def tnl_2_loc_street_number(self, vals, loc_name, ext_ref, default=None):
        '''Street number'''
        if 'street' in vals:
            loc_name = 'street'
        else:
            loc_name = '%s:street' % ext_ref[0:3]
        if loc_name in vals:
            vals[loc_name] = '%s, %s' % (vals[loc_name], vals[ext_ref])
        del vals[ext_ref]
        return vals

    def tnl_2_loc_invoice_number(self, vals, loc_name, ext_ref, default=None):
        '''Invoice number'''
        if ext_ref in vals:
            vals['move_name'] = vals[ext_ref]
        return vals

    def tnl_2_loc_journal(self, vals, loc_name, ext_ref, default=None):
        if 'journal_id' not in vals:
            journal = self.env['account.invoice']._default_journal()
            if journal:
                vals['journal_id'] = journal[0].id
        return vals

    def tnl_2_loc_account(self, vals, loc_name, ext_ref, default=None):
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

    def tnl_2_loc_uom(self, vals, loc_name, ext_ref, default=None):
        if loc_name not in vals and 'product_id' in vals:
            product = self.env['product.product'].browse(vals['product_id'])
            vals[loc_name] = product.uom_id.id
        return vals

    def tnl_2_loc_tax(self, vals, loc_name, ext_ref, default=None):
        if loc_name not in vals and 'product_id' in vals:
            product = self.env['product.product'].browse(vals['product_id'])
            if vals.get('type') in ('in_invoice', 'in_refund'):
                tax = product.supplier_taxes_id
            else:
                tax = product.taxes_id
            if tax:
                vals[loc_name] = [(6, 0, [tax.id])]
        return vals

    def get_model_structure(self, model, ignore=None):
        '''Store model structure in memory'''
        ignore = ignore or []
        if (self.STRUCT.get(model, {}) and
                datetime.now() < self.STRUCT[model]['EXPIRE']):
            return
        self.STRUCT[model] = self.STRUCT.get(model, {})
        self.STRUCT[model]['EXPIRE'] = datetime.now() + timedelta(
            minutes=(EXPIRATION_TIME + 3))
        ir_model = self.env['ir.model.fields']
        for field in ir_model.search([('model', '=', model)]):
            required = field.required
            readonly = field.readonly
            readonly = readonly or field.ttype in ('binary', 'reference')
            if field.name in ignore:
                readonly = True
            self.STRUCT[model][field.name] = {
                'ttype': field.ttype,
                'relation': field.relation,
                'required': required,
                'readonly': readonly,
                'protect': field.protect_update,
                }
            if field.relation and field.relation.startswith(model):
                self.STRUCT[model]['LINES_OF_REC'] = field.name
                self.STRUCT[model]['LINE_MODEL'] = field.relation
            elif field.relation and model.startswith(field.relation):
                self.STRUCT[model]['PARENT_ID'] = field.name
            if field.name == 'original_state':
                self.STRUCT[model]['MODEL_STATE'] = True
            elif field.name == 'to_delete':
                self.STRUCT[model]['MODEL_2DELETE'] = True
            elif field.name == 'name':
                self.STRUCT[model]['MODEL_WITH_NAME'] = True
            elif field.name == 'active':
                self.STRUCT[model]['MODEL_WITH_ACTIVE'] = True
            elif field.name == 'dim_name':
                self.STRUCT[model]['MODEL_WITH_DIMNAME'] = True
            elif field.name == 'company_id':
                self.STRUCT[model]['MODEL_WITH_COMPANY'] = True
            elif field.name == 'country_id':
                self.STRUCT[model]['MODEL_WITH_COUNTRY'] = True

    def get_channels(self):
        self.LOGLEVEL = 'info'
        for channel in self.env['synchro.channel'].search([]):
            if (channel.id in self.MANAGED_MODELS):
                if channel.trace:
                    self.LOGLEVEL = 'debug'
                if (datetime.now() < self.MANAGED_MODELS[
                        channel.id]['EXPIRE']):
                    continue
            self.MANAGED_MODELS[channel.id] = {}
            self.MANAGED_MODELS[channel.id]['EXPIRE'] = datetime.now(
                ) + timedelta(minutes=EXPIRATION_TIME*10)
            self.MANAGED_MODELS[channel.id]['PREFIX'] = channel.prefix
            self.MANAGED_MODELS[channel.id]['IDENTITY'] = channel.identity
            if channel.company_id:
                self.MANAGED_MODELS[channel.id][
                    'COMPANY_ID'] = channel.company_id.id
            else:
                self.MANAGED_MODELS[channel.id][
                    'COMPANY_ID'] = self.env.user.company_id.id
            self.MANAGED_MODELS[channel.id]['CLIENT_KEY'] = channel.client_key
            self.MANAGED_MODELS[channel.id][
                'COUNTERPART_URL'] = channel.counterpart_url
            self.MANAGED_MODELS[channel.id]['PASSWORD'] = channel.password
            if channel.produtc_without_variants:
                self.MANAGED_MODELS[channel.id]['NO_VARIANTS'] = True
            if channel.trace:
                self.MANAGED_MODELS[channel.id]['LOGLEVEL'] = 'debug'
                self.LOGLEVEL = 'debug'
            else:
                self.MANAGED_MODELS[channel.id]['LOGLEVEL'] = 'info'

    def get_channel_models(self, model=None):
        where = [('name', '=', model)] if model else []
        for rec in self.env['synchro.channel.model'].search(where):
            if rec.synchro_channel_id.id not in self.MANAGED_MODELS:
                continue
            model = rec.name
            channel_id = rec.synchro_channel_id.id
            if (model in self.MANAGED_MODELS[channel_id] and
                    datetime.now() < self.MANAGED_MODELS[
                    channel_id][model]['EXPIRE']):
                continue
            self.MANAGED_MODELS[channel_id][model] = {}
            if model:
                self.MANAGED_MODELS[channel_id][model][
                    'EXPIRE'] = datetime.now() + timedelta(
                        minutes=EXPIRATION_TIME)
            else:
                self.MANAGED_MODELS[channel_id][model][
                    'EXPIRE'] = datetime.now() + timedelta()
            if rec.field_2complete:
                self.MANAGED_MODELS[channel_id][model]['2PULL'] = True
            self.MANAGED_MODELS[channel_id][model][
                'MODEL_KEY'] = rec.field_uname
            self.MANAGED_MODELS[channel_id][model][
                'SKEYS'] = eval(rec.search_keys)
            self.MANAGED_MODELS[channel_id][model][
                'BIND'] = rec.counterpart_name
            if model:
                self.get_channel_model_fields(rec)
                self.get_model_structure(model)
        if model:
            for channel_id in self.MANAGED_MODELS:
                if self.MANAGED_MODELS[channel_id]['IDENTITY'] == 'odoo':
                    self.set_odoo_model(model, channel_id)

    def get_channel_model_fields(self, model_rec):
        model = model_rec.name
        channel_id = model_rec.synchro_channel_id.id
        self.MANAGED_MODELS[channel_id][model]['LOC_FIELDS'] = {}
        self.MANAGED_MODELS[channel_id][model]['EXT_FIELDS'] = {}
        self.MANAGED_MODELS[channel_id][model]['APPLY'] = {}
        self.MANAGED_MODELS[channel_id][model]['PROTECT'] = {}
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
            self.MANAGED_MODELS[channel_id][
                    model]['LOC_FIELDS'][loc_name] = ext_name
            self.MANAGED_MODELS[channel_id][
                    model]['EXT_FIELDS'][ext_name] = loc_name
            if field.apply and field.apply != 'none':
                self.MANAGED_MODELS[channel_id][
                    model]['APPLY'][loc_name] = field.apply
            if field.protect and field.protect != '0':
                self.MANAGED_MODELS[channel_id][
                    model]['PROTECT'][loc_name] = field.protect
        # special names
        self.MANAGED_MODELS[channel_id][model]['LOC_FIELDS']['id'] = ''
        ext_ref = '%s_id' % self.MANAGED_MODELS[channel_id]['IDENTITY']
        self.MANAGED_MODELS[channel_id][model]['LOC_FIELDS'][ext_ref] = 'id'
        self.MANAGED_MODELS[channel_id][model]['EXT_FIELDS']['id'] = ext_ref

    def set_odoo_model(self, model, channel_id):
        if model in self.MANAGED_MODELS[channel_id]:
            return
        self.MANAGED_MODELS[channel_id][model] = {}
        self.MANAGED_MODELS[channel_id][model]['LOC_FIELDS'] = {}
        self.MANAGED_MODELS[channel_id][model]['EXT_FIELDS'] = {}
        self.MANAGED_MODELS[channel_id][model]['APPLY'] = {}
        self.MANAGED_MODELS[channel_id][model]['PROTECT'] = {}
        skeys = ['name']
        for field in self.STRUCT[model]:
            if field <= 'Z':
                continue
            self.MANAGED_MODELS[channel_id][
                model]['LOC_FIELDS'][field] = field
            self.MANAGED_MODELS[channel_id][
                model]['EXT_FIELDS'][field] = field
            self.MANAGED_MODELS[channel_id][
                model]['PROTECT'][field] = self.STRUCT[model][field]['protect']
            if ((field == 'description' and model == 'account.tax') or
                    field == 'code'):
                skeys =[field]
        if model in self.SKEYS:
            self.MANAGED_MODELS[channel_id][model][
                'SKEYS'] = self.SKEYS[model]
        else:
            self.MANAGED_MODELS[channel_id][model][
                'SKEYS'] = [skeys]

    @api.model_cr_context
    def _init_self(self, model=None, cls=None):
        if not self.MANAGED_MODELS:
            self.get_channels()
            self.get_channel_models(model=model)
        elif model:
            self.get_channels()
            self.get_channel_models(model=model)
            self.get_model_structure(model)
        else:
            self.get_channels()
            self.get_channel_models()
        if cls is not None:
            if cls.__class__.__name__ != model:
                raise RuntimeError('Class %s not of declared model %s' % (
                    cls.__class__.__name__, model))
            if hasattr(cls, 'LINES_OF_REC'):
                self.STRUCT[model]['LINES_OF_REC'] = getattr(cls,
                                                             'LINES_OF_REC')
            if hasattr(cls, 'LINE_MODEL'):
                self.STRUCT[model]['LINE_MODEL'] = getattr(cls,
                                                           'LINE_MODEL')
            if hasattr(cls, 'PARENT_ID'):
                self.STRUCT[model]['PARENT_ID'] = getattr(cls, 'PARENT_ID')

    def drop_fields(self, model, vals, to_delete):
        for name in to_delete:
            if isinstance(vals, (list, tuple)):
                del vals[vals.index(name)]
            else:
                del vals[name]
        return vals

    def drop_invalid_fields(self, model, vals):
        if isinstance(vals, (list, tuple)):
            to_delete = list(set(vals) - set(self.STRUCT[model].keys()))
        else:
            to_delete = list(set(vals.keys()) - set(self.STRUCT[model].keys()))
        return self.drop_fields(model, vals, to_delete)

    def drop_protected_fields(self, rec, vals, model, channel_id):
        for field in vals.copy():
            protect = max(
                int(self.STRUCT[model].get(field, {}).get('protect', '0')),
                int(self.MANAGED_MODELS[channel_id][model]['PROTECT'].get(
                    field, '0')))
            if (protect == 2 or (protect == 1 and rec[field])):
                del vals[field]
            elif (isinstance(vals[field], (basestring, int, long, bool)) and
                    vals[field] == rec[field]):
                del vals[field]
        return vals

    def set_state_to_draft(self, model, rec, vals):
        if 'state' in vals:
            vals['original_state'] = vals['state']
        elif rec:
            vals['original_state'] = rec.state
        if model == 'account.invoice':
            if rec:
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
        return vals, 0

    def set_actual_state(self, model, rec):
        if model == 'account.invoice':
            if rec:
                rec.compute_taxes()
                if rec.state == rec.original_state:
                    return rec.id
                elif rec.state != 'draft':
                    return -4
                elif rec.original_state == 'open':
                    rec.action_invoice_open()
                elif rec.original_state == 'cancel':
                    rec.action_invoice_cancel()
        elif model == 'sale.order':
            if rec:
                rec._compute_tax_id()
                if rec.state == rec.original_state:
                    return rec.id
                elif rec.state != 'draft':
                    return -4
                elif rec.original_state == 'sale':
                    rec.action_confirm()
                elif rec.original_state == 'cancel':
                    rec.action_cancel()
        return rec.id

    def get_rec_by_reference(self, model, key_name, value, ctx, ilike=None):
        ir_model = self.env[model]
        if ilike:
            where = [(key_name, 'ilike', value)]
        else:
            where = [(key_name, '=', value)]
        if model not in ('res.partner', 'product.product', 'product.template'):
            if (key_name != 'id' and ctx.get('company_id') and
                    self.STRUCT[model].get('MODEL_WITH_COMPANY')):
                where.append(('company_id', '=', ctx['company_id']))
        if (key_name != 'id' and ctx.get('country_id') and
                self.STRUCT[model].get('MODEL_WITH_COUNTRY')):
            where.append(('country_id', '=', ctx['country_id']))
        rec = ir_model.search(where)
        if not rec and not ilike and key_name == 'name':
            return self.get_rec_by_reference(model, key_name, value, ctx,
                                             ilike=True)
        return rec

    def bind_foreign_text(self, model, value, is_foreign,
                          channel_id, ctx):
        if value.isdigit():
            return int(value)
        ir_model = self.env[model]
        if model in self.MANAGED_MODELS[channel_id]:
            key_name = self.MANAGED_MODELS[
                channel_id][model]['MODEL_KEY']
        else:
            key_name = 'name'
        new_value = False
        rec = self.get_rec_by_reference(model, key_name, value, ctx)
        if rec:
            new_value = rec[0].id
        if not new_value and model in self.MANAGED_MODELS[channel_id]:
            vals = {key_name: value}
            if (self.STRUCT[model].get('MODEL_WITH_COMPANY') and
                    ctx.get('company_id')):
                vals['company_id'] = ctx['company_id']
            if (self.STRUCT[model].get('MODEL_WITH_COUNTRY') and
                    ctx.get('country_id')):
                vals['country_id'] = ctx['country_id']
            new_value = self.synchro(ir_model, vals)
        return new_value

    def bind_foreign_ref(self, model, value, ext_id, is_foreign,
                         channel_id, ctx):
        new_value = False
        ir_model = self.env[model]
        if is_foreign:
            rec = ir_model.search([(ext_id, '=', value)])
        else:
            new_value = value
            rec = False
        if rec:
            new_value = rec[0].id
        if not new_value and model in self.MANAGED_MODELS[channel_id]:
            vals = {
                ext_id: value,
                'name': 'Unknown %d' % value,
            }
            if self.STRUCT[model].get('MODEL_WITH_COMPANY'):
                vals['company_id'] = ctx['company_id']
            new_value = self.synchro(ir_model, vals)
        return new_value

    def get_foreign_value(self, model, channel_id, value,
                         is_foreign, ext_id, ctx, tomany=None):
        self.logmsg(channel_id, 'get_foreign_value(%s,%s,%s)' % (
                    model, value, ext_id))
        if not value:
            return value
        self.get_model_structure(model)
        self.get_channel_models(model=model)
        new_value = False
        if isinstance(value, basestring):
            new_value = self.bind_foreign_text(
                model, value, is_foreign, channel_id, ctx)
            if tomany:
                new_value = [new_value]
        elif isinstance(model, (list, tuple)):
            new_value = []
            for id in value:
                new_value.append(self.bind_foreign_ref(
                    model, id, ext_id, is_foreign, channel_id, ctx))
        else:
            new_value = self.bind_foreign_ref(
                model, value, ext_id, is_foreign, channel_id, ctx)
        return new_value

    def cvt_m2o_value(self, model, name, value,
                      channel_id, ext_id, is_foreign, ctx, format=None):
        relation = self.STRUCT[model][name]['relation']
        if not relation:
            raise RuntimeError('No relation for field %s of %s' % (name,
                                                                   model))
        return self.get_foreign_value(relation, channel_id, value,
                                    is_foreign, ext_id, ctx)

    def cvt_m2m_value(self, model, name, value,
                      channel_id, ext_id, is_foreign, ctx, format=None):
        relation = self.STRUCT[model][name]['relation']
        if not relation:
            raise RuntimeError('No relation for field %s of %s' % (name,
                                                                   model))
        value = self.get_foreign_value(relation, channel_id, value,
                                       is_foreign, ext_id, ctx,
                                       tomany=True)
        if format == 'cmd' and value:
            value = [(6, 0, value)]
        return value

    def cvt_o2m_value(self, model, name, value,
                      channel_id, ext_id, is_foreign, ctx, format=None):
        relation = self.STRUCT[model][name]['relation']
        if not relation:
            raise RuntimeError('No relation for field %s of %s' % (name,
                                                                   model))
        value = self.get_foreign_value(relation, channel_id, value,
                                       is_foreign, ext_id, ctx,
                                       tomany=True)
        if format == 'cmd' and value:
            value = [(6, 0, value)]
        return value

    def names_from_ref(self, model, channel_from, vals, ext_ref,
                       prefix1, prefix2):
        if ext_ref.startswith(prefix1):
            # Case #1 - field like vg7_oder_id: name is odoo but value id
            #           id counterpart ref
            is_foreign = True
            loc_name = ext_ref[4:]
            loc_ext_ref = ext_ref
            if loc_name == 'id':
                loc_name = ext_name = loc_ext_ref
            else:
                if (model in self.MANAGED_MODELS[channel_from] and
                        loc_name in self.MANAGED_MODELS[
                            channel_from][model]['LOC_FIELDS']):
                    ext_name = self.MANAGED_MODELS[
                        channel_from][model]['LOC_FIELDS'][loc_name]
                    if ext_name[0] == '.':
                        ext_name = ''
                else:
                    ext_name = ''
        elif ext_ref.startswith(prefix2):
            # Case #2 - field like vg7:oder_id: both name and value are
            #           of counterpart refs
            is_foreign = True
            ext_name = ext_ref[4:]
            loc_ext_ref = prefix1 + ext_name
            if (model in self.MANAGED_MODELS[channel_from] and
                    ext_name in self.MANAGED_MODELS[
                        channel_from][model]['EXT_FIELDS']):
                loc_name = self.MANAGED_MODELS[
                    channel_from][model]['EXT_FIELDS'][ext_name]
                if loc_name[0] == '.':
                    loc_name = ''
            else:
                loc_name = ''
        else:
            # Case #3 - field and value are Odoo
            is_foreign = False
            ext_name = loc_name = ext_ref
            loc_ext_ref = ''
        return ext_name, loc_name, is_foreign, loc_ext_ref

    def get_default_n_apply(self, model, channel_from, loc_name, ext_name,
                            ttype=None):
        if model not in self.MANAGED_MODELS[channel_from]:
            return '', ''
        default = self.MANAGED_MODELS[
            channel_from][model]['APPLY'].get(loc_name or
                                              '.%s' % ext_name, '')
        if default.endswith('()'):
            apply = 'tnl_2_loc_%s' % default[:-2]
            default = False
        elif default:
            apply = 'tnl_2_loc_set_value'
        else:
            apply = ''
        if ttype == 'boolean':
            default = os0.str2bool(default, True)
        return default, apply

    def bind_to_internal(self, model, vals):

        def search_4_channel(vals):
            odoo_channel = channel_from = prefix1 = prefix2 = False
            for channel_id in self.MANAGED_MODELS:
                if channel_from:
                    break
                prefix1 = '%s_' % self.MANAGED_MODELS[channel_id]['PREFIX']
                prefix2 = '%s:' % self.MANAGED_MODELS[channel_id]['PREFIX']
                if self.MANAGED_MODELS[channel_id]['IDENTITY'] == 'odoo':
                    odoo_channel = channel_id
                for ext_ref in vals:
                    if (ext_ref.startswith(prefix1) or
                            ext_ref.startswith(prefix2)):
                        channel_from = channel_id
                        break
            if not channel_from and odoo_channel is not False:
                channel_from = odoo_channel
                prefix1 = '%s_' % self.MANAGED_MODELS[channel_from]['PREFIX']
                prefix2 = '%s:' % self.MANAGED_MODELS[channel_from]['PREFIX']
            return channel_from, prefix1, prefix2

        def process_fields(model, channel_from, vals, ext_id, ctx,
                           field_list=None, excl_list=None):
            for ext_ref in vals.copy():
                ext_name, loc_name, is_foreign, loc_ext_ref = \
                    self.names_from_ref(model, channel_from, vals,
                                        ext_ref, prefix1, prefix2)
                default, apply = self.get_default_n_apply(
                    model, channel_from, loc_name, ext_name,
                    ttype=self.STRUCT[model].get(loc_name, {}).get('ttype'))
                if not loc_name and is_foreign and hasattr(self, apply):
                    self.logmsg(channel_from,
                                '> Apply %s(%s,%s,%s)' % (
                                    apply,
                                    loc_name,
                                    ext_ref,
                                    default))
                    vals = getattr(self, apply)(vals,
                                                loc_name,
                                                ext_ref,
                                                default=default)
                    continue
                if not loc_name or loc_name not in self.STRUCT[model]:
                    self.logmsg(channel_from,
                        'Field <%s> does not exist in model %s' % (ext_ref,
                                                                   model))
                    del vals[ext_ref]
                    continue
                if (self.STRUCT[model][loc_name]['ttype'] in (
                        'many2one', 'integer') and
                        isinstance(vals[ext_ref], basestring) and
                        vals[ext_ref].isdigit()):
                    vals[ext_ref] = int(vals[ext_ref])
                elif (self.STRUCT[model][loc_name]['ttype'] == 'boolean' and
                         isinstance(vals[ext_ref], basestring)):
                    vals[ext_ref] = os0.str2bool(vals[ext_ref], True)
                if field_list and loc_name not in field_list:
                    continue
                if excl_list and loc_name in excl_list:
                    continue
                if is_foreign:
                    # Field like <vg7_id> with external ID in local DB
                    if loc_ext_ref in self.STRUCT[model]:
                        if ext_ref.startswith(prefix2):
                            vals[loc_ext_ref] = vals[ext_ref]
                            del vals[ext_ref]
                        rec = self.get_rec_by_reference(
                            model, loc_ext_ref, vals[loc_ext_ref], ctx)
                        if rec:
                            vals[loc_name] = rec[0][loc_ext_ref]
                            vals['id'] = rec[0].id
                            ext_id = loc_ext_ref
                        continue
                    # Counterpart one can supply both local and external value
                    elif loc_name in vals:
                        del vals[ext_ref]
                if self.STRUCT[model][loc_name]['ttype'] == 'one2many':
                    vals[loc_name] = self.cvt_o2m_value(
                        model, loc_name, vals[ext_ref],
                        channel_from, ext_id, is_foreign, ctx,
                        format='cmd')
                    if is_foreign or loc_name != ext_name:
                        del vals[ext_ref]
                elif self.STRUCT[model][loc_name]['ttype'] == 'many2many':
                    vals[loc_name] = self.cvt_m2m_value(
                        model, loc_name, vals[ext_ref],
                        channel_from, ext_id, is_foreign, ctx,
                        format='cmd')
                    if is_foreign or loc_name != ext_name:
                        del vals[ext_ref]
                elif self.STRUCT[model][loc_name]['ttype'] == 'many2one':
                    vals[loc_name] = self.cvt_m2o_value(
                        model, loc_name, vals[ext_ref],
                        channel_from, ext_id, is_foreign, ctx,
                        format='cmd')
                    if is_foreign or loc_name != ext_name:
                        del vals[ext_ref]
                elif is_foreign:
                    if hasattr(self, apply):
                        self.logmsg(channel_from,
                                    '> Apply %s(%s,%s,%s)' % (
                                        apply,
                                        loc_name,
                                        ext_ref,
                                        default))
                        vals = getattr(self, apply)(vals,
                                                    loc_name,
                                                    ext_ref,
                                                    default=default)
                    else:
                        vals[loc_name] = vals[ext_ref]
                        del vals[ext_ref]
            for loc_name in ctx:
                if loc_name not in vals and loc_name in self.STRUCT[model]:
                    if (loc_name != 'company_id' or
                            model not in ('res.partner',
                                          'product.product',
                                          'product.template')):
                        vals[loc_name] = ctx[loc_name]
            return vals

        channel_from, prefix1, prefix2 = search_4_channel(vals)
        if channel_from is False:
            _logger.info('> No valid channel detected')
            return vals, False, False
        ext_id = '%s_id' % self.MANAGED_MODELS[channel_from]['PREFIX']
        ctx = {}
        if 'company_id' in vals:
            ctx['company_id'] = vals['company_id']
        else:
            ctx['company_id'] =  self.MANAGED_MODELS[
                channel_from]['COMPANY_ID']
        if ctx['company_id']:
            ctx['country_id'] = self.env[
                'res.company'].browse(
                    ctx['company_id']).partner_id.country_id.id
        else:
            ctx['country_id'] = False
        self.logmsg(channel_from, 'ctx=%s' % ctx)
        vals = process_fields(model, channel_from, vals, ext_id, ctx,
                              field_list=(ctx.keys() + ['street']))
        vals = process_fields(model, channel_from, vals, ext_id, ctx,
                              excl_list=(ctx.keys() + ['street']))
        if (model == 'product.product' and
                vals.get('name') and
                ext_id in vals and
                self.MANAGED_MODELS[channel_from].get('NO_VARIANTS')):
            tmpl_vals = vals.copy()
            if 'id' in tmpl_vals:
                del tmpl_vals['id']
            id = self.synchro(self.env['product.template'], tmpl_vals)
            if id > 0:
                vals['product_tmpl_id'] = id
        return vals, ext_id, channel_from

    def set_default_values(self, model, vals, channel_id):
        prefix1 = '%s_' % self.MANAGED_MODELS[channel_id]['PREFIX']
        prefix2 = '%s:' % self.MANAGED_MODELS[channel_id]['PREFIX']
        for ext_ref in self.MANAGED_MODELS[channel_id][model]['APPLY']:
            ext_name, loc_name, is_foreign, loc_ext_ref = \
                self.names_from_ref(model, channel_id, vals,
                                    ext_ref, prefix1, prefix2)
            if loc_name not in vals:
                if (model in self.MANAGED_MODELS[channel_id] and
                        loc_name in self.MANAGED_MODELS[
                            channel_id][model]['LOC_FIELDS']):
                    ext_name = self.MANAGED_MODELS[
                        channel_id][model]['LOC_FIELDS'][loc_name]
                    if ext_name[0] == '.':
                        default, apply = self.get_default_n_apply(
                            model, channel_id, loc_name, ext_name,
                            ttype=self.STRUCT[model][loc_name]['ttype'])
                        if hasattr(self, apply):
                            self.logmsg(channel_id,
                                '> Apply %s(%s,%s,%s)' % (
                                    apply,
                                    loc_name,
                                    ext_ref,
                                    default))
                            vals = getattr(self, apply)(vals,
                                                        loc_name,
                                                        ext_ref,
                                                        default=default)
        return vals

    def search4rec(self, model, vals, ext_id,
                   constraints, has_active, channel_id):
        ir_model = self.env[model]
        company_id =  self.MANAGED_MODELS[channel_id]['COMPANY_ID']
        id = -1
        for keys in self.MANAGED_MODELS[channel_id][model]['SKEYS']:
            where = []
            for key in keys:
                if (key not in vals and
                        key == 'dim_name' and
                        vals.get('name')):
                    where.append(('dim_name',
                                  '=',
                                  self.dim_text(vals['name'])))
                elif key not in vals and key in self.CONTEXT_FIELDS:
                    if key == 'company_id':
                        where.append((key, '=', company_id))
                    elif self.CONTEXT_FIELDS[key]:
                        where.append((key, '=', self.CONTEXT_FIELDS[key]))
                elif key not in vals:
                    where = []
                    break
                else:
                    where.append((key, '=', vals[key]))
            if where:
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
                if ext_id:
                    where.append((ext_id, '=', False))
                rec = ir_model.search(where)
                if not rec and has_active:
                    where.append(('active', '=', False))
                    rec = ir_model.search(where)
                if rec:
                    id = rec[0].id
                    self.logmsg(channel_id,
                        '> synchro: found id=%d (%s)' % (id, where))
                    break
        if id < 0 and ext_id in vals:
            rec = ir_model.search(
                [('name', '=', 'Unknown %d' % vals[ext_id])])
            if rec:
                id = rec[0].id
                self.logmsg(channel_id,
                    '> synchro: found unknown id=%d' % id)
        return id

    def get_odoo_response(self, channel_id, model, id=False):
        return {}

    def get_vg7_response(self, channel_id, model, id=False):
        if id:
            url = os.path.join(
                self.MANAGED_MODELS[channel_id]['COUNTERPART_URL'],
                self.MANAGED_MODELS[channel_id][model]['BIND'],
                str(id))
        else:
            url = os.path.join(
                self.MANAGED_MODELS[channel_id]['COUNTERPART_URL'],
                self.MANAGED_MODELS[channel_id][model]['BIND'])
        headers = {'Authorization': 'access_token %s' %
                   self.MANAGED_MODELS[channel_id]['CLIENT_KEY']}
        try:
            response = requests.get(url, headers=headers)
        except BaseException:
            response = False
        if response:
            datas = response.json()
            return datas
        self.logmsg(channel_id,
                    'No response requests(%d,%s,%s,%s)' %
                    (channel_id,
                     url,
                     self.MANAGED_MODELS[channel_id]['CLIENT_KEY'],
                     self.MANAGED_MODELS[channel_id]['PREFIX']))
        self.STRUCT = {}
        self.MANAGED_MODELS = {}
        return {}

    def get_counterpart_response(self, channel_id, model, id=False):
        identity = self.MANAGED_MODELS[channel_id]['IDENTITY']
        if identity == 'odoo':
            return self.get_odoo_response(channel_id, model, id)
        elif identity == 'vg7':
            return self.get_vg7_response(channel_id, model, id)

    def show_debug(self, channel_id, model):
        if not channel_id:
            if not len(self.MANAGED_MODELS):
                return
            channel_id = self.MANAGED_MODELS.keys()[0]
        _logger.info('> channel_id=%d' % channel_id)
        _logger.info('> model=%s'% model)
        _logger.info('> model params:(2pull=%s,key=%s,bind=%s' % (
            self.MANAGED_MODELS[channel_id][model].get('2PULL'),
            self.MANAGED_MODELS[channel_id][model].get('MODEL_KEY'),
            self.MANAGED_MODELS[channel_id][model].get('BIND'),
            ))
        for field in self.MANAGED_MODELS[channel_id][model]['LOC_FIELDS']:
            _logger.info('--- %-20.20s=%-20.20s (%s/%s)' % (
                field,
                self.MANAGED_MODELS[channel_id][model]['LOC_FIELDS'][field],
                self.MANAGED_MODELS[channel_id][model]['APPLY'].get(field, 'None'),
                self.MANAGED_MODELS[channel_id][model]['PROTECT'].get(field, '0'),
            ))
        for field in self.MANAGED_MODELS[channel_id][model]['EXT_FIELDS']:
            loc_field = self.MANAGED_MODELS[channel_id][model]['EXT_FIELDS'][field]
            if loc_field in self.MANAGED_MODELS[channel_id][model]['LOC_FIELDS']:
                continue
            _logger.info('--- %-20.20s=%-20.20s (%s/%s)' % (
                loc_field,
                field,
                self.MANAGED_MODELS[channel_id][model]['APPLY'].get(loc_field, 'None'),
                self.MANAGED_MODELS[channel_id][model]['PROTECT'].get(loc_field, '0'),
            ))

    @api.model
    def synchro(self, cls, vals, constraints=None):
        model = cls.__class__.__name__
        self.logmsg(0, '> %s.synchro(%s)' % (model, vals))
        self._init_self(model=model, cls=cls)
        constraints = constraints or cls.CONTRAINTS
        has_dim_text = self.STRUCT[model].get('MODEL_WITH_DIMNAME', False)
        has_active = self.STRUCT[model].get('MODEL_WITH_ACTIVE', False) 
        has_state = self.STRUCT[model].get('MODEL_STATE', False)
        has_2delete = self.STRUCT[model].get('MODEL_2DELETE', False)
        if has_2delete:
            vals['to_delete'] = False
        lines_of_rec = self.STRUCT[model].get('LINES_OF_REC', False)
        # if self.LOGLEVEL == 'debug':
        #     self.show_debug(0, model)

        ir_model = self.env[model]
        vals, ext_id, channel_id = self.bind_to_internal(model, vals)
        if not channel_id:
            self.STRUCT = {}
            self.MANAGED_MODELS = {}
            return -6
        # if self.MANAGED_MODELS[channel_id]['IDENTITY'] == 'odoo':
        #     self.set_odoo_model(model, channel_id)
        id = -1
        rec = None
        if 'id' in vals:
            id = vals.pop('id')
            rec = ir_model.search([('id', '=', id)])
            if not rec or rec.id != id:
                _logger.error('ID %d does not exist in %s' %
                              (id, model))
                return -3
            id = rec.id
            self.logmsg(channel_id, '> synchro: found id=%s.%d' % (model, id))
        if id < 0:
            id = self.search4rec(model, vals, ext_id,
                                 constraints, has_active, channel_id)
        if has_state:
            vals, erc = self.set_state_to_draft(model, rec, vals)
            if erc < 0:
                return erc

        self.drop_invalid_fields(model, vals)
        if id > 0:
            try:
                rec = ir_model.browse(id)
                vals = self.drop_protected_fields(rec, vals, model, channel_id)
                if vals:
                    rec.write(vals)
                    self.logmsg(channel_id,
                                '>>> synchro: %s.write(%s)' % (model, vals))
                if lines_of_rec and hasattr(rec, lines_of_rec):
                    for line in rec[lines_of_rec]:
                        if not hasattr(line, 'to_delete'):
                            break
                        line.write({'to_delete': True})
            except BaseException, e:
                _logger.error('%s writing %s ID=%d' %
                              (e, model, id))
                return -2
        else:
            vals = self.set_default_values(model, vals, channel_id)
            if vals:
                try:
                    id = ir_model.create(vals).id
                    self.logmsg(
                        channel_id,
                        '>>> synchro: %d=%s.create(%s)' % (id, model, vals))
                except BaseException, e:
                    _logger.error('%s creating %s' % (e, model))
                    return -1
            else:
                return -7
        return id

    @api.model
    def commit(self, cls, id):
        model = cls.__class__.__name__
        self.logmsg(0, '> %s.commit()' % model)
        self._init_self(model=model, cls=cls)
        has_state = self.STRUCT[model].get('MODEL_STATE', False)
        lines_of_rec = self.STRUCT[model].get('LINES_OF_REC', False)
        model_line =  self.STRUCT[model].get('LINE_MODEL')
        if not has_state and not lines_of_rec and not model_line:
            return -5
        parent_id = self.STRUCT[model_line].get('PARENT_ID')
        if not parent_id:
            return -5
        rec = self.env[model].search([('id', '=', id)])
        if not rec:
            return -3
        rec_2_commit = rec[0]
        ir_model = self.env[model_line]
        if self.STRUCT[model_line].get('MODEL_2DELETE'):
            for rec in ir_model.search([(parent_id, '=', id),
                                        ('to_delete', '=', True)]):
                ir_model.unlink(rec.id)
        return self.set_actual_state(model, rec_2_commit)

    def prefix_bind(self, prefix, data):
        vals = {}
        for name in data:
            vals['%s:%s' % (prefix, name)] = data[name]
        return vals

    @api.multi
    def pull_recs_2_complete(self):
        self._init_self()
        for channel_id in self.MANAGED_MODELS:
            for model in self.MANAGED_MODELS[channel_id]:
                if model <= 'Z':
                    continue
                if not self.STRUCT[model].get('MODEL_WITH_NAME'):
                    continue
                ir_model = self.env[model]
                recs = ir_model.search([('name', 'like', 'Unknown ')])
                for rec in recs:
                    id = False
                    if rec.vg7_id:
                        id = rec.vg7_id
                    else:
                        id = int(rec.name[8:])
                    if not id:
                        continue
                    datas = self.get_counterpart_response(channel_id,
                                                          model,
                                                          id=id)
                    if not datas:
                        continue
                    if not isinstance(datas, (list, tuple)):
                        datas = [datas]
                    for data in datas:
                        if not data:
                            continue
                        ir_model.synchro(self.prefix_bind(
                            self.MANAGED_MODELS[channel_id]['PREFIX'],
                            data))
                        # commit every table to avoid too big transaction
                        self.env.cr.commit()   # pylint: disable=invalid-commit

    @api.multi
    def pull_full_records(self):
        self._init_self()
        for channel_id in self.MANAGED_MODELS:
            model_list = [x.name for x in self.env[
                'synchro.channel.model'].search(
                    [('synchro_channel_id', '=', channel_id)],
                    order='sequence')]
            # for model in self.MANAGED_MODELS[channel_id]:
            for model in model_list:
                if model <= 'Z':
                    continue
                self._init_self(model=model)
                if not self.MANAGED_MODELS[
                        channel_id][model].get('2PULL', False):
                    continue
                ir_model = self.env[model]
                datas = self.get_counterpart_response(channel_id,
                                                      model)
                if not datas:
                    continue
                if not isinstance(datas, (list, tuple)):
                    datas = [datas]
                for data in datas:
                    if not data:
                        continue
                    if 'id' not in data:
                        self.logmsg(channel_id,
                                    'Data received of model %s w/o id' %
                                    model)
                        continue
                    if isinstance(data['id'], (int, long)):
                        id = data['id']
                    else:
                        id = int(data['id'])
                    ext_id = '%s_id' % self.MANAGED_MODELS[
                        channel_id]['IDENTITY']
                    if not ir_model.search([(ext_id, '=', id)]):
                        ir_model.synchro(self.prefix_bind(
                            self.MANAGED_MODELS[channel_id]['PREFIX'],
                            data))
                        # commit every table to avoid too big transaction
                        self.env.cr.commit()   # pylint: disable=invalid-commit


class IrModelField(models.Model):
    _inherit = 'ir.model.fields'

    protect_update = fields.Selection(
        [('0', 'Updatable'),
         ('1', 'If empty'),
         ('2', 'Protected'),],
        string='Protect field against update',
        default='0',
    )

    @api.model_cr_context
    def _auto_init(self):
        res = super(IrModelField, self)._auto_init()

        self._cr.execute("""UPDATE ir_model_fields set protect_update='2'
        where name not like '____id' and model_id in
        (select id from ir_model where model='res.country');
        """)

        self._cr.execute("""UPDATE ir_model_fields set protect_update='2'
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

        self._cr.execute("""UPDATE ir_model_fields set protect_update='2'
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
