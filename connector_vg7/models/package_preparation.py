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


class StockPickingPackagePreparation(models.Model):
    _inherit = 'stock.picking.package.preparation'

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)
    original_state = fields.Char('Original Status')
    timestamp = fields.Datetime('Timestamp', copy=False, readonly=True)
    errmsg = fields.Char('Error message', copy=False, readonly=True)

    CONTRAINTS = ()

    @api.model_cr_context
    def _auto_init(self):
        res = super(StockPickingPackagePreparation, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.model
    def synchro(self, vals, disable_post=None, no_deep_fields=None,
                only_minimal=None):
        # TODO: correct workaround!!
        do_rewrite = False
        if 'vg7:ddt_number' in vals:
            do_rewrite = True
            saved_vals = vals.copy()
        id = self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post,
            only_minimal=only_minimal, no_deep_fields=no_deep_fields)
        if id > 0 and do_rewrite:
            saved_vals['id'] = id
            id = self.env['ir.model.synchro'].synchro(
                self, saved_vals, disable_post=True)
        return id

    @api.model
    def commit(self, id):
        return self.env['ir.model.synchro'].commit(self, id)


class StockPickingPackagePreparationLine(models.Model):
    _inherit = 'stock.picking.package.preparation.line'

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)
    to_delete = fields.Boolean('Record to delete')

    CONTRAINTS = ()

    @api.model_cr_context
    def _auto_init(self):
        res = super(StockPickingPackagePreparationLine, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.model
    def synchro(self, vals, disable_post=None,
                only_minimal=None, no_deep_fields=None):
        # TODO: correct workaround!!
        do_rewrite = False
        if 'vg7:order_row_id' in vals:
            do_rewrite = True
            saved_vals = vals.copy()
        id = self.env['ir.model.synchro'].synchro(self, vals,
            disable_post=disable_post,
            only_minimal=only_minimal, no_deep_fields=no_deep_fields)
        if id > 0 and do_rewrite:
            id = self.env['ir.model.synchro'].synchro(self, saved_vals,
                disable_post=disable_post,
                only_minimal=only_minimal, no_deep_fields=no_deep_fields)
        return id


class StockPickingGoods_description(models.Model):
    _inherit = 'stock.picking.goods_description'

    @api.multi
    @api.depends('name')
    def _set_dim_name(self):
        for rec in self:
            rec.dim_name = self.env[
                'ir.model.synchro'].dim_text(rec.name)

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
        res = super(StockPickingGoods_description, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
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


class StockPickingCarriageCondition(models.Model):

    _inherit = "stock.picking.carriage_condition"

    @api.multi
    @api.depends('name')
    def _set_dim_name(self):
        for rec in self:
            rec.dim_name = self.env[
                'ir.model.synchro'].dim_text(rec.name)

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
        res = super(StockPickingCarriageCondition, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
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


class StockPickingTransportationReason(models.Model):

    _inherit = "stock.picking.transportation_reason"

    @api.multi
    @api.depends('name')
    def _set_dim_name(self):
        for rec in self:
            rec.dim_name = self.env[
                'ir.model.synchro'].dim_text(rec.name)

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
        res = super(StockPickingTransportationReason, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
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
    def synchro(self, vals, disable_post=None,
                only_minimal=None, no_deep_fields=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post,
            only_minimal=only_minimal, no_deep_fields=no_deep_fields)


class StockPickingTransportationMethod(models.Model):

    _inherit = "stock.picking.transportation_method"

    @api.multi
    @api.depends('name')
    def _set_dim_name(self):
        for rec in self:
            rec.dim_name = self.env[
                'ir.model.synchro'].dim_text(rec.name)

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
        res = super(StockPickingTransportationMethod, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
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
