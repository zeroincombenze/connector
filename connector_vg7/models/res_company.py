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

try:
    from unidecode import unidecode
except ImportError as err:
    _logger.debug(err)


class ResCompany(models.Model):
    _inherit = "res.company"

    vg7_id = fields.Integer('VG7 ID', copy=False)
    oe7_id = fields.Integer('Odoo7 ID', copy=False)
    oe8_id = fields.Integer('Odoo8 ID', copy=False)
    oe10_id = fields.Integer('Odoo10 ID', copy=False)

    @api.model
    def __preprocess(self, channel_id, vals):
        _logger.info(
            '> preprocess(%s)' % vals)      # debug
        cache = self.env['ir.model.synchro.cache']
        min_vals = {}
        loc_id = False
        ext_id = False
        loc_ext_id = False
        model = 'res.company'
        stored_field = '__%s' % model
        for ext_ref in vals:
            ext_name, loc_name, is_foreign = self.env[
                'ir.model.synchro'].name_from_ref(channel_id, model, ext_ref)
            if ext_name == 'id':
                ext_id = vals[ext_ref]
                loc_ext_id = loc_name
            elif loc_id == 'id':
                loc_id = vals[ext_ref]
            if (not cache.get_struct_model_field_attr(
                    model, loc_name, 'ttype') in (
                    'many2one', 'one2many', 'many2many') or
                    cache.get_struct_model_field_attr(
                        model, loc_name, 'required')):
                min_vals[ext_ref] = vals[ext_ref]
        if (ext_id and
                not self.env[model].search([(loc_ext_id, '=', ext_id)]) or
                loc_id and not self.env[model].search([('id', '=', loc_id)])):
            cache.set_model_attr(
                channel_id, model, stored_field, vals)
            vals = min_vals
        return vals, ''

    @api.model
    def __postprocess(self, channel_id, parent_id, vals):
        _logger.info(
            '> postprocess(%d,%s)' % (parent_id, vals))  # debug
        cache = self.env['ir.model.synchro.cache']
        model = 'res.company'
        stored_field = '__%s' % model
        if cache.get_model_attr(channel_id, model, stored_field):
            vals = cache.get_model_attr(channel_id, model, stored_field)
            cache.del_model_attr(channel_id, model, stored_field)
            self.synchro(vals, disable_post=True)

    @api.model_cr_context
    def _auto_init(self):
        res = super(ResCompany, self)._auto_init()
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
