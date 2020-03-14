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
# from odoo.tools.translate import _
# from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WizardExportFatturapa(models.TransientModel):
    _name = "wizard.synchro.pull.records"
    _description = "Pull Records from counterpart"

    ir_model_id = fields.Many2one(
        comodel_name='ir.model')
    sel_rec = fields.Selection([
        ('all', 'All Records'),
        ('new', 'New Records'),
        ('upd', 'Refresh Records'),
        ('unk', 'Only Unknown Records')],
        'Which Records',
        default='new',
    )

    def pull_full_records(self):
        ir_model = self.env['ir.model']
        ir_model_synchro = self.env['ir.model.synchro']
        only_model = None
        if self.ir_model_id:
            only_model = ir_model.browse(self.ir_model_id.id).model
        if self.sel_rec == 'unk':
            ir_model_synchro.pull_recs_2_complete(only_model=only_model)
        else:
            local_ids =ir_model_synchro.pull_full_records(
                # force=force,
                only_model=only_model,
                select=self.sel_rec)
        return {
            'name': "Data imported",
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': only_model,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', local_ids)],
            'view_id': False,
        }
