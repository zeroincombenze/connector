# -*- coding: utf-8 -*-
# Copyright 2019 Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import os
import logging
from odoo import models, api
from odoo.exceptions import UserError
import urllib2, ssl

_logger = logging.getLogger(__name__)


class StockPickingPackagePreparation(models.Model):
    _inherit = 'stock.picking.package.preparation'

    @api.multi
    def set_done(self):
        super(StockPickingPackagePreparation, self).set_done()

        magento_model = self.env['magento.configure']
        ids = magento_model.search([('active', '!=', False)])
        if not ids:
            raise UserError('Magento configuration not found!')
        root_url = magento_model.browse(ids[0].id).name

        order_closed = []
        for package in self:
            for pick in package.picking_ids:
                if not pick.sale_id:
                    continue
                order_number = pick.sale_id.name
                url = '%s/service/completa_ordine.php' % root_url
                params = 'OdooOrder=%s' % order_number
                uri = '%s?%s' % (url, params)
                _logger.info('Close Magento Order by %s' % uri)
                try:
                    # response = urllib2.urlopen(uri).read()
                     os.system('wget --delete-after %s' % uri)
                except urllib2.HTTPError:
                    _logger.error('Magento Order error by <%s>' % uri)
                    raise UserError(
                        'Errore in aggiornamento da Magento <%s>' % uri)
        return True
