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

from odoo import fields, models
# from odoo.tools.translate import _
# from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WizardExportFatturapa(models.TransientModel):
    _name = "wizard.synchro.pull.records"
    _description = "Pull Records from counterpart"

    ir_model_id = fields.Many2one(
        comodel_name='ir.model',
        help='Select model to import')
    sel_rec = fields.Selection([
        ('all', 'All Records'),
        ('new', 'New Records'),
        ('upd', 'Refresh Records'),
        ('unk', 'Only Unknown Records')],
        'Which Records',
        default='new',
        help='Selet which records you want to import'
    )
    nesting_level = fields.Selection([
        ('all', 'All Level'),
        ('no_deep', 'No Deep'),
        ('min', 'No Deep, minimal data')],
        'Nesting Level',
        default='all',
        help='Set what system does with related record (*many records)\n'
             'All Level means recurse to import all related record\n'
             'No Deep does not import related record (field will be null)\n'
             'Minimal data mean only some values are stored in DB'
    )
    remote_ids = fields.Char('Remote IDs',
        help='List of remote Ids, comma or space separated;\n'
             'you can declare a range using format low-high;\n'
             'i.e.  "4 10-12" declares records 4,10,11,12.\n'
             'Leave empty to import all IDs'
    )

    def pull_full_records(self):
        ir_model = self.env['ir.model']
        ir_model_synchro = self.env['ir.model.synchro']
        only_model = None
        no_deep_fields = None
        only_minimal = False
        if self.nesting_level != 'all':
            no_deep_fields = ['*']
            if self.nesting_level == 'min':
                only_minimal = True
        if self.ir_model_id:
            only_model = ir_model.browse(self.ir_model_id.id).model
        if self.sel_rec == 'unk':
            ir_model_synchro.pull_recs_2_complete(only_model=only_model)
        else:
            local_ids =ir_model_synchro.pull_full_records(
                # force=force,
                only_model=only_model,
                select=self.sel_rec,
                only_minimal=only_minimal,
                no_deep_fields=no_deep_fields,
                remote_ids=self.remote_ids)
        return {
            'name': "Data imported",
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': only_model,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', local_ids)],
            'view_id': False,
        }
