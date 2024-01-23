# Copyright 2021 powERP enterprise network <https://www.powerp.it>
# Copyright 2021 SHS-AV s.r.l. <https://www.zeroincombenze.it>
# Copyright 2021 Didotech s.r.l. <https://www.didotech.com>
#
# License LGPL-3 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
#
from odoo import api, SUPERUSER_ID


def set_available_protocol(cr):
    """Set protocol available for Odoo identities

    Args:
        cr (obj): sql cursor

    Returns:
        None
    """
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        identity_model = env["synchro.connector.identity"]
        for identity in identity_model.search([]):
            if not identity.is_odoo():
                continue
            if "http+json" not in identity.enabled_protocols:
                identity.enabled_protocols = identity.enabled_protocols + ",http+json"
            if "https+json" not in identity.enabled_protocols:
                identity.enabled_protocols = identity.enabled_protocols + ",https+json"


def set_available_protocol_post(cr, registry):
    set_available_protocol(cr)
