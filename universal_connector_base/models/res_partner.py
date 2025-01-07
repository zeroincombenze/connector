#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    oe7_id = fields.Integer("Odoo7 ID", copy=False)
    oe8_id = fields.Integer("Odoo8 ID", copy=False)
    odoo10_id = fields.Integer("Odoo10 ID", copy=False)
    odoo12_id = fields.Integer("Odoo12 ID", copy=False)
    odoo16_id = fields.Integer("Odoo16 ID", copy=False)
    timestamp = fields.Datetime("Timestamp", copy=False, readonly=True)
    errmsg = fields.Char("Error message", copy=False, readonly=True)

    CONTRAINTS = [["id", "!=", "parent_id"]]

    @api.model_cr_context
    def _auto_init(self):
        res = super()._auto_init()
        self.env["synchro.backend"]._build_all_indexes(self)
        return res

    @api.model
    def synchro(
        self,
        vals,
        only_minimal=True,
        ttl=None,
        running_in_queue=None,
        jacket=None,
        model_spec=False,
        backend=None,
        dir_mapper=None,
        ctx=None,
    ):
        if only_minimal:
            vals[":type"] = vals.get(
                ":type",
                {
                    "shipping": "delivery",
                    "invoice": "invoice",
                    "supplier": "contact",
                }.get(model_spec, "contact"),
            )
            if model_spec == "supplier":
                vals[":supplier"] = True
        return super().synchro(
            vals,
            only_minimal=only_minimal,
            ttl=ttl,
            running_in_queue=running_in_queue,
            jacket=jacket,
            model_spec=model_spec,
            backend=backend,
            dir_mapper=dir_mapper,
            ctx=ctx,
        )


class ResCategory(models.Model):
    _inherit = "res.partner.category"

    oe7_id = fields.Integer("Odoo7 ID", copy=False)
    oe8_id = fields.Integer("Odoo8 ID", copy=False)
    odoo10_id = fields.Integer("Odoo10 ID", copy=False)
    odoo12_id = fields.Integer("Odoo12 ID", copy=False)
    odoo16_id = fields.Integer("Odoo16 ID", copy=False)

    @api.model_cr_context
    def _auto_init(self):
        res = super()._auto_init()
        self.env["synchro.backend"]._build_all_indexes(self)
        return res
