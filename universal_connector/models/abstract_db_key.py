from odoo import api, fields, models


class AbstractDBKey(models.AbstractModel):
    _name = "abstract.db.key"
    _description = "Abstract DB Key"

    vg7_id = fields.Integer("VG7 ID", copy=False)
    oe7_id = fields.Integer("Odoo7 ID", copy=False)
    oe8_id = fields.Integer("Odoo8 ID", copy=False)
    oe10_id = fields.Integer("Odoo10 ID", copy=False)
    oe12_id = fields.Integer("Odoo12 ID", copy=False)
    timestamp = fields.Datetime("Timestamp", copy=False, readonly=True)
    errmsg = fields.Char("Error message", copy=False, readonly=True)

    @api.model
    def synchro(
            self, vals, chk_in_queue=None, only_minimal=None, no_deep_fields=None,
            no_del_child=False
    ):
        return self.env["ir.model.synchro"].synchro(
            self,
            vals,
            chk_in_queue=chk_in_queue,
            only_minimal=only_minimal,
            no_deep_fields=no_deep_fields,
            no_del_child=no_del_child,
        )
