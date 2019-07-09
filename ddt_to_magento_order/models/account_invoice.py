# -*- coding: utf-8 -*-
# Copyright 2019 Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import os
import logging
from odoo import models, api
from odoo.exceptions import UserError
import urllib2
import ssl

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()

        magento_model = self.env['magento.configure']
        ids = magento_model.search([('active', '!=', False)])
        if not ids:
            raise UserError('Magento configuration not found!')
        root_url = magento_model.browse(ids[0].id).name

        order_closed = []
        for invoice in self:
            for line in invoice.invoice_line_ids:
                if not line.sale_line_ids:
                    continue
                order_number = line.sale_line_ids.order_id.name
                if order_number in order_closed:
                    continue
                order_closed.append(order_number)
                url = '%s/service/completa_ordine.php' % root_url
                params = 'OdooOrder=%s' % order_number
                uri = '%s?%s' % (url, params)
                _logger.info('Close Magento Order by %s' % uri)
                try:
                    os.system('wget --delete-after %s' % uri)
                except urllib2.HTTPError:
                    _logger.error('Magento Order error by <%s>' % uri)
                    raise UserError(
                        'Errore in aggiornamento da Magento <%s>' % uri)
        return res
