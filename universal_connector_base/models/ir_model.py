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
        running_in_queue=None,
    ):
        return self.env["ir.model.synchro"].synchro(
            self,
            vals,
            backend=backend,
            only_minimal=only_minimal,
            ttl=ttl,
            running_in_queue=running_in_queue,
        )

    @api.multi
    def pull_record(self):
        SynchroModel = self.env["synchro.channel.model"]
        for backend in self.env["synchro.channel"].search(
            [], order="sequence desc,name desc"
        ):
            synchro_model = SynchroModel.get_synchro_model_from_loc(backend, self._name)
            if not synchro_model:
                continue
            loc_ext_id = synchro_model.get_loc_ext_id()
            if hasattr(self, loc_ext_id) and getattr(self, loc_ext_id):
                self.env["ir.model.synchro"].trigger_one_record(
                    synchro_model.counterpart_name,
                    backend.prefix,
                    synchro_model.get_external_pk(getattr(self, loc_ext_id)),
                )
