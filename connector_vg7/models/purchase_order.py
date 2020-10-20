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


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)
    original_state = fields.Char('Original Status', copy=False)
    timestamp = fields.Datetime('Timestamp', copy=False, readonly=True)
    errmsg = fields.Char('Error message', copy=False, readonly=True)

    @api.model_cr_context
    def _auto_init(self):
        res = super(PurchaseOrder, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.model
    def commit(self, id):
        return self.env['ir.model.synchro'].commit(self, id)

    @api.model
    def synchro(self, vals, disable_post=None,
                only_minimal=None, no_deep_fields=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post,
            only_minimal=only_minimal, no_deep_fields=no_deep_fields)

    @api.multi
    def pull_record(self):
        self.env['ir.model.synchro'].pull_record(self)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)
    to_delete = fields.Boolean('Record to delete')

    @api.model_cr_context
    def _auto_init(self):
        res = super(PurchaseOrderLine, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    def assure_values(self, vals, rec):
        nm = 'product_id'
        if ((not isinstance(vals.get(nm), int) or not vals.get(nm))
                and not rec):
            product = self.env['product.product'].search(
                [('default_code', '=', 'MISC')])
            if not product:
                product = self.env['product.product'].search(
                    [], limit=1)
            if product:
                product = product[0]
                vals[nm] = product.id
        if not vals.get('price_unit') and not rec:
            vals['price_unit'] = 0.0
        return vals

    @api.model
    def synchro(self, vals, disable_post=None,
                only_minimal=None, no_deep_fields=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post,
            only_minimal=only_minimal, no_deep_fields=no_deep_fields)
