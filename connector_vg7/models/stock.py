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


class StockLocation(models.Model):
    _inherit = "stock.location"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)

    @api.model_cr_context
    def _auto_init(self):
        res = super(StockLocation, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)

    @api.model_cr_context
    def _auto_init(self):
        res = super(StockWarehouse, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res


class StockMove(models.Model):
    _inherit = "stock.move"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)
    timestamp = fields.Datetime('Timestamp', copy=False, readonly=True)
    errmsg = fields.Char('Error message', copy=False, readonly=True)

    @api.model_cr_context
    def _auto_init(self):
        res = super(StockMove, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    def assure_values(self, vals, rec):
        apply = self.env['ir.model.synchro.apply']
        product = False
        if 'product_id' not in vals and not rec:
            product = apply.get_default_product()
        if 'product_uom' not in vals and not rec:
            if not product:
                product = self.env['product.product'].browse(
                    vals['product.id'])
            vals['product_uom'] = product.uom_po_id.id
        if 'location_id' not in vals:
            vals['location_id'] = apply.get_default_location_id()
        return vals

    @api.model
    def synchro(self, vals, disable_post=None,
                only_minimal=None, no_deep_fields=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post,
            only_minimal=only_minimal, no_deep_fields=no_deep_fields)

    @api.multi
    def pull_record(self):
        self.env['ir.model.synchro'].pull_record(self)



class StockPicking(models.Model):
    _inherit = "stock.picking"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)
    timestamp = fields.Datetime('Timestamp', copy=False, readonly=True)
    errmsg = fields.Char('Error message', copy=False, readonly=True)

    @api.model_cr_context
    def _auto_init(self):
        res = super(StockPicking, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.model
    def synchro(self, vals, disable_post=None,
                only_minimal=None, no_deep_fields=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post,
            only_minimal=only_minimal, no_deep_fields=no_deep_fields)

    @api.multi
    def pull_record(self):
        self.env['ir.model.synchro'].pull_record(self)
