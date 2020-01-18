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
            partner.dim_name = self.env[
                'ir.model.synchro'].dim_text(partner.name)

    vg7_id = fields.Integer('VG7 ID', copy=False)
    vg72_id = fields.Integer('VG7 ID (2.nd)', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)
    dim_name = fields.Char('Search Key',
                           compute=_set_dim_name,
                           store=True,
                           readonly=True)

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
    def rephase_fields(self, vals, ext_ref):
        _logger.info(
            '> rephase(%s,%s)' % (vals, ext_ref))  # debug
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
        _logger.info(
            '> return %s' % vals)      # debug
        return vals

    @api.model
    def preprocess(self, channel_id, vals):

        def set_vg7_id(vals):
            found = False
            for nm in ('customer_shipping_id', 'vg7:id', 'vg7_id'):
                if vals.get(nm):
                    found = True
                    break
            if found:
                if isinstance(vals[nm], basestring):
                    vals[nm] = int(vals[nm])
                if vals.get('type'):
                    vals[nm] = self.env[
                        'ir.model.synchro'].get_loc_ext_id_value(
                        channel_id, 'res.partner', vals[nm], spec=vals['type'])
            return vals

        _logger.info(
            '> preprocess(%s)' % vals)      # debug
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
                        del vals[ext_ref]
                for ext_ref in ('vg7:shipping', 'vg7:billing'):
                    if ext_ref in vals:
                        vals[ext_ref] = self.rephase_fields(
                            vals[ext_ref], ext_ref)
                        if ext_ref == 'vg7:shipping':
                            vals[ext_ref]['type'] = 'delivery'
                            # vals[ext_ref] = set_vg7_id(vals[ext_ref])
                        elif ext_ref == 'vg7:billing':
                            vals[ext_ref]['type'] = 'invoice'
                            if ('vg7:id' not in vals[ext_ref] and
                                    'vg7:id' in vals):
                                vals[ext_ref]['vg7:id'] = vals['vg7:id']
                                vals[ext_ref] = set_vg7_id(vals[ext_ref])
                        if ('vg7:company' not in vals[ext_ref] and
                                'vg7:name' not in vals[ext_ref] and
                                'vg7:surename' not in vals[ext_ref]):
                            if 'vg7:company' in vals:
                                vals[ext_ref][
                                    'vg7:company'] = vals['vg7:company']
                            elif ('vg7:name' in vals or
                                  'vg7:surename' in vals):
                                vals[ext_ref]['vg7:company'] = '%s %s' % (
                                    vals.get('vg7:name', ''),
                                    vals.get('vg7:surename', ''))
                        if ext_ref == 'vg7:billing':
                            for nm in ('vg7:piva',
                                       'vg7:cf',
                                       'vg7:esonerato_fe',
                                       'vg7:codice_univoco',
                                       'vg7:bank',
                                       'vg7:payment',
                                       'vg7:payment_id',
                                       'vg7:pec',):
                                if (nm in vals[ext_ref] and
                                        (nm not in vals or
                                         vals[ext_ref][nm] == vals[nm])):
                                    vals[nm] = vals[ext_ref][nm]
                                    del vals[ext_ref][nm]
                            for nm in ('vg7:company',
                                       'vg7:name',
                                       'vg7:surename',
                                       'vg7:street',
                                       'vg7:postal_code',
                                       'vg7:city',
                                       'vg7:region',
                                       'vg7:region_id',
                                       'vg7:mail',
                                       'vg7:country'
                                       'vg7:country_id'):
                                if (nm in vals[ext_ref] and
                                        (nm not in vals or
                                         vals[ext_ref][nm] == vals[nm])):
                                    vals[nm] = vals[ext_ref][nm]
                        _logger.info(
                            '> store(%s,%s)' % (vals[ext_ref], ext_ref))  # debug
                        cache.set_model_attr(
                            channel_id, actual_model, ext_ref, vals[ext_ref])
                        del vals[ext_ref]
                    else:
                        cache.set_model_attr(
                            channel_id, actual_model, ext_ref, {})
                _logger.info(
                    '> %s.synchro(%s,%s)' % (actual_model, vals, True))
        return vals, spec

    @api.model
    def postprocess(self, channel_id, id, vals):
        _logger.info(
            '> postprocess(%d,%s)' % (id, vals))  # debug
        cache = self.env['ir.model.synchro.cache']
        model = 'res.partner'
        for ext_ref in ('vg7:shipping', 'vg7:billing'):
            if cache.get_model_attr(channel_id, model, ext_ref):
                vals = {}
                for field in cache.get_model_attr(channel_id, model, ext_ref):
                    vals[field] = cache.get_model_attr(
                        channel_id, model, ext_ref)[field]
                vals['parent_id'] = id
                cache.del_model_attr(channel_id, model, ext_ref)
                self.synchro(vals, disable_post=True)

    @api.model
    def synchro(self, vals, disable_post=None):
        if not disable_post:
            vals['type'] = 'contact'
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post)

    @api.multi
    def pull_record(self):
        self.env['ir.model.synchro'].pull_record(self)


class ResPartnerShipping(models.Model):
    _name = "res.partner.shipping"
    _inherit = "res.partner"

    CONTRAINTS = (['id', '!=', 'parent_id'])

    @api.model
    def synchro(self, vals, disable_post=None):
        vals = self.env['res.partner'].rephase_fields(
            vals, 'vg7:shipping')
        vals['type'] = 'delivery'
        return self.env['ir.model.synchro'].synchro(self, vals)


class ResPartneriNVOICE(models.Model):
    _name = "res.partner.invoice"
    _inherit = "res.partner"

    CONTRAINTS = (['id', '!=', 'parent_id'])

    @api.model
    def synchro(self, vals, disable_post=None):
        vals = self.env['res.partner'].rephase_fields(
            vals, 'vg7:billing')
        vals['type'] = 'invoice'
        return self.env['ir.model.synchro'].synchro(self, vals)


class ResPartnerSupplier(models.Model):
    _name = "res.partner.supplier"
    _inherit = "res.partner"

    @api.model
    def synchro(self, vals, disable_post=None):
        vals['supplier'] = True
        return self.env['ir.model.synchro'].synchro(self, vals)
