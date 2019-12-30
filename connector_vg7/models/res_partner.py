# -*- coding: utf-8 -*-
#
# Copyright 2018-19 - SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
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
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    dim_name = fields.Char('Search Key',
                           compute=_set_dim_name,
                           store=True,
                           readonly=True)

    CONTRAINTS = (['id', '!=', 'parent_id'])

    @api.model_cr_context
    def _auto_init(self):
        res = super(ResPartner, self)._auto_init()
        for prefix in ('vg7', 'oe7'):
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
    def preprocess(self, channel_id, vals):

        def set_vg7_id(vals):
            if vals.get('vg7:id'):
                nm = 'vg7:id'
            elif vals.get('vg7_id'):
                nm = 'vg7_id'
            else:
                nm = None
            if nm:
                if isinstance(vals[nm], basestring):
                    vals[nm] = int(vals[nm])
                if vals[nm] < 100000000:
                    if vals.get('type') == 'delivery':
                        vals[nm] = vals[nm] + 100000000
                    elif vals.get('type') == 'invoice':
                        vals[nm] = vals[nm] + 200000000
            return vals

        def rephase_fields(vals, ext_ref):
            prefix = '%s_' % ext_ref.split(':')[1]
            for field in vals.copy():
                if field == 'customer_shipping_id':
                    name = 'vg7:id'
                else:
                    name = 'vg7:%s' % field.replace(prefix, '')
                if name != field:
                    vals[name] = vals[field]
                    del vals[field]
            for nm in ('vg7:company', 'vg7:name', 'vg7:surename'):
                if (nm in vals and
                        (not isinstance(vals[nm], basestring) or
                         not vals[nm].strip())):
                    del vals[nm]
            return vals

        cache = self.env['ir.model.synchro.cache']
        model = 'res.partner'
        if cache.get_attr(channel_id, 'PREFIX') == 'vg7':
            if vals.get('type') == 'delivery':
                for ext_ref in ('vg7:piva',
                                'vg7:esonerato_fe',
                                'vg7:codice_univoco',
                                'electronic_invoice_subjected'):
                    if ext_ref in vals:
                        del vals[ext_ref]
            elif vals.get('type') == 'invoice':
                vals = set_vg7_id(vals)
                for ext_ref in ('vg7:piva',):
                    if ext_ref in vals:
                        del vals[ext_ref]
            else:
                for ext_ref in ('parent_id',):
                    if ext_ref in vals:
                        del vals[ext_ref]
                for ext_ref in ('vg7:shipping', 'vg7:billing'):
                    if ext_ref in vals:
                        vals[ext_ref] = rephase_fields(vals[ext_ref], ext_ref)
                        if ext_ref == 'vg7:shipping':
                            vals[ext_ref]['type'] = 'delivery'
                        elif ext_ref == 'vg7:billing':
                            vals[ext_ref]['type'] = 'invoice'
                        if 'vg7:id' not in vals[ext_ref] and 'vg7:id' in vals:
                            vals[ext_ref]['vg7:id'] = vals['vg7:id']
                            vals[ext_ref] = set_vg7_id(vals[ext_ref])
                        if ('vg7:company' not in vals[ext_ref] and
                                'vg7:name' not in vals[ext_ref] and
                                'vg7:surename' not in vals[ext_ref]):
                            if 'vg7:company' in vals:
                                vals[ext_ref]['name'] = vals['vg7:company']
                            elif ('vg7:name' in vals or
                                  'vg7:surename' in vals):
                                vals[ext_ref]['name'] = '%s %s' % (
                                    vals.get('vg7:name', ''),
                                    vals.get('vg7:surename', ''))
                        if ext_ref == 'vg7:billing':
                            for nm in ('vg7:piva',
                                       'vg7:esonerato_fe',
                                       'vg7:codice_univoco'):
                                if nm in vals[ext_ref] and nm not in vals:
                                    vals[nm] = vals[ext_ref][nm]
                                    del vals[ext_ref][nm]
                        cache.set_model_attr(
                            channel_id, model, ext_ref, vals[ext_ref])
                        del vals[ext_ref]
                    else:
                        cache.set_model_attr(channel_id, model, ext_ref, {})
        return vals

    @api.model
    def postprocess(self, channel_id, id, vals):
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

    def rephase_fields(self, vals, ext_ref):
        prefix = '%s_' % ext_ref.split(':')[1]
        for field in vals.copy():
            if field == 'vg7:customer_shipping_id':
                name = 'vg7:id'
            else:
                name = '%s' % field.replace(prefix, '')
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
    def synchro(self, vals, disable_post=None):
        vals = self.rephase_fields(vals, 'vg7:shipping')
        vals['type'] = 'delivery'
        return self.env['ir.model.synchro'].synchro(self, vals)
