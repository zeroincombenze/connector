# -*- coding: utf-8 -*-
#
# Copyright 2019-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging
from openerp.osv import orm, fields

_logger = logging.getLogger(__name__)

try:
    import oerplib
except ImportError as err:
    _logger.error(err)


class AccountInvoice(orm.Model):
    _inherit = 'account.invoice'

    def send_synchro(self, cr, uid, ids):
        ir_model = self.pool['ir.model']
        model = self.__class__.__name__
        cnx, session = ir_model.rpc_session()
        prefix = ir_model.get_prefix()
        retcode = 0
        for this in self.browse(cr, uid, ids):
            try:
                retcode = cnx.execute('ir.model.synchro',
                                      'trigger_one_record',
                                      model,
                                      prefix,
                                      this.id)
            except BaseException:
                _logger.error('Connector VG7 not installed by counterpart')
                raise UserError(
                    _('Connector VG7 not installed by counterpart'))
                retcode = -1
            if retcode < 0:
                raise UserError(
                    _('Remote error %d' % retcode))
                break
        return (retcode > 0)
