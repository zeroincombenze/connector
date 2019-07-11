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
#
import os
import requests
import json
import logging
from odoo import fields, models, api
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

try:
    from unidecode import unidecode
except ImportError as err:
    _logger.debug(err)


class IrModelSynchro(models.Model):
    _name = 'ir.model.synchro'
    _inherit = 'ir.model'

    MAGIC_FIELDS = {'company_id': False,
                    'is_company': True,
    }
    STRUCT = {}
    MANAGED_MODELS = {}
    # MANAGED_MODELS = {
    #     'account.account': 'code',
    #     'account.invoice': 'number',
    #     'account.tax': 'description',
    #     'product.product': 'default_code',
    #     'product.template': 'default_code',
    #     'res.partner': 'name',
    #     'sale.order': 'name',
    # }

    def _build_unique_index(self, model, prefix):
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

    def tnl_2_loc_vat(self, vals, loc_name, ext_ref):
        if len(vals[ext_ref]) == 11 and vals[ext_ref].isdigit():
            return 'IT%s' % vals[ext_ref]
        return vals[ext_ref]

    def tnl_2_loc_upper(self, vals, loc_name, ext_ref):
        return vals[ext_ref].upper()

    def tnl_2_loc_lower(self, vals, loc_name, ext_ref):
        return vals[ext_ref].lower()

    def get_model_structure(self, model, ignore=None):
        ignore = ignore or []
        if self.STRUCT.get(model, {}) and not ignore:
            return
        self.STRUCT[model] = self.STRUCT.get(model, {})
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

    def get_channels(self):
        for channel in self.env['synchro.channel'].search([]):
            if channel.id in self.MANAGED_MODELS:
                continue
            self.MANAGED_MODELS[channel.id] = {}
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

    def get_channel_models(self):
        for rec in self.env['synchro.channel.model'].search([]):
            if rec.synchro_channel_id.id not in self.MANAGED_MODELS:
                continue
            if rec.name not in self.MANAGED_MODELS[
                    rec.synchro_channel_id.id]:
                self.MANAGED_MODELS[
                    rec.synchro_channel_id.id][rec.name] = {}
                self.get_model_structure(rec.name)
            if rec.field_2complete:
                self.MANAGED_MODELS[
                    rec.synchro_channel_id.id][
                        rec.name]['2COMPLETE'] = True
            self.MANAGED_MODELS[
                rec.synchro_channel_id.id][
                    rec.name]['MODEL_KEY'] = rec.field_uname
            self.MANAGED_MODELS[
                rec.synchro_channel_id.id][
                    rec.name]['BIND'] = rec.counterpart_name
            self.get_channel_model_fields(rec)

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
            self.MANAGED_MODELS[channel_id][
                    model]['LOC_FIELDS'][field.name] = field.counterpart_name
            self.MANAGED_MODELS[channel_id][
                    model]['EXT_FIELDS'][field.counterpart_name] = field.name
            if field.apply:
                self.MANAGED_MODELS[channel_id][
                    model]['APPLY'][field.name] = field.apply
            if field.protect:
                self.MANAGED_MODELS[channel_id][
                    model]['PROTECT'][field.name] = field.protect

    @api.model_cr_context
    def _init_self(self, model=None, cls=None):
        if not self.MANAGED_MODELS:
            self.get_channels()
            self.get_channel_models()
        if model:
            self.get_model_structure(model)
        if cls is not None:
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

    def drop_tech_fields(self, rec, vals, model, channel_id):
        for field in vals:
            protect = self.MANAGED_MODELS[
                channel_id][model]['PROTECT'].get(field, 'update')
            if (rec[field] and
                    field in vals and
                    (protect == 'protect' or
                     (protect == 'similar' and
                      isinstance(rec[field], basestring) and
                      self.dim_text(
                          rec[field]) == self.dim_text(vals[field])))):
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

    def _set_journal_id(self, vals):
        if 'journal_id' not in vals:
            journal = self.env['account.invoice']._default_journal()
            if journal:
                vals['journal_id'] = journal[0].id
        return vals

    def _set_account_id(self, vals):
        if 'journal_id' not in vals:
            vals = self._set_journal_id(vals)
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
                    'account.journal'].browse(vals['journal_id'])
                if vals.get('type') in ('in_invoice', 'in_refund'):
                    vals['account_id'] = journal.default_debit_account_id.id
                else:
                    vals['account_id'] = journal.default_credit_account_id.id
        return vals

    def _set_product_uom(self, vals):
        if 'product_uom' not in vals and 'product_id' in vals:
            product = self.env['product.product'].browse(vals['product_id'])
            vals['product_uom'] = product.uom_id.id
        return vals

    def _set_uom_id(self, vals):
        if 'uom_id' not in vals and 'product_id' in vals:
            product = self.env['product.product'].browse(vals['product_id'])
            vals['uom_id'] = product.uom_id.id
        return vals

    def _set_invoice_line_tax_ids(self, vals):
        if 'invoice_line_tax_ids' not in vals and 'product_id' in vals:
            product = self.env['product.product'].browse(vals['product_id'])
            if vals.get('type') in ('in_invoice', 'in_refund'):
                tax = product.supplier_taxes_id
            else:
                tax = product.taxes_id
            if tax:
                vals['invoice_line_tax_ids'] = [(6, 0, [tax.id])]
        return vals

    def get_rec_by_reference(self, model, key_name, value, company_id):
        ir_model = self.env[model]
        where = [(key_name, '=', value)]
        if key_name != 'id' and self.STRUCT[model].get('MODEL_WITH_COMPANY'):
            where.append(('company_id', '=', company_id))
        return ir_model.search(where)

    def bind_foreign_text(self, model, value, is_foreign,
                          channel_id, company_id):
        ir_model = self.env[model]
        if model in self.MANAGED_MODELS[channel_id]:
            key_name = self.MANAGED_MODELS[
                channel_id][model]['MODEL_KEY']
        else:
            key_name = 'name'
        new_value = False
        rec = self.get_rec_by_reference(model, key_name, value, company_id)
        if rec:
            new_value = rec[0].id
        if not new_value and model in self.MANAGED_MODELS[channel_id]:
            vals = {key_name: value}
            if self.STRUCT[model].get('MODEL_WITH_COMPANY'):
                vals['company_id'] = company_id
            new_value = self.synchro(ir_model, vals)
        return new_value

    def bind_foreign_ref(self, model, value, ext_id, is_foreign,
                         channel_id, company_id):
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
                vals['company_id'] = company_id
            new_value = self.synchro(ir_model, vals)
        return new_value

    def get_foreign_value(self, model, channel_id, value,
                         is_foreign, ext_id, company_id, tomany=None):
        if not value:
            return value
        self.get_model_structure(model)
        new_value = False
        if isinstance(value, basestring):
            new_value = self.bind_foreign_text(
                model, value, is_foreign, channel_id, company_id)
            if tomany:
                new_value = [new_value]
        elif isinstance(model, (list, tuple)):
            new_value = []
            for id in value:
                new_value.append(self.bind_foreign_ref(
                    model, id, ext_id, is_foreign, channel_id, company_id))
        else:
            new_value = self.bind_foreign_ref(
                model, value, ext_id, is_foreign, channel_id, company_id)
        return new_value

    def cvt_m2o_value(self, model, name, value,
                      channel_id, ext_id, is_foreign, company_id, format=None):
        relation = self.STRUCT[model][name]['relation']
        if not relation:
            raise RuntimeError('No relation for field %s of %s' % (name,
                                                                   model))
        return self.get_foreign_value(relation, channel_id, value,
                                    is_foreign, ext_id, company_id)

    def cvt_m2m_value(self, model, name, value,
                      channel_id, ext_id, is_foreign, company_id, format=None):
        relation = self.STRUCT[model][name]['relation']
        if not relation:
            raise RuntimeError('No relation for field %s of %s' % (name,
                                                                   model))
        value = self.get_foreign_value(relation, channel_id, value,
                                       is_foreign, ext_id, company_id,
                                       tomany=True)
        if format == 'cmd' and value:
            value = [(6, 0, value)]
        return value

    def cvt_o2m_value(self, model, name, value,
                      channel_id, ext_id, is_foreign, company_id, format=None):
        relation = self.STRUCT[model][name]['relation']
        if not relation:
            raise RuntimeError('No relation for field %s of %s' % (name,
                                                                   model))
        value = self.get_foreign_value(relation, channel_id, value,
                                       is_foreign, ext_id, company_id,
                                       tomany=True)
        if format == 'cmd' and value:
            value = [(6, 0, value)]
        return value

    def bind_to_internal(self, model, vals):

        def search_channel(vals):
            channel_from = prefix1 = prefix2 = False
            for channel_id in self.MANAGED_MODELS:
                if channel_from:
                    break
                prefix1 = '%s_' % self.MANAGED_MODELS[channel_id]['PREFIX']
                prefix2 = '%s:' % self.MANAGED_MODELS[channel_id]['PREFIX']
                for ext_ref in vals:
                    if (ext_ref.startswith(prefix1) or
                            ext_ref.startswith(prefix2)):
                        channel_from = channel_id
                        break
            return channel_from, prefix1, prefix2

        def get_names_from_ref(model, channel_from, vals, ext_ref,
                               prefix1, prefix2):
            if (not ext_ref.startswith(prefix1) and
                    not ext_ref.startswith(prefix2)):
                is_foreign = False
                ext_name = loc_name = ext_ref
                loc_ext_ref = ''
            else:
                is_foreign = True
                ext_name = ext_ref[4:]
                loc_ext_ref = prefix1 + ext_name
                if (model in self.MANAGED_MODELS[channel_from] and
                        ext_name in self.MANAGED_MODELS[
                            channel_from][model]['EXT_FIELDS']):
                    loc_name = self.MANAGED_MODELS[
                        channel_from][model]['EXT_FIELDS'][ext_name]
                else:
                    loc_name = ext_name
            return ext_name, loc_name, is_foreign, loc_ext_ref

        channel_from, prefix1, prefix2 = search_channel(vals)
        if channel_from is False:
            return vals, False, False
        ext_id = '%s_id' % self.MANAGED_MODELS[channel_from]['PREFIX']
        if 'company_id' in vals:
            company_id = vals['company_id']
        else:
            company_id =  self.MANAGED_MODELS[channel_from]['COMPANY_ID']
        for ext_ref in vals.copy():
            ext_name, loc_name, is_foreign, loc_ext_ref = get_names_from_ref(
                model, channel_from, vals, ext_ref, prefix1, prefix2)
            if loc_name not in self.STRUCT[model]:
                _logger.debug(
                        'Field <%s> does not exist in model %s' % (ext_ref,
                                                                   model))
                del vals[ext_ref]
                continue
            if (self.STRUCT[model][loc_name]['ttype'] in ('many2one',
                                                          'integer') and
                    isinstance(vals[ext_ref], basestring) and
                    vals[ext_ref].isdigit()):
                vals[ext_ref] = int(vals[ext_ref])
            if ext_ref == 'company_id':
                continue
            if is_foreign:
                # Field like <vg7_id> with external ID in local DB
                if loc_ext_ref in self.STRUCT[model]:
                    if ext_ref.startswith(prefix2):
                        vals[loc_ext_ref] = vals[ext_ref]
                        del vals[ext_ref]
                    rec = self.get_rec_by_reference(
                        model, loc_ext_ref, vals[loc_ext_ref], company_id)
                    if rec:
                        vals[loc_name] = rec[0][loc_ext_ref]
                        vals['id'] = rec[0].id
                        ext_id = loc_ext_ref
                    continue
                # Counterpart partner can supply both local and both external value
                elif loc_name in vals:
                    del vals[ext_ref]
            if self.STRUCT[model][loc_name]['ttype'] == 'one2many':
                vals[loc_name] = self.cvt_o2m_value(
                    model, loc_name, vals[ext_ref],
                    channel_from, ext_id, is_foreign, company_id, format='cmd')
                if is_foreign or loc_name != ext_name:
                    del vals[ext_ref]
            elif self.STRUCT[model][loc_name]['ttype'] == 'many2many':
                vals[loc_name] = self.cvt_m2m_value(
                    model, loc_name, vals[ext_ref],
                    channel_from, ext_id, is_foreign, company_id, format='cmd')
                if is_foreign or loc_name != ext_name:
                    del vals[ext_ref]
            elif self.STRUCT[model][loc_name]['ttype'] == 'many2one':
                vals[loc_name] = self.cvt_m2o_value(
                    model, loc_name, vals[ext_ref],
                    channel_from, ext_id, is_foreign, company_id, format='cmd')
                if is_foreign or loc_name != ext_name:
                    del vals[ext_ref]
            elif is_foreign:
                apply = 'tnl_2_loc_%s' % self.MANAGED_MODELS[
                    channel_from][model]['APPLY'].get(loc_name, '')
                if hasattr(self, apply):
                    vals[loc_name] = getattr(self, apply)(vals,
                                                          loc_name,
                                                          ext_ref)
                else:
                    vals[loc_name] = vals[ext_ref]
                del vals[ext_ref]
            if (loc_name in vals and
                    vals[loc_name] is False and
                    self.STRUCT[model][loc_name]['ttype'] != 'boolean'):
                del vals[loc_name]
        if (model == 'product.product' and
                vals.get('name') and
                self.MANAGED_MODELS[channel_from].get('NO_VARIANTS')):
            tmpl_vals = vals.copy()
            id = self.synchro(self.env['product.template'], tmpl_vals)
            if id > 0:
                vals['product_tmpl_id'] = id
        return vals, ext_id, channel_from

    def search4rec(self, ir_model, vals, ext_id,
                   skeys, constraints, has_active, channel_id):
        company_id =  self.MANAGED_MODELS[channel_id]['COMPANY_ID']
        id = -1
        for keys in skeys:
            where = []
            for key in keys:
                if (key not in vals and
                        key == 'dim_name' and
                        vals.get('name')):
                    where.append(('dim_name',
                                  '=',
                                  self.dim_text(vals['name'])))
                elif key not in vals and key in self.MAGIC_FIELDS:
                    if key == 'company_id':
                        where.append((key, '=', company_id))
                    elif self.MAGIC_FIELDS[key]:
                        where.append((key, '=', self.MAGIC_FIELDS[key]))
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
                    _logger.debug(
                        '> synchro: found id=%d (%s)' % (id, where))
                    break
        if id < 0 and ext_id in vals:
            rec = ir_model.search(
                [('name', '=', 'Unknown %d' % vals[ext_id])])
            if rec:
                id = rec[0].id
                _logger.debug(
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
                   self.MANAGED_MODELS[channel_id]['CLIENT_KEY'] }
        response = requests.get(url, headers=headers)
        if response:
            datas = response.json()
            return datas
        return {}

    def get_counterpart_response(self, channel_id, model, id=False):
        identity = self.MANAGED_MODELS[channel_id]['IDENTITY']
        if identity == 'odoo':
            return self.get_odoo_response(channel_id, model, id)
        elif identity == 'vg7':
            return self.get_vg7_response(channel_id, model, id)

    @api.model
    def synchro(self, cls, vals, skeys=None, constraints=None,
                keep=None, default=None):
        model = cls.__class__.__name__
        self._init_self(model=model, cls=cls)
        skeys = skeys or cls.SKEYS
        constraints = constraints or cls.CONTRAINTS
        keep = keep or cls.KEEP
        default = default or cls.DEFAULT
        has_dim_text = self.STRUCT[model].get('MODEL_WITH_DIMNAME', False)
        has_active = self.STRUCT[model].get('MODEL_WITH_ACTIVE', False) 
        has_state = self.STRUCT[model].get('MODEL_STATE', False)
        has_2delete = self.STRUCT[model].get('MODEL_2DELETE', False)
        if has_2delete:
            default['to_delete'] = False
        lines_of_rec = self.STRUCT[model].get('LINES_OF_REC', False)
        _logger.debug('synchro(%s,%s)' % (model, vals))

        ir_model = self.env[model]
        vals, ext_id, channel_id = self.bind_to_internal(model, vals)
        self.drop_invalid_fields(model, vals)
        id = -1
        rec = None
        if 'id' in vals:
            id = vals.pop('id')
            rec = ir_model.search([('id', '=', id)])
            if not rec or rec.id != id:
                _logger.error('ID %d does not exist in %s' %
                              id, model)
                return -3
            id = rec.id
            _logger.debug('> synchro: found id=%s.%d' % (model, id))
        if id < 0:
            id = self.search4rec(ir_model, vals, ext_id,
                                 skeys, constraints, has_active, channel_id)
        for field in default:
            if not vals.get(field) and field in default:
                if hasattr(self, '_set_%s' % field):
                    vals = getattr(self, '_set_%s' % field)(vals)
                else:
                    vals[field] = default[field]
        if has_state:
            vals, erc = self.set_state_to_draft(model, rec, vals)
            if erc < 0:
                return erc

        if id > 0:
            try:
                rec = ir_model.browse(id)
                rec.write(self.drop_tech_fields(rec, vals, model, channel_id))
                _logger.debug('> synchro: %s.write(%s)' % (model, vals))
                if lines_of_rec and lines_of_rec in rec:
                    for line in rec[lines_of_rec]:
                        line.to_delete = True
            except BaseException, e:
                _logger.error('%s writing %s ID=%d' %
                              (e, model, id))
                return -2
        else:
            try:
                id = ir_model.create(vals).id
                _logger.debug(
                    '> synchro: %d=%s.create(%s)' % (id, model, vals))
            except BaseException, e:
                _logger.error('%s creating %s' % (e, model))
                return -1
        return id

    @api.model
    def commit(self, cls, id):
        model = cls.__class__.__name__
        self._init_self(model=model, cls=cls)
        has_state = self.STRUCT[model].get('MODEL_STATE', False)
        lines_of_rec = self.STRUCT[model].get('LINES_OF_REC', False)
        model_line =  self.STRUCT[model].get('LINE_MODEL')
        _logger.debug('commit(%s)' % model)
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
                if not self.STRUCT[model]['MODEL_WITH_NAME']:
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
                    if not isinstance(datas, (list, tuple)):
                        datas = [datas]
                    for data in datas:
                        ir_model.synchro(self.prefix_bind(
                            self.MANAGED_MODELS[channel_id]['PREFIX'],
                            data))
                        self.env.cr.commit()

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
                self._init_self(model=model)
                if not self.MANAGED_MODELS[
                        channel_id][model].get('2COMPLETE', False):
                    continue
                ir_model = self.env[model]
                datas = self.get_counterpart_response(channel_id,
                                                      model)
                if not isinstance(datas, (list, tuple)):
                    datas = [datas]
                for data in datas:
                    id = int(data['id'])
                    if not ir_model.search([('id', '=', id)]):
                        ir_model.synchro(self.prefix_bind(
                            self.MANAGED_MODELS[channel_id]['PREFIX'],
                            data))
                        self.env.cr.commit()


class IrModelField(models.Model):
    _inherit = 'ir.model.fields'

    protect_update = fields.Selection(
        [('update', 'Updatable'),
         ('similar', 'If similar'),
         ('protect', 'Protected'),],
        string='Protect field against update',
        default='update',
    )
