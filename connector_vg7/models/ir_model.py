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
from datetime import datetime, timedelta
import requests
# from lxml import etree
import logging
from odoo import fields, models, api
# from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)
try:
    from python_plus import unicodes
except ImportError as err:
    _logger.debug(err)
try:
    from unidecode import unidecode
except ImportError as err:
    _logger.debug(err)
try:
    from os0 import os0
except ImportError as err:
    _logger.debug(err)
# import pdb


class IrModelSynchro(models.Model):
    _name = 'ir.model.synchro'
    _inherit = 'ir.model'

    CONTEXT_FIELDS = {
        'company_id': False,
        'country_id': False,
        'is_company': True,
    }
    LOGLEVEL = 'debug'
    SKEYS = {
        'res.country': (['code'], ['name']),
        'res.country.state': (['code', 'country_id'], ['name'], ['dim_name']),
        'res.partner': (['vat', 'fiscalcode', 'is_company', 'type'],
                        ['vat', 'fiscalcode', 'is_company'],
                        ['rea_code'],
                        ['vat', 'name', 'is_company', 'type'],
                        ['fiscalcode', 'type'],
                        ['vat', 'is_company'],
                        ['name', 'is_company'],
                        ['vat'],
                        ['name'],
                        ['dim_name']),
        'res.company': (['vat'],),
        'account.account': (['code', 'company_id'],
                            ['name', 'company_id'],
                            ['dim_name', 'company_id']),
        'account.account.type': (['type'], ['name'], ['dim_name']),
        'account.tax': (['description'], ['name'], ['dim_name'],),
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

    def tnl_2_loc_set_value(self, vals, loc_name, ext_ref, default=None):
        if loc_name not in vals and default:
            vals[loc_name] = default
        return vals

    def tnl_2_loc_upper(self, vals, loc_name, ext_ref, default=None):
        if isinstance(vals[ext_ref], basestring):
            vals[loc_name] = vals[ext_ref].upper()
        else:
            vals[loc_name] = vals[ext_ref]
        return vals

    def tnl_2_loc_lower(self, vals, loc_name, ext_ref, default=None):
        if isinstance(vals[ext_ref], basestring):
            vals[loc_name] = vals[ext_ref].lower()
        else:
            vals[loc_name] = vals[ext_ref]
        return vals

    def tnl_2_loc_bool(self, vals, loc_name, ext_ref, default=None):
        vals[loc_name] = os0.str2bool(vals.get(ext_ref), False)
        return vals

    def tnl_2_loc_not(self, vals, loc_name, ext_ref, default=None):
        vals[loc_name] = not os0.str2bool(vals.get(ext_ref), True)
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
        if (isinstance(vals[ext_ref], basestring) and
                len(vals[ext_ref]) == 11 and
                vals[ext_ref].isdigit()):
            vals[loc_name] = 'IT%s' % vals[ext_ref]
        else:
            vals[loc_name] = vals[ext_ref]
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

    def tnl_2_loc_agents(self, vals, loc_name, ext_ref, default=None):
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
        if partner.agents:
            line_agents_data = _prepare_line_agents_data(partner)
            if line_agents_data:
                vals[loc_name] = [
                    (0, 0,
                     line_agent_data) for line_agent_data in line_agents_data]
        return vals

    def tnl_2_loc_partner_info(self, vals, loc_name, ext_ref, default=None):
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

    def tnl_2_loc_company_info(self, vals, loc_name, ext_ref, default=None):
        if loc_name in vals:
            return vals
        company_id = vals.get('company_id')
        if not company_id:
            return vals
        company = self.env[
                'res.company'].browse(company_id)
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

    def drop_fields(self, model, vals, to_delete):
        for name in to_delete:
            if isinstance(vals, (list, tuple)):
                del vals[vals.index(name)]
            else:
                del vals[name]
        return vals

    def drop_invalid_fields(self, model, vals):
        cache = self.env['ir.model.synchro.cache']
        if isinstance(vals, (list, tuple)):
            to_delete = list(set(vals) - set(
                cache.get_struct_attr(model).keys()))
        else:
            to_delete = list(set(vals.keys()) - set(
                cache.get_struct_attr(model).keys()))
        return self.drop_fields(model, vals, to_delete)

    def drop_protected_fields(self, rec, vals, model, channel_id):
        cache = self.env['ir.model.synchro.cache']
        for field in vals.copy():
            protect = max(
                int(cache.get_struct_model_field_attr(
                    model, field, 'protect', default='0')),
                int(cache.get_model_field_attr(
                    channel_id, model, field, 'PROTECT', default='0')))
            if (protect == 3 or
                    (protect == 2 and rec[field]) or
                    (protect == 1 and not vals[field])):
                del vals[field]
            elif isinstance(vals[field], (basestring, int, long, bool)):
                if ((cache.get_struct_model_field_attr(
                    model, field, 'ttype') == 'many2one' and vals[
                        field] == rec[field].id) or
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
        return vals, 0

    def set_actual_state(self, model, rec):
        if not rec:
            return -3
        cache = self.env['ir.model.synchro.cache']
        if model == 'account.invoice':
            rec.compute_taxes()
            # rec.write({})
            if rec.state == rec.original_state:
                return rec.id
            elif rec.state != 'draft':
                return -4
            elif rec.original_state == 'open':
                rec.action_invoice_open()
            elif rec.original_state == 'cancel':
                rec.action_invoice_cancel()
        elif model == 'sale.order':
            # rec.write({})
            if rec.state == rec.original_state:
                return rec.id
            elif rec.state != 'draft':
                return -4
            elif rec.original_state == 'sale':
                rec._compute_tax_id()
                if cache.get_struct_model_attr('sale.order.line', 'agents'):
                    rec._compute_commission_total()
                rec.action_confirm()
            elif rec.original_state == 'cancel':
                rec.action_cancel()
        return rec.id

    def create_new_ref(self, model, key_name, value, ctx):
        cache = self.env['ir.model.synchro.cache']
        ir_model = self.env[model]
        vals = {key_name: value}
        if (key_name != 'company_id' and
                cache.get_struct_model_attr(model, 'MODEL_WITH_COMPANY') and
                ctx.get('company_id')):
            vals['company_id'] = ctx['company_id']
        if (key_name != 'country_id' and
                cache.get_struct_model_attr(model, 'MODEL_WITH_COUNTRY') and
                ctx.get('country_id')):
            vals['country_id'] = ctx['country_id']
        if (key_name != 'name' and
                cache.get_struct_model_attr(model, 'MODEL_WITH_NAME')):
            if isinstance(value, (int, long)):
                vals['name'] = 'Unknown %d' % value
            else:
                vals['name'] = '%s=%s' % (key_name, value)
        new_value = self.synchro(ir_model, vals)
        if new_value <= 0:
            if key_name == 'company_id' and ctx.get('company_id'):
                new_value = ctx['company_id']
            elif key_name == 'country_id' and ctx.get('country_id'):
                new_value = ctx['country_id']
            else:
                new_value = False
        return new_value

    def get_rec_by_reference(self, model, key_name, value, ctx, mode=None):
        mode = mode or '='
        self.logmsg(1, 'get_rec_by_reference(%s,%s %s %s)' % (
                    model, key_name, mode, value))
        cache = self.env['ir.model.synchro.cache']
        ir_model = self.env[model]
        if mode == 'tnl':
            translation_model = self.env['synchro.channel.domain.translation']
            where = [('model', '=',  model),
                     ('key', '=', key_name),
                     ('ext_value', 'ilike', self.dim_text(value))]
            rec = translation_model.search(where)
            if not rec:
                return rec
            value = rec[0].odoo_value
            mode = 'ilike'
        where = [(key_name, mode, value)]
        if model not in ('res.partner', 'product.product', 'product.template'):
            if (key_name != 'id' and ctx.get('company_id') and
                    cache.get_struct_model_attr(model, 'MODEL_WITH_COMPANY')):
                where.append(('company_id', '=', ctx['company_id']))
        if (key_name != 'id' and ctx.get('country_id') and
                cache.get_struct_model_attr(model, 'MODEL_WITH_COUNTRY')):
            where.append(('country_id', '=', ctx['country_id']))
        rec = ir_model.search(where)
        if not rec and mode != 'tnl' and isinstance(value, basestring):
            rec = self.get_rec_by_reference(model, key_name, value, ctx,
                                            mode='tnl')
        if not rec:
            if mode == '=' and key_name == 'name':
                return self.get_rec_by_reference(model, key_name, value, ctx,
                                                 mode='ilike')
            elif key_name == 'code' and cache.get_struct_model_attr(
                    model, 'MODEL_WITH_NAME'):
                return self.get_rec_by_reference(model, 'name', value, ctx,
                                                 mode=mode)
        return rec

    def bind_foreign_text(self, model, value, is_foreign, channel_id, ctx):
        self.logmsg(channel_id, 'bind_foreign_text(%s,%s,%s)' % (
                    model, value, is_foreign))
        cache = self.env['ir.model.synchro.cache']
        if value.isdigit():
            return int(value)
        # ir_model = self.env[model]
        if cache.get_attr(channel_id, model):
            key_name = cache.get_model_attr(channel_id, model, 'MODEL_KEY')
        else:
            key_name = 'name'
        new_value = False
        rec = self.get_rec_by_reference(model, key_name, value, ctx)
        if rec:
            new_value = rec[0].id
        if not new_value and cache.get_attr(channel_id, model):
            new_value = self.create_new_ref(model, key_name, value, ctx)
        return new_value

    def bind_foreign_ref(self, model, value, ext_id, is_foreign,
                         channel_id, ctx):
        self.logmsg(channel_id, 'bind_foreign_ref(%s,%s,%s,%s)' % (
                    model, value, ext_id, is_foreign))
        cache = self.env['ir.model.synchro.cache']
        new_value = False
        ir_model = self.env[model]
        if is_foreign:
            rec = ir_model.search([(ext_id, '=', value)])
        else:
            new_value = value
            rec = False
        if rec:
            new_value = rec[0].id
        if not new_value and cache.get_attr(channel_id, model):
            new_value = self.create_new_ref(model, 'ext_id', value, ctx)
        return new_value

    def get_foreign_value(self, model, channel_id, value,
                          ext_id, is_foreign, ctx, tomany=None):
        self.logmsg(channel_id, 'get_foreign_value(%s,%s,%s,%s)' % (
                    model, value, ext_id, is_foreign))
        if not value:
            return value
        cache = self.env['ir.model.synchro.cache']
        cache.setup_model_structure(model)
        cache.setup_models_in_channels(model)
        new_value = False
        if isinstance(value, basestring):
            new_value = self.bind_foreign_text(
                model, value, is_foreign, channel_id, ctx)
            if tomany and new_value:
                new_value = [new_value]
        elif isinstance(model, (list, tuple)):
            new_value = []
            for id in value:
                new_id = self.bind_foreign_ref(
                    model, id, ext_id, is_foreign, channel_id, ctx)
                if new_id:
                    new_value.append(new_id)
        else:
            new_value = self.bind_foreign_ref(
                model, value, ext_id, is_foreign, channel_id, ctx)
        return new_value

    def cvt_m2o_value(self, model, name, value,
                      channel_id, ext_id, is_foreign, ctx, format=None):
        cache = self.env['ir.model.synchro.cache']
        relation = cache.get_struct_model_field_attr(model, name, 'relation')
        if not relation:
            raise RuntimeError('No relation for field %s of %s' % (name,
                                                                   model))
        return self.get_foreign_value(relation, channel_id, value,
                                      ext_id, is_foreign, ctx)

    def cvt_m2m_value(self, model, name, value,
                      channel_id, ext_id, is_foreign, ctx, format=None):
        cache = self.env['ir.model.synchro.cache']
        relation = cache.get_struct_model_field_attr(model, name, 'relation')
        if not relation:
            raise RuntimeError('No relation for field %s of %s' % (name,
                                                                   model))
        value = self.get_foreign_value(relation, channel_id, value,
                                       ext_id, is_foreign, ctx,
                                       tomany=True)
        if format == 'cmd' and value:
            value = [(6, 0, value)]
        return value

    def cvt_o2m_value(self, model, name, value,
                      channel_id, ext_id, is_foreign, ctx, format=None):
        cache = self.env['ir.model.synchro.cache']
        relation = cache.get_struct_model_field_attr(model, name, 'relation')
        if not relation:
            raise RuntimeError('No relation for field %s of %s' % (name,
                                                                   model))
        value = self.get_foreign_value(relation, channel_id, value,
                                       ext_id, is_foreign, ctx,
                                       tomany=True)
        if format == 'cmd' and value:
            value = [(6, 0, value)]
        return value

    def names_from_ref(self, model, channel_from, vals, ext_ref,
                       prefix1, prefix2):
        cache = self.env['ir.model.synchro.cache']
        if ext_ref.startswith(prefix1):
            # Case #1 - field like vg7_oder_id: name is odoo but value id
            #           is of counterpart ref
            is_foreign = True
            loc_name = ext_ref[4:]
            loc_ext_ref = ext_ref
            if loc_name == 'id':
                loc_name = ext_name = loc_ext_ref
            else:
                ext_name = cache.get_model_field_attr(
                    channel_from, model, loc_name, 'LOC_FIELDS', default='')
                if ext_name.startswith('.'):
                        ext_name = ''
        elif ext_ref.startswith(prefix2):
            # Case #2 - field like vg7:oder_id: both name and value are
            #           of counterpart refs
            is_foreign = True
            ext_name = ext_ref[4:]
            loc_ext_ref = prefix1 + ext_name
            loc_name = cache.get_model_field_attr(
                channel_from, model, ext_name, 'EXT_FIELDS', default='')
            if loc_name.startswith('.'):
                loc_name = ''
        else:
            # Case #3 - field and value are Odoo
            is_foreign = False
            ext_name = loc_name = ext_ref
            loc_ext_ref = ''
        return ext_name, loc_name, is_foreign, loc_ext_ref

    def get_default_n_apply(self, model, channel_from, loc_name, ext_name,
                            is_foreign, ttype=None):
        cache = self.env['ir.model.synchro.cache']
        if not cache.get_attr(channel_from, model):
            return '', ''
        default = cache.get_model_field_attr(
            channel_from, model, loc_name or '.%s' % ext_name, 'APPLY',
            default='')
        if default.endswith('()'):
            if default == 'not()' and not is_foreign:
                apply = ''
            else:
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
            cache = self.env['ir.model.synchro.cache']
            odoo_channel = channel_from = prefix1 = prefix2 = False
            for channel_id in cache.get_channel_list():
                if channel_from:
                    break
                prefix1 = '%s_' % cache.get_attr(channel_id, 'PREFIX')
                prefix2 = '%s:' % cache.get_attr(channel_id, 'PREFIX')
                if cache.get_attr(channel_id, 'IDENTITY') == 'odoo':
                    odoo_channel = channel_id
                for ext_ref in vals:
                    if (ext_ref.startswith(prefix1) or
                            ext_ref.startswith(prefix2)):
                        channel_from = channel_id
                        break
            if not channel_from and odoo_channel is not False:
                channel_from = odoo_channel
                prefix1 = '%s_' % cache.get_attr(channel_id, 'PREFIX')
                prefix2 = '%s:' % cache.get_attr(channel_id, 'PREFIX')
            return channel_from, prefix1, prefix2

        def do_apply(channel_from, model, vals, loc_name, ext_name, ext_ref,
                     apply, default, is_foreign):
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
            return vals

        def rm_ext_value(vals, loc_name, ext_name, ext_ref, is_foreign):
            if (is_foreign or loc_name != ext_name) and ext_ref in vals:
                if loc_name not in vals:
                    vals[loc_name] = vals[ext_ref]
                del vals[ext_ref]
            return vals

        def do_apply_n_clean(channel_from, model, vals, loc_name, ext_name,
                             ext_ref, apply, default, is_foreign):
            vals = do_apply(channel_from, model, vals, loc_name, ext_name,
                            ext_ref, apply, default, is_foreign)
            vals = rm_ext_value(vals, loc_name, ext_name, ext_ref, is_foreign)
            return vals

        def process_fields(channel_from, model, vals, ext_id, ctx,
                           field_list=None, excl_list=None):
            cache = self.env['ir.model.synchro.cache']
            prefix1 = '%s_' % cache.get_attr(channel_from, 'PREFIX')
            prefix2 = '%s:' % cache.get_attr(channel_from, 'PREFIX')
            for ext_ref in vals.copy():
                ext_name, loc_name, is_foreign, loc_ext_ref = \
                    self.names_from_ref(model, channel_from, vals,
                                        ext_ref, prefix1, prefix2)
                default, apply = self.get_default_n_apply(
                    model, channel_from, loc_name, ext_name, is_foreign,
                    ttype=cache.get_struct_model_field_attr(
                        model, ext_name, 'ttype'))
                if not loc_name or not cache.get_struct_model_attr(model,
                                                                   loc_name):
                    if is_foreign and hasattr(self, apply):
                        vals = do_apply(channel_from, model, vals,
                                        loc_name, ext_name, ext_ref,
                                        apply, default, is_foreign)
                    else:
                        self.logmsg(
                            channel_from,
                            'Field <%s> does not exist in model %s' % (ext_ref,
                                                                       model))
                    vals = rm_ext_value(vals, loc_name, ext_name, ext_ref,
                                        is_foreign)
                    continue
                if (cache.get_struct_model_field_attr(
                        model, loc_name, 'ttype') in ('many2one',
                                                      'integer') and
                        isinstance(vals[ext_ref], basestring) and
                        vals[ext_ref].isdigit()):
                    vals[ext_ref] = int(vals[ext_ref])
                elif (cache.get_struct_model_field_attr(
                        model, loc_name, 'ttype') == 'boolean' and
                        isinstance(vals[ext_ref], basestring)):
                    vals[ext_ref] = os0.str2bool(vals[ext_ref], True)
                if ((field_list and loc_name not in field_list) or
                        (excl_list and loc_name in excl_list)):
                    continue
                if is_foreign:
                    # Field like <vg7_id> with external ID in local DB
                    if loc_ext_ref in cache.get_struct_attr(model):
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
                    # If counterpart partner supplies both
                    # local and external values, just process local value
                    elif loc_name in vals:
                        del vals[ext_ref]
                        continue
                if cache.get_struct_model_field_attr(
                        model, loc_name, 'ttype') == 'one2many':
                    vals[loc_name] = self.cvt_o2m_value(
                        model, loc_name, vals[ext_ref],
                        channel_from, ext_id, is_foreign, ctx,
                        format='cmd')
                elif cache.get_struct_model_field_attr(
                        model, loc_name, 'ttype') == 'many2many':
                    vals[loc_name] = self.cvt_m2m_value(
                        model, loc_name, vals[ext_ref],
                        channel_from, ext_id, is_foreign, ctx,
                        format='cmd')
                elif cache.get_struct_model_field_attr(
                        model, loc_name, 'ttype') == 'many2one':
                    vals[loc_name] = self.cvt_m2o_value(
                        model, loc_name, vals[ext_ref],
                        channel_from, ext_id, is_foreign, ctx,
                        format='cmd')
                vals = do_apply_n_clean(channel_from, model, vals,
                                        loc_name, ext_name, ext_ref,
                                        apply, default, is_foreign)
                if (loc_name in vals and
                        vals[loc_name] is False and
                        cache.get_struct_model_field_attr(
                            model, loc_name, 'ttype') != 'boolean'):
                    del vals[loc_name]

            for loc_name in ctx:
                if (loc_name not in vals and
                        loc_name in cache.get_struct_attr(model)):
                    if (loc_name != 'company_id' or
                            model not in ('res.partner',
                                          'product.product',
                                          'product.template')):
                        vals[loc_name] = ctx[loc_name]
            return vals

        channel_from, prefix1, prefix2 = search_4_channel(vals)
        if channel_from is False:
            _logger.warning('> No valid channel detected')
            return vals, False, False
        cache = self.env['ir.model.synchro.cache']
        ext_id = '%s_id' % cache.get_attr(channel_from, 'PREFIX')
        ctx = {}
        if 'company_id' in vals:
            ctx['company_id'] = vals['company_id']
        elif cache.get_struct_model_attr(model, 'MODEL_WITH_COMPANY'):
            ctx['company_id'] = cache.get_attr(channel_from, 'COMPANY_ID')
        if ctx.get('company_id'):
            ctx['country_id'] = self.env[
                'res.company'].browse(
                    ctx['company_id']).partner_id.country_id.id
        else:
            ctx['country_id'] = \
                self.env.user.company_id.partner_id.country_id.id
        self.logmsg('debug', 'ctx=%s' % ctx)
        if hasattr(self.env[model], 'preprocess'):
            vals = self.env[model].preprocess(channel_from, vals)
        vals = process_fields(channel_from, model, vals, ext_id, ctx,
                              field_list=(ctx.keys() + ['street']))
        vals = process_fields(channel_from, model, vals, ext_id, ctx,
                              excl_list=(ctx.keys() + ['street']))
        if (model == 'product.product' and
                vals.get('name') and
                ext_id in vals and
                cache.get_attr(channel_from, 'NO_VARIANTS')):
            tmpl_vals = vals.copy()
            if 'id' in tmpl_vals:
                del tmpl_vals['id']
            id = self.synchro(self.env['product.template'], tmpl_vals)
            if id > 0:
                vals['product_tmpl_id'] = id
        return vals, ext_id, channel_from

    def set_default_values(self, model, vals, channel_id):
        cache = self.env['ir.model.synchro.cache']
        prefix1 = '%s_' % cache.get_attr(channel_id, 'PREFIX')
        prefix2 = '%s:' % cache.get_attr(channel_id, 'PREFIX')
        for ext_ref in cache.get_model_attr(channel_id, model, 'APPLY'):
            ext_name, loc_name, is_foreign, loc_ext_ref = \
                self.names_from_ref(model, channel_id, vals,
                                    ext_ref, prefix1, prefix2)
            if loc_name not in vals:
                if loc_name in cache.get_model_attr(channel_id,
                                                    model, 'LOC_FIELDS'):
                    ext_name = cache.get_model_field_attr(
                        channel_id, model, loc_name, 'LOC_FIELDS')
                    if ext_name[0] == '.':
                        default, apply = self.get_default_n_apply(
                            model, channel_id, loc_name, ext_name, is_foreign,
                            ttype=cache.get_struct_model_field_attr(
                                model, loc_name, 'ttype'))
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
        cache = self.env['ir.model.synchro.cache']
        company_id = cache.get_attr(channel_id, 'COMPANY_ID')

        id = -1
        for keys in cache.get_model_attr(channel_id, model, 'SKEYS'):
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
        cache = self.env['ir.model.synchro.cache']
        if id:
            url = os.path.join(
                cache.get_attr(channel_id, 'COUNTERPART_URL'),
                cache.get_model_attr(channel_id, model, 'BIND'),
                str(id))
        else:
            url = os.path.join(
                cache.get_attr(channel_id, 'COUNTERPART_URL'),
                cache.get_model_attr(channel_id, model, 'BIND'))
        headers = {'Authorization': 'access_token %s' %
                   cache.get_attr(channel_id, 'CLIENT_KEY')}
        self.logmsg(channel_id,
                    '> vg7_requests(%s,%s)' % (url, headers))
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
                     cache.get_attr(channel_id, 'CLIENT_KEY'),
                     cache.get_attr(channel_id, 'PREFIX')))
        cache.clean_cache(channel_id=channel_id, model=model)
        return {}

    def get_counterpart_response(self, channel_id, model, id=False):
        cache = self.env['ir.model.synchro.cache']
        identity = cache.get_attr(channel_id, 'IDENTITY')
        if identity == 'odoo':
            return self.get_odoo_response(channel_id, model, id)
        elif identity == 'vg7':
            return self.get_vg7_response(channel_id, model, id)

    @api.model
    def synchro(self, cls, vals, constraints=None):
        vals = unicodes(vals)
        model = cls.__class__.__name__
        self.logmsg(0, '> %s.synchro(%s)' % (model, vals))
        ir_model = self.env[model]
        cache = self.env['ir.model.synchro.cache']
        cache.open(model=model, cls=cls)
        constraints = constraints or cls.CONTRAINTS
        has_active = cache.get_struct_model_attr(
            model, 'MODEL_WITH_ACTIVE', default=False)
        has_state = cache.get_struct_model_attr(
            model, 'MODEL_STATE', default=False)
        has_2delete = cache.get_struct_model_attr(
            model, 'MODEL_2DELETE', default=False)
        if has_2delete:
            vals['to_delete'] = False
        lines_of_rec = cache.get_struct_model_attr(
            model, 'LINES_OF_REC', default=False)

        vals, ext_id, channel_id = self.bind_to_internal(model, vals)
        if not channel_id:
            cache.clean_cache()
            return -6
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
                self.logmsg(channel_id, 'Record %s.%d not changed' % (model,
                                                                      id))
        return id

    @api.model
    def commit(self, cls, id):
        model = cls.__class__.__name__
        self.logmsg(0, '> %s.commit()' % model)
        cache = self.env['ir.model.synchro.cache']
        cache.open(model=model, cls=cls)
        has_state = cache.get_struct_model_attr(
            model, 'MODEL_STATE', default=False)
        lines_of_rec = cache.get_struct_model_attr(
            model, 'LINES_OF_REC', default=False)
        model_line = cache.get_struct_model_attr(model, 'LINE_MODEL')
        if not has_state and not lines_of_rec and not model_line:
            return -5
        parent_id = cache.get_struct_model_attr(model_line, 'PARENT_ID')
        if not parent_id:
            return -5
        try:
            rec_2_commit = self.env[model].browse(id)
        except:
            return -3
        if cache.get_struct_model_attr(model_line, 'MODEL_2DELETE'):
            ir_model = self.env[model_line]
            for rec in ir_model.search([(parent_id, '=', id),
                                        ('to_delete', '=', True)]):
                rec.unlink()
        return self.set_actual_state(model, rec_2_commit)

    def prefix_bind(self, prefix, data):
        vals = {}
        for name in data:
            vals['%s:%s' % (prefix, name)] = data[name]
        return vals

    @api.multi
    def pull_recs_2_complete(self):
        self.logmsg(0, '> pull_recs_2_complete()')
        cache = self.env['ir.model.synchro.cache']
        cache.open()
        for channel_id in cache.get_channel_list():
            for model in cache.get_attr_list(channel_id):
                if not cache.is_struct(model):
                    continue
                if not cache.get_struct_model_attr(model, 'MODEL_WITH_NAME'):
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
                            cache.get_attr(channel_id, 'PREFIX'),
                            data))
                        # commit every table to avoid too big transaction
                        self.env.cr.commit()   # pylint: disable=invalid-commit

    @api.multi
    def pull_full_records(self, force=None):
        self.logmsg(0, '> pull_full_records(%s)' % force)
        cache = self.env['ir.model.synchro.cache']
        cache.open()
        for channel_id in cache.get_channel_list():
            model_list = [x.name for x in self.env[
                'synchro.channel.model'].search(
                    [('synchro_channel_id', '=', channel_id)],
                    order='sequence')]
            for model in model_list:
                if not cache.is_struct(model):
                    continue
                cache.open(model=model)
                if not cache.get_model_attr(channel_id, model, '2PULL',
                                            default=False):
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
                    ext_id = '%s_id' % cache.get_attr(channel_id, 'IDENTITY')
                    if force or not ir_model.search([(ext_id, '=', id)]):
                        ir_model.synchro(self.prefix_bind(
                            cache.get_attr(channel_id, 'PREFIX'),
                            data))
                        # commit every table to avoid too big transaction
                        self.env.cr.commit()   # pylint: disable=invalid-commit


class IrModelSynchroCache(models.Model):
    _name = 'ir.model.synchro.cache'
    _inherit = 'ir.model.synchro'

    STRUCT = {}
    MANAGED_MODELS = {}
    EXPIRATION_TIME = 60

    def lifetime(self, lifetime):
        if lifetime >= 5 and lifetime <= 3600:
            self.EXPIRATION_TIME = lifetime

    def clean_cache(self, channel_id=None, model=None, lifetime=None):
        dbname = self._cr.dbname
        self.STRUCT[dbname] = self.STRUCT.get(dbname, {})
        self.MANAGED_MODELS[dbname] = self.MANAGED_MODELS.get(dbname, {})
        if model:
            # self.STRUCT[model] = {}
            self.STRUCT[dbname][model] = {}
        else:
            # self.STRUCT = {}
            self.STRUCT[dbname] = {}
        if channel_id:
            if model:
                # self.MANAGED_MODELS[channel_id][model] = {}
                self.MANAGED_MODELS[dbname][channel_id] = self.MANAGED_MODELS[
                    dbname].get(channel_id, {})
                self.MANAGED_MODELS[dbname][channel_id][model] = {}
            else:
                # self.MANAGED_MODELS[channel_id] = {}
                self.MANAGED_MODELS[dbname][channel_id] = {}
        else:
            # self.MANAGED_MODELS = {}
            self.MANAGED_MODELS[dbname] = {}
        if lifetime:
            self.lifetime(lifetime)

    def set_loglevel(self, loglevel):
        for channel_id in self.get_channel_list():
            self.set_attr(channel_id, 'LOGLEVEL', loglevel)

    def is_struct(self, model):
        return model >= 'a'

    def get_channel_list(self):
        # return self.MANAGED_MODELS
        return self.MANAGED_MODELS.get(self._cr.dbname, {})

    def get_attr_list(self, channel_id):
        # return self.MANAGED_MODELS.get(channel_id, {})
        return self.MANAGED_MODELS.get(self._cr.dbname, {}).get(channel_id, {})

    def get_attr(self, channel_id, attrib, default=None):
        # return self.MANAGED_MODELS.get(channel_id, {}).get(attrib, default)
        return self.MANAGED_MODELS.get(self._cr.dbname, {}).get(
            channel_id, {}).get(attrib, default)

    def get_model_attr(self, channel_id, model, attrib, default=None):
        # return self.MANAGED_MODELS.get(
        #     channel_id, {}).get(model, {}).get(attrib, default)
        return self.MANAGED_MODELS.get(self._cr.dbname, {}).get(
            channel_id, {}).get(model, {}).get(attrib, default)

    def get_model_field_attr(self, channel_id, model, field, attrib,
                             default=None):
        # return self.MANAGED_MODELS.get(
        #     channel_id, {}).get(model, {}).get(attrib, {}).get(
        #         field, default)
        return self.MANAGED_MODELS.get(self._cr.dbname, {}).get(
            channel_id, {}).get(model, {}).get(attrib, {}).get(
                field, default)

    def set_channel(self, channel_id):
        # self.MANAGED_MODELS[channel_id] = self.MANAGED_MODELS.get(
        #     channel_id, {})
        self.MANAGED_MODELS[self._cr.dbname] = self.MANAGED_MODELS.get(
            self._cr.dbname, {})
        self.MANAGED_MODELS[self._cr.dbname][
            channel_id] = self.MANAGED_MODELS.get(self._cr.dbname, {}).get(
                channel_id, {})

    def set_model(self, channel_id, model):
        self.set_channel(channel_id)
        # self.MANAGED_MODELS[channel_id][model] = self.MANAGED_MODELS[
        #     channel_id].get(model, {})
        self.MANAGED_MODELS[self._cr.dbname][channel_id][
            model] = self.MANAGED_MODELS.get(self._cr.dbname, {})[
                channel_id].get(model, {})
        self.set_model_attr(channel_id, model, 'LOC_FIELDS', {})
        self.set_model_attr(channel_id, model, 'EXT_FIELDS', {})
        self.set_model_attr(channel_id, model, 'APPLY', {})
        self.set_model_attr(channel_id, model, 'PROTECT', {})

    def set_attr(self, channel_id, attrib, value):
        # self.MANAGED_MODELS[channel_id][attrib] = value
        self.MANAGED_MODELS[self._cr.dbname][channel_id][attrib] = value

    def set_model_attr(self, channel_id, model, attrib, value):
        # self.MANAGED_MODELS[channel_id][model][attrib] = value
        self.MANAGED_MODELS[self._cr.dbname][channel_id][model][attrib] = value

    def set_model_field_attr(self, channel_id, model, field, attrib, value):
        # self.MANAGED_MODELS[channel_id][model][attrib][field] = value
        self.MANAGED_MODELS[self._cr.dbname][channel_id][model][attrib][
            field] = value

    def model_list(self):
        # return self.STRUCT
        return self.STRUCT.get(self._cr.dbname, {})

    def get_struct_attr(self, attrib, default=None):
        default = default or {}
        # return self.STRUCT.get(attrib, default)
        return self.STRUCT.get(self._cr.dbname, {}).get(attrib, default)

    def get_struct_model_attr(self, model, attrib, default=None):
        # return self.STRUCT.get(model, {}).get(attrib, default)
        return self.STRUCT.get(self._cr.dbname, {}).get(model, {}).get(
            attrib, default)

    def get_struct_model_field_attr(self, model, field, attrib, default=None):
        # return self.STRUCT.get(model, {}).get(field, {}).get(attrib, default)
        return self.STRUCT.get(self._cr.dbname, {}).get(model, {}).get(
            field, {}).get(attrib, default)

    def set_struct_model(self, model):
        # self.STRUCT[model] = self.STRUCT.get(model, {})
        self.STRUCT[self._cr.dbname] = self.STRUCT.get(
            self._cr.dbname, {})
        self.STRUCT[self._cr.dbname][model] = self.STRUCT.get(
            self._cr.dbname, {}).get(model, {})

    def set_struct_model_attr(self, model, attrib, value):
        # self.STRUCT[model][attrib] = value
        self.STRUCT[self._cr.dbname][model][attrib] = value

    def setup_model_structure(self, model, ro_fields=None):
        '''Store model structure in memory'''
        if not model:
            return
        ro_fields = ro_fields or []
        if self.get_struct_model_attr(model,
                                      'EXPIRE',
                                      default=datetime.now()) > datetime.now():
            return
        ir_model = self.env['ir.model.fields']
        self.set_struct_model(model)
        self.set_struct_model_attr(model, 'EXPIRE',
                                   datetime.now() + timedelta(
                                       seconds=(self.EXPIRATION_TIME)))
        for field in ir_model.search([('model', '=', model)]):
            required = field.required
            readonly = field.readonly
            readonly = readonly or field.ttype in ('binary', 'reference')
            if field.name in ro_fields:
                readonly = True
            self.set_struct_model_attr(
                model, field.name, {
                    'ttype': field.ttype,
                    'relation': field.relation,
                    'required': required,
                    'readonly': readonly,
                    'protect': field.protect_update,
                })
            if field.relation and field.relation.startswith(model):
                self.set_struct_model_attr(model, 'LINES_OF_REC', field.name)
                self.set_struct_model_attr(model, 'LINE_MODEL', field.relation)
            elif field.relation and model.startswith(field.relation):
                self.set_struct_model_attr(model, 'PARENT_ID', field.name)
            if field.name == 'original_state':
                self.set_struct_model_attr(model, 'MODEL_STATE', True)
            elif field.name == 'to_delete':
                self.set_struct_model_attr(model, 'MODEL_2DELETE', True)
            elif field.name == 'name':
                self.set_struct_model_attr(model, 'MODEL_WITH_NAME', True)
            elif field.name == 'active':
                self.set_struct_model_attr(model, 'MODEL_WITH_ACTIVE', True)
            elif field.name == 'dim_name':
                self.set_struct_model_attr(model, 'MODEL_WITH_DIMNAME', True)
            elif field.name == 'company_id':
                self.set_struct_model_attr(model, 'MODEL_WITH_COMPANY', True)
            elif field.name == 'country_id':
                self.set_struct_model_attr(model, 'MODEL_WITH_COUNTRY', True)

    def setup_channels(self):
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
            if self.get_attr(channel.id,
                             'EXPIRE',
                             default=datetime.now()) > datetime.now():
                continue
            self.set_channel(channel.id)
            self.set_attr(channel.id, 'EXPIRE',
                          datetime.now() + timedelta(
                              seconds=(self.EXPIRATION_TIME * 3)))
            self.set_attr(channel.id, 'PREFIX', channel.prefix)
            self.set_attr(channel.id, 'IDENTITY', channel.identity)
            if channel.company_id:
                self.set_attr(channel.id,
                              'COMPANY_ID', channel.company_id.id)
            else:
                self.set_attr(channel.id,
                              'COMPANY_ID', self.env.user.company_id.id)
            self.set_attr(channel.id, 'CLIENT_KEY', channel.client_key)
            self.set_attr(channel.id,
                          'COUNTERPART_URL', channel.counterpart_url)
            self.set_attr(channel.id, 'PASSWORD', channel.password)
            if channel.produtc_without_variants:
                self.set_attr(channel.id, 'NO_VARIANTS', True)
            if channel.trace:
                self.set_attr(channel.id, 'LOGLEVEL', 'info')
            else:
                self.set_attr(channel.id, 'LOGLEVEL', 'debug')

    def setup_models_in_channels(self, model):
        if not model:
            return
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
            self.set_model_attr(channel_id, model, 'EXPIRE',
                                datetime.now() + timedelta(
                                    seconds=(self.EXPIRATION_TIME) * 2))
            if rec.field_2complete:
                self.set_model_attr(channel_id, model, '2PULL', True)
            self.set_model_attr(
                channel_id, model, 'MODEL_KEY', rec.field_uname)
            self.set_model_attr(
                channel_id, model, 'SKEYS', eval(rec.search_keys))
            self.set_model_attr(
                channel_id, model, 'BIND', rec.counterpart_name)
            self.setup_channel_model_fields(rec)
        for channel_id in self.get_channel_list():
            if self.get_attr(channel_id, 'IDENTITY') == 'odoo':
                self.set_odoo_model(channel_id, model)

    def setup_channel_model_fields(self, model_rec):
        model = model_rec.name
        channel_id = model_rec.synchro_channel_id.id
        self.set_model(channel_id, model)
        self.set_odoo_model(channel_id, model, force=True)
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
        # special names
        ext_ref = '%s_id' % self.get_attr(channel_id, 'IDENTITY')
        self.set_model_field_attr(
            channel_id, model, 'id', 'LOC_FIELDS', '')
        self.set_model_field_attr(
            channel_id, model, ext_ref, 'LOC_FIELDS', 'id')
        self.set_model_field_attr(
            channel_id, model, 'id', 'EXT_FIELDS', ext_ref)

    def set_odoo_model(self, channel_id, model, force=None):
        if not force and self.get_attr(channel_id, model):
            return
        identity = self.get_attr(channel_id, 'IDENTITY')
        self.set_model(channel_id, model)
        skeys = ['name']
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
            if ((field == 'description' and model == 'account.tax') or
                    field == 'code'):
                skeys = [field]
        if model in self.SKEYS:
            self.set_model_attr(channel_id, model, 'SKEYS', self.SKEYS[model])
        else:
            self.set_model_attr(channel_id, model, 'SKEYS', [skeys])

    @api.model_cr_context
    def open(self, model=None, cls=None):
        self.setup_model_structure(model)
        self.setup_channels()
        self.setup_models_in_channels(model)
        if cls is not None:
            if cls.__class__.__name__ != model:
                raise RuntimeError('Class %s not of declared model %s' % (
                    cls.__class__.__name__, model))
            if hasattr(cls, 'LINES_OF_REC'):
                self.set_struct_model_attr(model, 'LINES_OF_REC',
                                           getattr(cls, 'LINES_OF_REC'))
            if hasattr(cls, 'LINE_MODEL'):
                self.set_struct_model_attr(model, 'LINE_MODEL',
                                           getattr(cls, 'LINE_MODEL'))
            if hasattr(cls, 'PARENT_ID'):
                self.set_struct_model_attr(model, 'PARENT_ID',
                                           getattr(cls, 'PARENT_ID'))

    def show_debug(self, channel_id, model):
        if not model:
            return
        if channel_id:
            _logger.warning('> channel_id=%d' % channel_id)
            _logger.warning('> model=%s' % model)
            _logger.warning('> model params:(2pull=%s,key=%s,bind=%s)' % (
                self.get_model_attr(channel_id, model, '2PULL'),
                self.get_model_attr(channel_id, model, 'MODEL_KEY'),
                self.get_model_attr(channel_id, model, 'BIND'),
                )
            )
            for field in self.get_model_attr(channel_id,
                                             model, 'LOC_FIELDS', default={}):
                if not self.is_struct(field):
                    continue
                _logger.warning('--- %-20.20s=%-20.20s (%s/"%s")' % (
                    field,
                    self.get_model_field_attr(
                        channel_id, model, field, 'LOC_FIELDS'),
                    self.get_model_field_attr(
                        channel_id, model, field, 'APPLY'),
                    self.get_model_field_attr(
                        channel_id, model, field, 'PROTECT', default='0'),
                    )
                )
            for field in self.get_model_attr(channel_id,
                                             model, '', default={}):
                if not self.is_struct(field):
                    continue
                loc_field = self.get_model_field_attr(
                    channel_id, model, field, 'EXT_FIELDS')
                if loc_field in self.get_model_field_attr(
                        channel_id, model, field, 'LOC_FIELDS'):
                    continue
                _logger.warning('--- %-20.20s=%-20.20s (%s/"%s")' % (
                    loc_field,
                    field,
                    self.get_model_field_attr(
                        channel_id, model, field, 'APPLY'),
                    self.get_model_field_attr(
                        channel_id, model, field, 'PROTECT', default='0'),
                    )
                )
            _logger.warning('> ')
        _logger.warning('> model=%s' % model)
        _logger.warning('> model params:(Company=%s,Lines=%s,LnModel=%s,'
                     'Parent=%s,State=%s)' % (
                         self.get_struct_model_attr(model,
                                                    'MODEL_WITH_COMPANY'),
                         self.get_struct_model_attr(model, 'LINES_OF_REC'),
                         self.get_struct_model_attr(model, 'LINE_MODEL'),
                         self.get_struct_model_attr(model, 'PARENT_ID'),
                         self.get_struct_model_attr(model, 'MODEL_STATE'),
                         ))
        for field in self.get_struct_attr(model, default={}):
            if not self.is_struct(field):
                continue
            _logger.warning('--- %-20.20s: %s (Req=%s,RO=%s,rel=%s,Prot=%s)' % (
                self.get_struct_model_attr(model, model, field),
                self.get_struct_model_field_attr(model, field, 'ttype'),
                self.get_struct_model_field_attr(model, field, 'required'),
                self.get_struct_model_field_attr(model, field, 'readonly'),
                self.get_struct_model_field_attr(model, field, 'relation'),
                self.get_struct_model_field_attr(model, field, 'protect'),
                )
            )


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


# class IrModelFieldSynchroModel(models.Model):
#     _inherit = 'ir.model.synchro.import'

#     def __init__(self):
#         _tags = {
#             'record': self._tag_record,
#         }

#     def _tag_record(self, rec, mode=None, data_node=None):
#         pass

#     def parse(self, xml, mode=None):
#         roots = ['openerp','data','odoo']
#         if xml.tag not in roots:
#             raise Exception(
#                 "Root xml tag must be <openerp>, <odoo> or <data>.")
#         for rec in xml:
#             if rec.tag in roots:
#                 self.parse(rec, mode)
#             elif rec.tag in self._tags:
#                 try:
#                     self._tags[rec.tag](rec, xml, mode=mode)
#                 except Exception, e:
#                     raise ParseError
#         return True

#     def load_xml_file(self):
#         xmlfile = os.path.abspath(os.path.join(os.path.dirname(__file__),
#                                                '..',
#                                                'data',
#                                                'synchro_channel.xml'))
#         with open(xmlfile, 'r') as fd:
#             xmlcontent = fd.read()
#         # dom = etree.fromstring(xmlcontent)
#         doc = etree.parse(xmlfile)
