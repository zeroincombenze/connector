# -*- coding: utf-8 -*-
# Copyright 2019 Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
# Return code:
# -1: error creating record
# -2: error writing record
# -3: record with passed id does not exist
# -4: unmodificable record
#
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
    MANAGED_MODELS = {
        'account.account': 'code',
        'account.invoice': 'number',
        'account.tax': 'description',
        'product.product': 'default_code',
        'product.template': 'default_code',
        'res.partner': 'name',
        'sale.order': 'name',
    }

    def _build_unique_index(self, model):
        if isinstance(model, (list, tuple)):
            table = model[0].replace('.', '_')
        else:
            table = model.replace('.', '_')
        index_name = '%s_unique_vg7' % table
        self._cr.execute(
            "SELECT indexname FROM pg_indexes WHERE indexname = '%s'" %
            index_name
        )
        if not self._cr.fetchone():
            self._cr.execute(
                "CREATE UNIQUE INDEX %s on %s (vg7_id) where vg7_id<>0" %
                (index_name, table)
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

    def drop_tech_fields(self, rec, vals, keep):
        for field in keep:
            if (rec[field] and
                field in vals and
                    isinstance(rec[field], basestring) and
                        self.dim_text(
                            rec[field]) == self.dim_text(
                                vals[field])):
                del vals[field]
        return vals

    def set_current_state(self, model, rec, vals):
        if 'state' in vals:
            vals['original_state'] = vals['state']
        elif rec:
            vals['original_state'] = rec.state
        if model == 'account.invoice':
            if rec:
                if rec.state == 'paid':
                    return vals, -4
                if rec.state == 'open':
                    rec.action_invoice_cancel()
                if rec.state == 'cancel':
                    rec.action_invoice_draft()
            vals['state'] = 'draft'
        elif model == 'sale.order':
            if rec:
                pass
            vals['state'] = 'draft'
        return vals, 0

    def cvt_m2o_value(self, model, name, value, format=None):
        relation = self.STRUCT[model][name]['relation']
        if value:
            if not relation:
                raise RuntimeError('No relation for field %s of %s' % (name,
                                                                       model))
            self.get_model_structure(relation)
            ir_model = self.env[relation]
            new_value = False
            if (isinstance(value, basestring) and
                    relation in self.MANAGED_MODELS):
                rec = ir_model.search([(self.MANAGED_MODELS[relation],
                                        '=',
                                        value)])
            else:
                rec = ir_model.search([('vg7_id', '=', value)])
            if rec:
                new_value = rec[0].id
            elif relation in self.MANAGED_MODELS:
                if isinstance(value, basestring):
                    new_value = self.synchro(ir_model, {
                        'name': value})
                else:
                    new_value = self.synchro(ir_model, {
                        'vg7_id': value,
                        'name': 'Unknown %d' % value})
            value = new_value
        return value

    def cvt_m2m_value(self, model, name, value, format=None):
        relation = self.STRUCT[model][name]['relation']
        if value:
            if not relation:
                raise RuntimeError('No relation for field %s of %s' % (name,
                                                                       model))
            self.get_model_structure(relation)
            ir_model = self.env[relation]
            new_value = []
            for id in value:
                if (isinstance(value, basestring) and
                        relation in self.MANAGED_MODELS):
                    rec = ir_model.search([(self.MANAGED_MODELS[relation],
                                            '=',
                                            value)])
                else:
                    rec = ir_model.search([('vg7_id', '=', value)])
                if rec:
                    new_value.append(rec[0].id)
                elif relation in self.MANAGED_MODELS:
                    if isinstance(value, basestring):
                        new_value = self.synchro(ir_model, {
                            'name': value})
                    else:
                        new_value = self.synchro(ir_model, {
                            'vg7_id': value,
                            'name': 'Unknown %d' % value})
            value = new_value if new_value else False
        if format == 'cmd' and value:
            value = [(6, 0, value)]
        return value

    def cvt_o2m_value(self, model, name, value, format=None):
        relation = self.STRUCT[model][name]['relation']
        if value:
            if not relation:
                raise RuntimeError('No relation for field %s of %s' % (name,
                                                                       model))
            self.get_model_structure(relation)
            ir_model = self.env[relation]
            new_value = []
            for id in value:
                if (isinstance(value, basestring) and
                        relation in self.MANAGED_MODELS):
                    rec = ir_model.search([(self.MANAGED_MODELS[relation],
                                            '=',
                                            value)])
                else:
                    rec = ir_model.search([('vg7_id', '=', value)])
                if rec:
                    new_value.append(rec[0].id)
                elif relation in self.MANAGED_MODELS:
                    if isinstance(value, basestring):
                        new_value = self.synchro(ir_model, {
                            'name': value})
                    else:
                        new_value = self.synchro(ir_model, {
                            'vg7_id': value,
                            'name': 'Unknown %d' % value})
            value = new_value if new_value else False
        if format == 'cmd' and value:
            value = [(6, 0, value)]
        return value

    def tnl_values(self, model, vals):
        ir_model = self.env[model]
        for vg7_name in vals.copy():
            if not vg7_name.startswith('vg7_'):
                continue
            name = vg7_name[4:]
            if name in vals:
                del vals[vg7_name]
                continue
            if vg7_name == 'vg7_id':
                rec = ir_model.search([(vg7_name, '=', vals[vg7_name])])
                if rec:
                    vals['id'] = rec[0].id
                    continue
            elif self.STRUCT[model][name]['ttype'] == 'one2many':
                vals[name] = self.cvt_o2m_value(model, name, vals[vg7_name],
                                                format='cmd')
                del vals[vg7_name]
            elif self.STRUCT[model][name]['ttype'] == 'many2many':
                vals[name] = self.cvt_m2m_value(model, name, vals[vg7_name],
                                                format='cmd')
                del vals[vg7_name]
            elif self.STRUCT[model][name]['ttype'] in ('many2one'):
                vals[name] = self.cvt_m2o_value(model, name, vals[vg7_name],
                                                format='cmd')
                del vals[vg7_name]
            if (name in vals and
                    vals[name] is False and
                    self.STRUCT[model][name]['ttype'] != 'boolean'):
                del vals[name]
        return vals

    def _set_journal_id(self, vals):
        if not 'journal_id' in vals:
            journal = self.env['account.invoice']._default_journal()
            if journal:
                vals['journal_id'] = journal[0].id
        return vals

    def _set_account_id(self, vals):
        if not 'journal_id' in vals:
            vals = self._set_journal_id(vals)
        if not 'account_id' in vals and 'product_id' in vals:
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
        if not 'product_uom' in vals and 'product_id' in vals:
            product = self.env['product.product'].browse(vals['product_id'])
            vals['product_uom'] = product.uom_id.id
        return vals

    def _set_uom_id(self, vals):
        if not 'uom_id' in vals and 'product_id' in vals:
            product = self.env['product.product'].browse(vals['product_id'])
            vals['uom_id'] = product.uom_id.id
        return vals

    def search4rec(self, ir_model, vals, skeys, constraints, has_active):
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
                    if self.MAGIC_FIELDS[key]:
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
                where.append(('vg7_id', '=', False))
                rec = ir_model.search(where)
                if not rec and has_active:
                    where.append(('active','=',False))
                    rec = ir_model.search(where)
                if rec:
                    id = rec[0].id
                    _logger.debug(
                        '> synchro: found id=%d (%s)' % (id, where))
                    break
        if id < 0 and 'vg7_id' in vals:
            rec = ir_model.search(
                [('name', '=', 'Unknown %d' % vals['vg7_id'])])
            if rec:
                id = rec[0].id
                _logger.debug(
                    '> synchro: found unknown id=%d' % id)
        return id

    @api.model
    def synchro(self, cls, vals, skeys=None, constraints=None,
                keep=None, default=None):
        # import pdb
        # pdb.set_trace()
        model = cls.__class__.__name__
        self.get_model_structure(model)
        model_line = '%s.line' % model
        skeys = skeys or cls.SKEYS
        constraints = constraints or cls.CONTRAINTS
        keep = keep or cls.KEEP
        default = default or cls.DEFAULT
        has_dim_text = hasattr(cls,'dim_text')
        has_active = hasattr(cls,'active')
        has_state = hasattr(cls,'original_state')
        if hasattr(cls,'to_delete'):
            default['to_delete'] = False
        has_2delete = hasattr(cls,'to_delete')
        lines_of_rec = False if not hasattr(cls,'LINES') else cls.LINES
        _logger.debug('synchro(%s,%s)' % (model, vals))

        ir_model = self.env[model]
        vals = self.tnl_values(model, vals)
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
            _logger.debug('> synchro: found id=%d' % id)
        if id < 0:
            id = self.search4rec(ir_model, vals,
                                 skeys, constraints, has_active)

        for field in default:
            if not vals.get(field) and field in default:
                if hasattr(self, '_set_%s' % field):
                    vals = getattr(self, '_set_%s' % field)(vals)
                else:
                    vals[field] = default[field]
        if has_state:
            vals, erc = self.set_current_state(model, rec, vals)
            if erc < 0:
                return erc

        if id > 0:
            try:
                rec = ir_model.browse(id)
                rec.write(self.drop_tech_fields(rec, vals, keep))
                _logger.debug('> synchro: write(%s)' % vals)
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
                _logger.debug('> synchro: %d=create(%s)' % (id, vals))
            except BaseException, e:
                _logger.error('%s creating %s' % (e, model))
                return -1
        return id

    @api.model
    def commit(self, cls, id):
        model = cls.__class__.__name__
        has_state = hasattr(cls,'original_state')
        lines_of_rec = False if not hasattr(cls,'LINES') else cls.LINES
        parent_id = False if not hasattr(cls,'PARENT_ID') else cls.PARENT_ID
        _logger.debug('commit(%s)' % model)
        if not has_state and not lines_of_rec:
            return
        rec = self.env[model].search([('id', '=', id)])
        if not rec:
            return -3
        rec_2_commit = rec[0]
        self.get_model_structure(model)
        model_line = '%s.line' % model
        ir_model = self.env[model_line]
        for rec in ir_model.search([(parent_id, '=', id),
                                    ('to_delete', '=', True)]):
            ir_model.unlink(rec.id)
        if model == 'sale.order':
            rec_2_commit._compute_tax_id()
        return id
