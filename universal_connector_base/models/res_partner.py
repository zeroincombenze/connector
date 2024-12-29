#
# Copyright 2018-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
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
    oe10_id = fields.Integer("Odoo10 ID", copy=False)
    oe12_id = fields.Integer("Odoo12 ID", copy=False)
    oe16_id = fields.Integer("Odoo16 ID", copy=False)
    timestamp = fields.Datetime("Timestamp", copy=False, readonly=True)
    errmsg = fields.Char("Error message", copy=False, readonly=True)

    CONTRAINTS = [["id", "!=", "parent_id"]]

    @api.model_cr_context
    def _auto_init(self):
        res = super()._auto_init()
        self.env["synchro.channel"]._build_all_indexes(self)
        return res

    @api.model
    def synchro(
        self,
        vals,
        backend=None,
        only_minimal=True,
        ttl=None,
        running_in_queue=None,
        jacket=None,
        logrec=None,
        ctx=None,
    ):
        if only_minimal:
            vals[":type"] = vals.get(":type", "contact")
        return super().synchro(
            vals,
            backend=backend,
            only_minimal=only_minimal,
            ttl=ttl,
            running_in_queue=running_in_queue,
            jacket=jacket,
            logrec=logrec,
            ctx=ctx,
        )


class ResCategory(models.Model):
    _inherit = "res.partner.category"

    oe7_id = fields.Integer("Odoo7 ID", copy=False)
    oe8_id = fields.Integer("Odoo8 ID", copy=False)
    oe10_id = fields.Integer("Odoo10 ID", copy=False)
    oe12_id = fields.Integer("Odoo12 ID", copy=False)
    oe16_id = fields.Integer("Odoo16 ID", copy=False)

    @api.model_cr_context
    def _auto_init(self):
        res = super()._auto_init()
        self.env["synchro.channel"]._build_all_indexes(self)
        return res
