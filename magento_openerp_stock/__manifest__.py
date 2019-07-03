# -*- coding: utf-8 -*-
##########################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
##########################################################################

{
    'name': 'MOB Stock Management',
    'version': '1.0.2',
    'category': 'Generic Modules',
    'author': 'Webkul Software Pvt. Ltd.',
    'website': 'https://store.webkul.com/Magento-OpenERP-Bridge.html',
    'sequence': 1,
    'summary': 'MOB Stock Extension',
    'description': """
MOB Stock Extesnion
=========================
    Stock Management From Odoo To Magento.

    This module will automatically manage stock from odoo to magento during below operations.

    1. Sales Order
    2. Purchase Order
    3. Point Of Sales

	NOTE : This module works very well with latest version of magento 1.9 and latest version of Odoo 10.0.
    """,
    'depends': ['magento_bridge'],
    'data': [
            'views/res_config_view.xml',
    ],
    'application': True,
    'installable': True,
    'active': False,
    'pre_init_hook': 'pre_init_check',
}
