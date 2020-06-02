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


class SaleOrder(models.Model):
    _inherit = "sale.order"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)
    original_state = fields.Char('Original Status', copy=False)
    timestamp = fields.Datetime('Timestamp', copy=False, readonly=True)
    errmsg = fields.Char('Error message', copy=False, readonly=True)

    CONTRAINTS = []
    DEFAULT = {}

    @api.model_cr_context
    def _auto_init(self):
        res = super(SaleOrder, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.model
    def __preprocess(self, channel_id, vals):
        xmodel = 'sale.order'
        stored_field = 'agent_id'
        _logger.info(
            '%s.preprocess(%s)' % (xmodel, vals))
        cache = self.env['ir.model.synchro.cache']
        cache.del_model_attr(channel_id, xmodel, stored_field)
        if 'vg7:agent_id' in vals:
            agent_id, agent = self.bind_record(
                channel_id, xmodel, {'vg7_id': int(vals['vg7:agent_id'])})
            if agent_id:
                vals['user_id'] = agent_id
                cache.set_model_attr(
                    channel_id, xmodel, stored_field, agent_id)
            del vals['vg7:agent_id']
        elif 'vg7:customer_id' in vals:
            partner_id, partner = self.bind_record(
                channel_id, 'res.partner',
                {'vg7_id': int(vals['vg7:customer_id'])})
            if partner:
                vals['user_id'] = partner.agents[0].id
        return vals, ''

    def __postprocess(self, channel_id, parent_id, vals):
        # _logger.info(
        #     '> postprocess(%d,%s)' % (parent_id, vals))  # debug
        return False

    @api.model
    def set_defaults(self):
        for nm in ('pricelist_id',
                   'payment_term_id',
                   'fiscal_position_id'):
            if nm == 'fiscal_position_id':
                partner_nm = 'property_account_position_id'
            else:
                partner_nm = 'property_%s' % nm
            if not getattr(self, nm):
                setattr(self, nm, getattr(self.partner_id, partner_nm))
        for nm in ('goods_description_id',
                   'carriage_condition_id',
                   'transportation_reason_id',
                   'transportation_method_id'):
            if hasattr(self, nm) and not getattr(self, nm):
                setattr(self, nm, getattr(self.partner_id, nm))
        for nm in ('partner_invoice_id',
                   'partner_shipping_id'):
            if not getattr(self, nm):
                setattr(self, nm, self.partner_id.id)
        nm = 'note'
        partner_nm = 'sale_note'
        if not getattr(self, nm):
            setattr(self, nm, getattr(self.company_id, partner_nm))

    def assure_values(self, vals, rec):
        for nm in ('partner_shipping_id', 'partner_invoice_id'):
            if isinstance(vals.get(nm), int) and vals[nm] <= 0:
                del vals[nm]
            if not vals.get(nm) and not rec:
                vals[nm] = vals['partner_id']
        return vals

    @api.model
    def synchro(self, vals, disable_post=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post)

    @api.model
    def commit(self, id):
        return self.env['ir.model.synchro'].commit(self, id)

    @api.multi
    def pull_record(self):
        self.env['ir.model.synchro'].pull_record(self)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)
    to_delete = fields.Boolean('Record to delete')

    CONTRAINTS = []

    @api.model_cr_context
    def _auto_init(self):
        res = super(SaleOrderLine, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.model
    def synchro(self, vals, disable_post=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post)
