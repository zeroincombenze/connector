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


class ProjectProject(models.Model):
    _inherit = "project.project"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)

    CONTRAINTS = []

    @api.model_cr_context
    def _auto_init(self):
        res = super(ProjectProject, self)._auto_init()
        for prefix in ('vg7', 'oe7', 'oe8', 'oe10'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.model
    def synchro(self, vals, disable_post=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post)

    @api.multi
    def pull_record(self):
        self.env['ir.model.synchro'].pull_record(self)


class ProjectTags(models.Model):
    _inherit = "project.tags"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)

    CONTRAINTS = []

    @api.model_cr_context
    def _auto_init(self):
        res = super(ProjectTags, self)._auto_init()
        for prefix in ('vg7', 'oe7'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.model
    def synchro(self, vals, disable_post=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post)


class ProjectTask(models.Model):
    _inherit = "project.task"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)

    CONTRAINTS = []

    @api.model_cr_context
    def _auto_init(self):
        res = super(ProjectTask, self)._auto_init()
        for prefix in ('vg7', 'oe7'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.model
    def synchro(self, vals, disable_post=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post)


class ProjectTaskType(models.Model):
    _inherit = "project.task.type"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)

    CONTRAINTS = []

    @api.model_cr_context
    def _auto_init(self):
        res = super(ProjectTaskType, self)._auto_init()
        for prefix in ('vg7', 'oe7'):
            self.env['ir.model.synchro']._build_unique_index(self._inherit,
                                                             prefix)
        return res

    @api.model
    def synchro(self, vals, disable_post=None):
        return self.env['ir.model.synchro'].synchro(
            self, vals, disable_post=disable_post)
