#
# Copyright 2019-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging

from odoo import api, fields, models

# from odoo.tools.translate import _
# from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WizardSynchroPullRecord(models.TransientModel):
    _name = "wizard.synchro.pull.record"
    _description = "Pull Records from counterparty"

    backend_id = fields.Many2one("synchro.channel", required=True, string="Backend")
    dir_mapper_id = fields.Many2one(
        comodel_name="synchro.channel.model",
        string="Model",
        # domain=lambda self: self._get_backend_domain(),
        help="Select model to import",
    )
    # sel_rec = fields.Selection(
    #     [
    #         ("all", "All Records"),
    #         ("new", "New Records"),
    #         ("upd", "Refresh Records"),
    #         ("unk", "Only Unknown Records"),
    #     ],
    #     "Which Records",
    #     default="new",
    #     help="Selet which records you want to import",
    # )
    remote_ids = fields.Char(
        "Remote IDs",
        help="List of remote Ids, comma or space separated;\n"
        "you can declare a range using format low-high;\n"
        'i.e.  "4 10-12" declares records 4,10,11,12.\n'
        "Leave empty to import all IDs",
    )

    @api.onchange("backend_id")
    def onchange_backend_id(self):
        return {
            "domain": {
                "dir_mapper_id": [("synchro_channel_id", "=", self.backend_id.id)]
            }
        }

    # @api.onchange("ir_model_id")
    # def onchange_model_id(self):
    #     recs = self.env["synchro.channel.model"].search(
    #         [("name", "=", self.ir_model_id.res_model), ("model_spec", "=", False)]
    #     )
    #     rec_counter = 0
    #     for rec in recs:
    #         if rec.rec_counter > rec_counter:
    #             rec_counter = rec.rec_counter
    #     if rec_counter:
    #         self.remote_ids = "%s-" % (rec_counter + 1)

    def evaluate_remote_ids(self):
        remote_ids = []
        for item in (
            self.remote_ids.strip()
            .replace("[", "")
            .replace("]", "")
            .replace(",", " ")
            .replace("  ", " ")
            .split(" ")
        ):
            if item.strip().isdigit():
                remote_ids.append(int(item))
            else:
                if "-" not in item:
                    continue
                low, high = item.split("-", 1)
                if low.strip().isdigit():
                    low = int(low)
                elif high.strip().isdigit():
                    low = max(int(high) - 100, 1)
                else:
                    low = 1
                if high.strip().isdigit():
                    high = int(high)
                else:
                    high = low + 100
                remote_ids += eval("range(%d,%d)" % (low, high + 1))
        return remote_ids

    def pull_full_records(self):
        Cache = self.env["ir.model.synchro.cache"]
        remote_ids = self.evaluate_remote_ids()
        for res_id in remote_ids:
            Cache.que_push(
                self.backend_id,
                "trigger",
                self.dir_mapper_id.counterpart_name,
                res_id,
                4,
                {},
                prio=2,
            )
        local_ids = self.backend_id.synchro_queue(commit=True)
        return {
            "name": "Data imported",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": self.dir_mapper_id.name,
            "type": "ir.actions.act_window",
            "domain": [("id", "in", local_ids)],
            "view_id": False,
        }
