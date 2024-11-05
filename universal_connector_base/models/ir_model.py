#
from odoo import api, models


class BaseModel(models.BaseModel):

    _inherit = "base"

    @api.model
    def bind_external_ref(self, loc_ext_id, ext_id):
        if not hasattr(self, loc_ext_id):  # pragma: no cover
            recs = []
        else:
            recs = self.search([(loc_ext_id, "=", ext_id)])
        return recs[0] if recs else self.env[self._name]

    @api.model
    def synchro(
        self,
        vals,
        backend=None,
        only_minimal=True,
        ttl=None,
    ):
        return self.env["ir.model.synchro"].synchro(
            self,
            vals,
            backend=backend,
            only_minimal=only_minimal,
            ttl=ttl,
        )
