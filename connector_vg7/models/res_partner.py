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

_logger = logging.getLogger(__name__)

try:
    from unidecode import unidecode
except ImportError as err:
    _logger.debug(err)


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.multi
    @api.depends('name')
    def _set_dim_name(self):
        for partner in self:
            if partner.name:
                partner.dim_name = self.env[
                    'ir.model.synchro'].dim_text(partner.name)
            elif partner.parent_id:
                partner.dim_name = self.env[
                    'ir.model.synchro'].dim_text(partner.parent_id.name)

    vg7_id = fields.Integer('VG7 ID', copy=False)
    vg72_id = fields.Integer('VG7 ID (2.nd)', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)
    dim_name = fields.Char('Search Key',
                           compute=_set_dim_name,
                           store=True,
                           readonly=True)
    timestamp = fields.Datetime('Timestamp', copy=False, readonly=True)
    errmsg = fields.Char('Error message', copy=False, readonly=True)

    CONTRAINTS = (['id', '!=', 'parent_id'])

    @api.model_cr_context
    def _auto_init(self):
        res = super(ResPartner, self)._auto_init()
        for prefix in ('vg7', 'vg72', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

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

    @api.model
    def shirt_vals(self, vals, ext_ref):
        self.env['ir.model.synchro'].logmsg('debug',
            '>>> res.partner.shirt_vals(%s,%s)' % (vals, ext_ref))
        prefix1 = ext_ref.split(':')[0]
        prefix2 = '%s_' % ext_ref.split(':')[1]
        prefix = '%s:' % prefix1
        for field in vals.copy():
            if field.startswith(ext_ref):
                name = '%s' % field.replace(prefix2, '')
            elif field.startswith(prefix):
                name = field
            elif field.startswith(prefix2):
                name = '%s:%s' % (prefix1, field.replace(prefix2, ''))
            else:
                name = '%s:%s' % (prefix1, field)
            if name != field:
                vals[name] = vals[field]
                del vals[field]
        for nm in ('vg7:company', 'vg7:name', 'vg7:surename'):
            if (nm in vals and
                    (not isinstance(vals[nm], basestring) or
                     not vals[nm].strip())):
                del vals[nm]
        return vals

    @api.model
    def preprocess(self, channel_id, vals):

        def set_vg7_id(vals):
            for nm in ('customer_shipping_id', 'vg7:id', 'vg7_id'):
                if vals.get(nm):
                    if isinstance(vals[nm], basestring):
                        vals[nm] = int(vals[nm])
                    if vals.get('type'):
                        vals[nm] = self.env[
                            'ir.model.synchro'].get_loc_ext_id_value(
                            channel_id, 'res.partner', vals[nm],
                            spec=vals['type'])
            return vals

        _logger.info(
            '>>> preprocess(%s)' % vals)      # debug
        cache = self.env['ir.model.synchro.cache']
        actual_model = 'res.partner'
        spec = ''
        if cache.get_attr(channel_id, 'PREFIX') == 'vg7':
            if vals.get('type') == 'delivery':
                vals = set_vg7_id(vals)
                for ext_ref in ('vg7:piva',
                                'vg7:cf',
                                'vg7:esonerato_fe',
                                'vg7:codice_univoco',
                                'electronic_invoice_subjected'):
                    if ext_ref in vals:
                        del vals[ext_ref]
                spec = vals['type']
            elif vals.get('type') == 'invoice':
                vals = set_vg7_id(vals)
                spec = vals['type']
            else:
                for ext_ref in ('parent_id', 'type_inv_addr'):
                    if ext_ref in vals:
                        del vals[ext_ref]
                for ext_ref in ('vg7:billing', 'vg7:shipping'):
                    diff = False
                    if ext_ref in vals:
                        vals[':customer'] = True
                        vals[ext_ref] = self.shirt_vals(
                            vals[ext_ref], ext_ref)
                        if ext_ref == 'vg7:shipping':
                            vals[ext_ref]['type'] = 'delivery'
                        elif ext_ref == 'vg7:billing':
                            vals[ext_ref]['type'] = 'invoice'
                            if ('vg7:id' not in vals[ext_ref] and
                                    'vg7:id' in vals):
                                vals[ext_ref]['vg7:id'] = vals['vg7:id']
                                vals[ext_ref] = set_vg7_id(vals[ext_ref])
                            for nm in ('vg7:type',
                                       'vg7:piva',
                                       'vg7:cf',
                                       'vg7:esonerato_fe',
                                       'vg7:codice_univoco',
                                       'vg7:bank',
                                       'vg7:bank_id',
                                       'vg7:payment',
                                       'vg7:payment_id',
                                       'vg7:pec',
                                       'bank_account_id'):
                                if (nm in vals[ext_ref] and
                                        (nm not in vals or
                                         vals[ext_ref][nm] == vals[nm])):
                                    vals[nm] = vals[ext_ref][nm]
                                    del vals[ext_ref][nm]
                        for nm in ('vg7:company',
                                   'vg7:name',
                                   'vg7:surename',
                                   'vg7:street',
                                   'vg7:street_number',
                                   'vg7:postal_code',
                                   'vg7:city',
                                   'vg7:region',
                                   'vg7:region_id',
                                   'vg7:email',
                                   'vg7:country',
                                   'vg7:country_id',
                                   'vg7:telephone',
                                   'vg7:telephone2'):
                            if nm not in vals[ext_ref]:
                                continue
                            elif nm in ('vg7:company',
                                        'vg7:name',
                                        'vg7:surename'):
                                if vals.get(nm) != vals[ext_ref].get(nm):
                                    if ext_ref != 'vg7:billing':
                                        diff = True
                                    elif not vals.get(nm):
                                        vals[nm] = vals[ext_ref][nm]
                                else:
                                    vals[ext_ref][nm] = False
                            elif nm in vals[ext_ref] and not vals.get(nm):
                                vals[nm] = vals[ext_ref][nm]
                            elif vals.get(nm) != vals[ext_ref].get(nm):
                                diff = True
                        if diff:
                            self.env['ir.model.synchro'].logmsg('debug',
                                '>>> store(%s,%s)' % (vals[ext_ref], ext_ref))
                            cache.set_model_attr(
                                channel_id, actual_model, ext_ref,
                                vals[ext_ref])
                        del vals[ext_ref]
                    else:
                        cache.set_model_attr(
                            channel_id, actual_model, ext_ref, {})
        return vals, spec

    @api.model
    def postprocess(self, channel_id, parent_id, vals):
        _logger.info(
            '>>> postprocess(%d,%s)' % (parent_id, vals))  # debug
        cache = self.env['ir.model.synchro.cache']
        model = 'res.partner'
        done = False
        for ext_ref in ('vg7:shipping', 'vg7:billing'):
            if cache.get_model_attr(channel_id, model, ext_ref):
                vals = {}
                for field in cache.get_model_attr(channel_id, model, ext_ref):
                    vals[field] = cache.get_model_attr(
                        channel_id, model, ext_ref)[field]
                vals['parent_id'] = parent_id
                cache.del_model_attr(channel_id, model, ext_ref)
                self.synchro(vals, disable_post=True)
                done = True
        return done

    def assure_values(self, vals, rec):
        actual_model = 'res.partner'
        actual_cls = self.env[actual_model]
        if rec:
            for nm in ('type', ):
                if nm not in vals:
                    vals[nm] = getattr(rec, nm)
        if ('codice_destinatario' in vals and
                not vals['codice_destinatario']):
            del vals['codice_destinatario']
        if (vals.get('electronic_invoice_subjected') and
                not vals.get('codice_destinatario')):
            if rec and rec.codice_destinatario:
                vals['codice_destinatario'] = rec.codice_destinatario.strip()
            else:
                del vals['electronic_invoice_subjected']
            if not vals['codice_destinatario']:
                del vals['electronic_invoice_subjected']
                del vals['codice_destinatario']
        if 'ipa_code' in vals and not vals['ipa_code']:
            del vals['ipa_code']
        if vals.get('is_pa') and not vals.get('ipa_code'):
            if rec and rec.ipa_code:
                vals['ipa_code'] = rec.ipa_code.strip()
            else:
                del vals['is_pa']
            if not vals['ipa_code']:
                del vals['is_pa']
                del vals['ipa_code']
        if vals.get('individual'):
            vals['is_company'] = True
        if vals.get('type') in ('delivery', 'invoice'):
            parent = False
            if vals.get('parent_id'):
                parent_id = int(vals['parent_id'])
                if actual_cls.search([('id', '=', parent_id)]):
                    parent = actual_cls.browse(parent_id)
                else:
                    del vals['parent_id']
            elif rec and rec.parent_id:
                parent = rec.parent_id
            if parent and not isinstance(parent, (int, long)):
                if (vals.get('name') and
                        (vals.get('name') == parent.name or
                         vals.get('name', '').startswith('Unknown'))):
                    vals['name'] = False
            if vals and (not rec or not rec.name):
                vals['is_company'] = False
            if parent and not isinstance(parent, (int, long)):
                for nm in ('vat', 'fiscalcode', 'codice_destinatario',
                           'country_id', 'state_id'):
                    if (not vals.get(nm) and
                            (not rec or (rec and not rec[nm])) and
                            parent[nm]):
                        if nm.endswith('_id'):
                            vals[nm] = parent[nm].id
                        else:
                            vals[nm] = parent[nm]
        else:
            if not vals.get('name') and not rec:
                vals['name'] = 'Unknown'
        if vals.get('rea_code'):
            ids = actual_cls.search([('rea_code', '=', vals['rea_code'])])
            if ids:
                if not rec or ids[0].id != rec.id:
                    _logger.info(
                        'Duplicate REA Code %s' % vals['rea_code'])
                    del vals['rea_code']
        return vals

    @api.model
    def synchro(self, vals, disable_post=None,
                only_minimal=None, no_deep_fields=None):
        if not disable_post:
            vals[':type'] = 'contact'
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post,
            only_minimal=only_minimal, no_deep_fields=no_deep_fields)

    @api.multi
    def pull_record(self):
        self.env['ir.model.synchro'].pull_record(self)


class ResPartnerShipping(models.Model):
    _name = "res.partner.shipping"
    _inherit = "res.partner"

    CONTRAINTS = (['id', '!=', 'parent_id'])

    @api.model
    def synchro(self, vals, disable_post=None,
                only_minimal=None, no_deep_fields=None):
        vals = self.env['res.partner'].shirt_vals(
            vals, 'vg7:shipping')
        vals[':type'] = 'delivery'
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post,
            only_minimal=only_minimal, no_deep_fields=no_deep_fields)


class ResPartnerInvoice(models.Model):
    _name = "res.partner.invoice"
    _inherit = "res.partner"

    CONTRAINTS = (['id', '!=', 'parent_id'])

    @api.model
    def synchro(self, vals, disable_post=None,
                only_minimal=None, no_deep_fields=None):
        vals = self.env['res.partner'].shirt_vals(
            vals, 'vg7:billing')
        vals[':type'] = 'invoice'
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post,
            only_minimal=only_minimal, no_deep_fields=no_deep_fields)


class ResPartnerSupplier(models.Model):
    _name = "res.partner.supplier"
    _inherit = "res.partner"

    @api.model
    def synchro(self, vals, disable_post=None,
                only_minimal=None, no_deep_fields=None):
        vals['supplier'] = True
        vals[':type'] = 'contact'
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post,
            only_minimal=only_minimal, no_deep_fields=no_deep_fields)
