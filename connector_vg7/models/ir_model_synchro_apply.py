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


class IrModelSynchroApply(models.Model):
    _name = 'ir.model.synchro.apply'
    _inherit = 'ir.model'


    def apply_set_value(self, channel_id, vals, loc_name,
                            ext_ref, loc_ext_id, default=None, ctx=None):
        if loc_name not in vals:
            if vals.get(ext_ref):
                vals[loc_name] = vals[ext_ref]
            elif default:
                vals[loc_name] = default
        return vals

    def apply_set_tmp_name(self, channel_id, vals, loc_name,
                               ext_ref, loc_ext_id, default=None, ctx=None):
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
                vals[loc_name] = '%s' % vals[loc_ext_id]
            else:
                vals[loc_name] = 'Unknown %s' % vals[loc_ext_id]
        else:
            vals[loc_name] = 'Unknown'
        return vals

    def apply_upper(self, channel_id, vals, loc_name,
                        ext_ref, loc_ext_id, default=None, ctx=None):
        if ext_ref in vals:
            if isinstance(vals[ext_ref], basestring):
                vals[loc_name] = vals[ext_ref].upper()
            else:
                vals[loc_name] = vals[ext_ref]
        return vals

    def apply_lower(self, channel_id, vals, loc_name,
                        ext_ref, loc_ext_id, default=None, ctx=None):
        if ext_ref in vals:
            if isinstance(vals[ext_ref], basestring):
                vals[loc_name] = vals[ext_ref].lower()
            else:
                vals[loc_name] = vals[ext_ref]
        return vals

    def apply_bool(self, channel_id, vals, loc_name,
                       ext_ref, loc_ext_id, default=None, ctx=None):
        if ext_ref in vals:
            vals[loc_name] = os0.str2bool(vals.get(ext_ref), Fialse)
        return vals

    def apply_not(self, channel_id, vals, loc_name,
                      ext_ref, loc_ext_id, default=None, ctx=None):
        if ext_ref in vals:
            if isinstance(vals[ext_ref], (int, long, bool)):
                vals[loc_name] = not vals[ext_ref]
            else:
                vals[loc_name] = not os0.str2bool(vals[ext_ref], True)
        return vals

    def apply_person(self, channel_id, vals, loc_name,
                         ext_ref, loc_ext_id, default=None, ctx=None):
        '''First name and/or last name'''
        if ext_ref in vals and loc_name != ext_ref:
            vals[loc_name] = vals[ext_ref]
            del vals[ext_ref]
        if ('lastname' in vals and 'firstname' in vals and
                (vals['lastname'] or vals['firstname'])):
            if not vals.get('name'):
                vals['name'] = '%s %s' % (
                    vals['lastname'] or '', vals['firstname'] or '')
                if not vals['name'].strip():
                    vals = self.apply_set_tmp_name(
                        channel_id, vals, 'name', ext_ref, loc_ext_id)
                vals['is_company'] = True
                vals['individual'] = True
            del vals['lastname']
            del vals['firstname']
        return vals

    def apply_vat(self, channel_id, vals, loc_name,
                      ext_ref, loc_ext_id, default=None, ctx=None):
        '''External vat may not contain ISO code'''
        if ext_ref in vals:
            if isinstance(vals[ext_ref], basestring):
                vals[ext_ref] = vals[ext_ref].strip()
                if (len(vals[ext_ref]) == 11 and
                        vals[ext_ref].isdigit()):
                    vals[loc_name] = 'IT%s' % vals[ext_ref]
                elif vals[ext_ref]:
                    vals[loc_name] = vals[ext_ref]
            elif vals[ext_ref]:
                vals[loc_name] = vals[ext_ref]
        return vals

    def apply_street_number(self, channel_id, vals, loc_name,
                                ext_ref, loc_ext_id, default=None, ctx=None):
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
                                 ext_ref, loc_ext_id, default=None, ctx=None):
        '''Invoice number'''
        if ext_ref in vals:
            vals['move_name'] = vals[ext_ref]
        return vals

    def apply_journal(self, channel_id, vals, loc_name,
                          ext_ref, loc_ext_id, default=None, ctx=None):
        if 'journal_id' not in vals:
            journal = self.env['account.invoice']._default_journal()
            if journal:
                vals['journal_id'] = journal[0].id
        return vals

    def apply_account(self, channel_id, vals, loc_name,
                          ext_ref, loc_ext_id, default=None, ctx=None):
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
                      ext_ref, loc_ext_id, default=None, ctx=None):
        if loc_name not in vals and 'product_id' in vals:
            product = self.env['product.product'].browse(vals['product_id'])
            vals[loc_name] = product.uom_id.id
        elif not vals.get(loc_name):
            vals[loc_name] = self.env.ref('product.product_uom_unit').id
        return vals

    def apply_tax(self, channel_id, vals, loc_name,
                      ext_ref, loc_ext_id, default=None, ctx=None):
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
                         ext_ref, loc_ext_id, default=None, ctx=None):
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
                               ext_ref, loc_ext_id, default=None, ctx=None):
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
                                  ext_ref, loc_ext_id, default=None, ctx=None):
        if (loc_name in vals and
                isinstance(vals.get(loc_name), int) and
                vals[loc_name] > 0):
            return vals
        if 'partner_id' in vals:
            vals[loc_name] = vals['partner_id']
        return vals

    def apply_company_info(self, channel_id, vals, loc_name,
                               ext_ref, loc_ext_id, default=None, ctx=None):
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
                             ext_ref, loc_ext_id, default=None, ctx=None):
        if loc_name in vals:
            return vals
        ctx = ctx or {}
        if loc_name in ctx:
            vals[loc_name] = ctx[loc_name]
        return vals

    def apply_set_einvoice(self, channel_id, vals, loc_name,
                               ext_ref, loc_ext_id, default=None, ctx=None):
        if vals.get(ext_ref):
            if len(vals[ext_ref]) == 7:
                vals['electronic_invoice_subjected'] = True
                vals['is_pa'] = False
            elif len(vals[ext_ref]) == 6:
                vals['electronic_invoice_subjected'] = False
                vals['is_pa'] = True
                vals['ipa_code'] = vals[ext_ref]
                if loc_name in vals:
                    del vals[loc_name]
        return vals

    def apply_set_is_pa(self, channel_id, vals, loc_name,
                            ext_ref, loc_ext_id, default=None, ctx=None):
        if len(vals.get(ext_ref, '')) == 6:
            vals['is_pa'] = True
        return vals

    def apply_iban(self, channel_id, vals, loc_name,
                   ext_ref, loc_ext_id, default=None, ctx=None):
        if vals.get(ext_ref):
            vals[loc_name] = vals[ext_ref].replace(' ', '')
        elif vals.get('vg7:ABI') and vals.get('vg7:CAB'):
            vals[loc_name] = 'IT00A%s%s000000000000' % (vals['ABI'],
                                                        vals['CAB'])
        return vals

    def apply_eom(self, channel_id, vals, loc_name,
                   ext_ref, loc_ext_id, default=None, ctx=None):
        if vals.get(ext_ref):
            eom = os0.str2bool('%s' % vals[ext_ref], False)
            if eom:
                vals['option'] = 'day_after_invoice_date'
            else:
                vals['option'] = 'fix_day_following_month'
            del vals[ext_ref]
        if vals.get('vg7:scadenza'):
            if (isinstance(vals['vg7:scadenza'], basestring) and
                    vals['vg7:scadenza'].isdigit()):
                num_days = int(vals['vg7:scadenza'])
            elif isinstance(vals['vg7:scadenza'], (int, long)):
                num_days = vals['vg7:scadenza']
            else:
                num_days = False
            if num_days:
                cache = self.env['ir.model.synchro.cache']
                if cache.get_struct_model_attr(
                        'account.payment.term.line', 'months'):
                    vals['months'] = num_days / 30
                    vals['days'] = 0
                else:
                    vals['days'] = num_days - 2
        return vals

    def apply_set_inv_warn(self, channel_id, vals, loc_name, ext_ref,
                           loc_ext_id, default=None, ctx=None):
        if vals.get(ext_ref):
            vals['invoice_warn'] = 'warning'
            vals[loc_name] = vals[ext_ref]
        return vals

    def apply_datetime(self, channel_id, vals, loc_name, ext_ref,
                       loc_ext_id, default=None, ctx=None):
        if vals.get(ext_ref):
            vals[loc_name] = vals[ext_ref]
            if len(vals[ext_ref].split(' ')) == 1:
                vals[loc_name] = '%s 00:00:00' % vals[ext_ref]
        return vals

    ############################
    # ODOO MIGRATION FUNCTIONS #
    ############################
    def apply_oe_account_tax_amount(self, channel_id, vals, loc_name, ext_ref,
                                    loc_ext_id, default=None, ctx=None):
        synchro_model = self.env['ir.model.synchro']
        tnldict = synchro_model.get_tnldict(channel_id)
        ext_odoo_ver = synchro_model.get_ext_odoo_ver(ext_ref.split(':')[0])
        vals[loc_name] = transodoo.translate_from_to(
            tnldict, 'account.tax', vals[ext_ref],
            ext_odoo_ver, release.major_version,
            type='value', fld_name='amount')
        return vals

    def apply_oe_account_account_type_name(
            self, channel_id, vals, loc_name, ext_ref, loc_ext_id,
            default=None, ctx=None):
        if not vals.get(loc_name):
            synchro_model = self.env['ir.model.synchro']
            tnldict = synchro_model.get_tnldict(channel_id)
            ext_odoo_ver = synchro_model.get_ext_odoo_ver(
                ext_ref.split(':')[0])
            names = transodoo.translate_from_to(
                tnldict, 'account.account.type', vals[ext_ref],
                ext_odoo_ver, release.major_version,
                type='value', fld_name='report_type')
            name = vals.get('name', '').lower()
            if name == 'Contante':
                name2 = 'cash'
            elif name == 'Cassa':
                name2 = 'cash'
            if isinstance(names, list):
                for nm in names:
                    if nm == name:
                        vals[loc_name] = nm
                        break
        return vals

    def apply_oe_account_account_type(
            self, channel_id, vals, loc_name, ext_ref, loc_ext_id,
            default=None, ctx=None):
        if vals[ext_ref] == 'view':
            vals[loc_name] = 'other'
        else:
            vals[loc_name] = vals[ext_ref]
        return vals
