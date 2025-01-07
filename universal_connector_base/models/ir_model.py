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
        only_minimal=True,
        ttl=None,
        running_in_queue=None,
        jacket=None,
        model_spec=False,
        backend=None,
        dir_mapper=None,
        ctx=None,
    ):
        return self.env["ir.model.synchro"].synchro(
            self,
            vals,
            only_minimal=only_minimal,
            ttl=ttl,
            running_in_queue=running_in_queue,
            jacket=jacket,
            model_spec=model_spec,
            backend=backend,
            dir_mapper=dir_mapper,
            ctx=ctx,
        )

    @api.multi
    def pull_record(self):
        for backend in self.env["synchro.backend"].search(
            [], order="sequence desc,name desc"
        ):
            dir_mapper = backend.get_dir_mapper(model=self._name)
            if not dir_mapper:  # pragma: no cover
                continue
            loc_ext_id = dir_mapper.get_loc_ext_id()
            if hasattr(self, loc_ext_id) and getattr(self, loc_ext_id):
                self.env["ir.model.synchro"].trigger_one_record(
                    dir_mapper.counterpart_name,
                    backend.prefix,
                    dir_mapper.get_external_pk(getattr(self, loc_ext_id)),
                )
