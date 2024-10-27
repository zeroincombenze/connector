#
# Copyright 2019-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

from odoo.addons.component.core import Component


class MetadataBatchImporter(Component):
    """ Import the records directly, without delaying the jobs.

    Import the Odoo Minimal Datas :
    * UOM
    * Product categories
    * Product attributes and theirs values

    They are imported directly because this is a rare and fast operation,
    and we don't really bother if it blocks the UI during this time.
    (that's also a mean to rapidly check the connectivity with Odoo).

    """

    _name = "odoo.metadata.batch.importer"
    _inherit = "odoo.direct.batch.importer"
    _apply_on = [
        "odoo.product.uom",
        "odoo.product.attribute",
        "odoo.product.attribute.value",
    ]
