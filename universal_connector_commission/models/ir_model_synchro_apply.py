# -*- coding: utf-8 -*-
#
# Copyright 2026 Zeroincombenze srls <https://www.zeroincombenze.it>
#
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import models


class IrModelSynchroApply(models.Model):
    _inherit = "ir.model.synchro.apply"

    def apply_agent_user(
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
        """Agent from agent_id -> partner (vg73_id):
        - set salesman (user linked to agent partner) if not yet set
        - assign agent to order customer if customer has no agent
        """
        agent_id = vals.pop(ext_ref, False) if ext_ref else False
        try:
            agent_id = int(agent_id or 0)
        except (TypeError, ValueError):
            agent_id = 0
        if not agent_id:
            return vals
        agent = self.env["res.partner"].search(
            [("vg73_id", "=", agent_id)], limit=1)
        if not agent:
            return vals
        if loc_name not in vals:
            user = self.env["res.users"].search(
                [("partner_id", "=", agent.id)], limit=1)
            if user:
                vals[loc_name] = user.id
        if isinstance(vals.get("partner_id"), (int, long)) and vals["partner_id"] > 0:
            customer = self.env["res.partner"].browse(vals["partner_id"])
            if customer.exists() and not customer.agents:
                customer.write({"agents": [(4, agent.id)]})
        return vals
