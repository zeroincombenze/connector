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


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.multi
    @api.depends('name')
    def _set_dim_name(self):
        for product in self:
            product.dim_name = self.env[
                'ir.model.synchro'].dim_text(product.name)

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)
    dim_name = fields.Char('Search Key',
                           compute=_set_dim_name,
                           store=True,
                           readonly=True)

    CONTRAINTS = ()
    LINES_OF_REC = False
    LINE_MODEL = False

    @api.model_cr_context
    def _auto_init(self):
        res = super(ProductTemplate, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(
                self._inherit, prefix)
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
    def synchro(self, vals, disable_post=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post)

    @api.multi
    def pull_record(self):
        for product in self.product_variant_ids:
            self.env['ir.model.synchro'].pull_record(product)


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.multi
    @api.depends('name')
    def _set_dim_name(self):
        for product in self:
            product.dim_name = self.env[
                'ir.model.synchro'].dim_text(product.name)

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)
    dim_name = fields.Char('Search Key',
                           compute=_set_dim_name,
                           store=True,
                           readonly=True)

    CONTRAINTS = ()

    @api.model_cr_context
    def _auto_init(self):
        res = super(ProductProduct, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(
                self._inherit, prefix)
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
        cache = self.env['ir.model.synchro.cache']
        if (('vg7_id' in vals or 'vg7:id' in vals) and
                cache.get_attr(channel_id, 'NO_VARIANTS')):
            tmpl_vals = vals.copy()
            if 'id' in tmpl_vals:
                del tmpl_vals['id']
            id = self.env['product.template'].synchro(tmpl_vals)
            if id > 0:
                vals['product_tmpl_id'] = id
        return vals, ''

    @api.model
    def synchro(self, vals, disable_post=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post)


class ProductUom(models.Model):
    _inherit = "product.uom"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)

    CONTRAINTS = ()

    @api.model_cr_context
    def _auto_init(self):
        res = super(ProductUom, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(
                self._inherit, prefix)
        return res

    @api.model
    def synchro(self, vals, disable_post=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post)

    @api.multi
    def pull_record(self):
        return self.env['ir.model.synchro'].pull_record(self)


class ProductCategory(models.Model):
    _inherit = "product.category"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)

    CONTRAINTS = ()

    @api.model_cr_context
    def _auto_init(self):
        res = super(ProductCategory, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(
                self._inherit, prefix)
        return res

    @api.model
    def synchro(self, vals, disable_post=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post)


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)

    CONTRAINTS = ()

    @api.model_cr_context
    def _auto_init(self):
        res = super(ProductPricelist, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(
                self._inherit, prefix)
        return res

    @api.model
    def synchro(self, vals, disable_post=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post)
