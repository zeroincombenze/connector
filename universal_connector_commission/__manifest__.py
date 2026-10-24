# -*- coding: utf-8 -*-
#
# Copyright 2026 Zeroincombenze srls <https://www.zeroincombenze.it>
#
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
{
    "name": "Universal Connector - Commissions",
    "version": "10.0.0.1.0",
    "category": "Generic Modules",
    "summary": "Universal Connector plug-in for agents and commissions",
    "author": "Zeroincombenze srls",
    "website": "https://www.zeroincombenze.it/",
    "development_status": "Beta",
    "license": "AGPL-3",
    "depends": [
        "universal_connector",
        "sale_commission",
    ],
    "data": [
        "views/partner_view.xml",
        "data/synchro_partner.xml",
        "data/synchro_sale_order.xml",
    ],
    "installable": True,
    "auto_install": True,
}
