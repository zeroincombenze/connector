# -*- coding: utf-8 -*-
#
# Copyright 2019-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
def migrate(cr, version):
    cr.execute("""
        UPDATE res_partner set vg7_id = null
        where (vg7_id >= 100000000 and vg7_id < 200000000) or
              (type = 'delivery' and vg7_id < 100000000) or
              (type <> 'contact' and (name = '' or name is null));
    """
    )
    cr.execute("""
        UPDATE res_partner set parent_id = null
        where parent_id is not null and type = 'contact';
    """
    )
    cr.execute("""
        DELETE from res_partner
        where (name = '' or name is null) and
              (vg7_id = 0 or vg7_id is null) and
              id not in (select partner_id from sale_order
                         group by partner_id) and
              id not in (select partner_shipping_id from sale_order
                         group by partner_shipping_id) and
              id not in (select partner_invoice_id from sale_order
                         group by partner_invoice_id) and
              id not in (select partner_id from account_invoice
                         group by partner_id) and
              id not in (select partner_shipping_id from account_invoice
                         group by partner_shipping_id);
    """
    )
