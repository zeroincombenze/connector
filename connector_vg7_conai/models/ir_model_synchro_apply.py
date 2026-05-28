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
from odoo import models

_logger = logging.getLogger(__name__)


class IrModelSynchroApply(models.Model):
    _inherit = "ir.model.synchro.apply"

    def apply_conai(
        self,
        backend,
        vals,
        loc_name,
        ext_ref,
        loc_ext_id_name,
        vmodel,
        default=None,
        ctx=None,
    ):
        if (loc_name not in vals or not vals.get(loc_name)) and not vals.get(ext_ref):
            if "product_id" in vals:
                product = self.env["product.product"].browse(vals["product_id"])
                vals[loc_name] = product.conai_category_id.id
        return vals
