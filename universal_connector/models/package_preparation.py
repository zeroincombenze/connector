# -*- coding: utf-8 -*-
#
# Copyright 2019-26 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class StockPickingPackagePreparation(models.Model):
    _name = "stock.picking.package.preparation"
    _inherit = ["stock.picking.package.preparation", "abstract.db.key"]

    original_state = fields.Char("Original Status", copy=False)

    @api.model_cr_context
    def _auto_init(self):
        res = super(StockPickingPackagePreparation, self)._auto_init()
        for prefix in ("vg7", "oe7", "oe8", "oe10"):
            self.env["ir.model.synchro"]._build_unique_index(self._inherit, prefix)
        return res

    @api.model
    def commit(self, id):
        return self.env["ir.model.synchro"].commit(self, id)

    @api.multi
    def pull_record(self):
        self.env["ir.model.synchro"].pull_record(self)


class StockPickingPackagePreparationLine(models.Model):
    _name = "stock.picking.package.preparation.line"
    _inherit = ["stock.picking.package.preparation.line", "abstract.db.key"]

    to_delete = fields.Boolean("Record to delete")

    @api.model_cr_context
    def _auto_init(self):
        res = super(StockPickingPackagePreparationLine, self)._auto_init()
        for prefix in ("vg7", "oe7", "oe8", "oe10"):
            self.env["ir.model.synchro"]._build_unique_index(self._inherit, prefix)
        return res


class StockPickingGoods_description(models.Model):
    _name = "stock.picking.goods_description"
    _inherit = ["stock.picking.goods_description", "abstract.db.key"]

    @api.multi
    @api.depends("name")
    def _set_dim_name(self):
        for ddt in self:
            ddt.dim_name = self.env["ir.model.synchro.cache"].hashname(ddt.name)

    dim_name = fields.Char(
        "Search Key", compute=_set_dim_name, store=True, readonly=True
    )

    @api.model_cr_context
    def _auto_init(self):
        res = super(StockPickingGoods_description, self)._auto_init()
        for prefix in ("vg7", "oe7", "oe8", "oe10"):
            self.env["ir.model.synchro"]._build_unique_index(self._inherit, prefix)
        return res


class StockPickingCarriageCondition(models.Model):
    _name = "stock.picking.carriage_condition"
    _inherit = ["stock.picking.carriage_condition", "abstract.db.key"]

    @api.multi
    @api.depends("name")
    def _set_dim_name(self):
        for rec in self:
            rec.dim_name = self.env["ir.model.synchro.cache"].hashname(rec.name)

    dim_name = fields.Char(
        "Search Key", compute=_set_dim_name, store=True, readonly=True
    )

    @api.model_cr_context
    def _auto_init(self):
        res = super(StockPickingCarriageCondition, self)._auto_init()
        for prefix in ("vg7", "oe7", "oe8", "oe10"):
            self.env["ir.model.synchro"]._build_unique_index(self._inherit, prefix)
        return res


class StockPickingTransportationReason(models.Model):
    _name = "stock.picking.transportation_reason"
    _inherit = ["stock.picking.transportation_reason", "abstract.db.key"]

    @api.multi
    @api.depends("name")
    def _set_dim_name(self):
        for rec in self:
            rec.dim_name = self.env["ir.model.synchro.cache"].hashname(rec.name)

    dim_name = fields.Char(
        "Search Key", compute=_set_dim_name, store=True, readonly=True
    )

    @api.model_cr_context
    def _auto_init(self):
        res = super(StockPickingTransportationReason, self)._auto_init()
        for prefix in ("vg7", "oe7", "oe8", "oe10"):
            self.env["ir.model.synchro"]._build_unique_index(self._inherit, prefix)
        return res


class StockPickingTransportationMethod(models.Model):
    _name = "stock.picking.transportation_method"
    _inherit = ["stock.picking.transportation_method", "abstract.db.key"]

    @api.multi
    @api.depends("name")
    def _set_dim_name(self):
        for rec in self:
            rec.dim_name = self.env["ir.model.synchro.cache"].hashname(rec.name)

    dim_name = fields.Char(
        "Search Key", compute=_set_dim_name, store=True, readonly=True
    )

    @api.model_cr_context
    def _auto_init(self):
        res = super(StockPickingTransportationMethod, self)._auto_init()
        for prefix in ("vg7", "oe7", "oe8", "oe10"):
            self.env["ir.model.synchro"]._build_unique_index(self._inherit, prefix)
        return res
