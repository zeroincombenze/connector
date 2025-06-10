#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from future.utils import PY3
from datetime import datetime, timedelta
import json
import logging

# import odoo
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from python_plus import _u

_logger = logging.getLogger(__name__)


class SynchroLog(models.Model):
    _name = "synchro.log"
    _description = "Universal Connector Logger"
    _order = "timestamp desc, id desc"

    LOGLEVEL = "3"
    loglevel2num = {
        "error": "4",
        "info": "3",
        "warning": "2",
        "debug": "1",
        "none": "0",
    }

    timestamp = fields.Datetime("Timestamp", copy=False)
    res_model = fields.Char("Model")
    res_id = fields.Integer("Model ID")
    errmsg = fields.Char("Error message", copy=False)
    errcode = fields.Integer("Error code", copy=False)
    loglevel = fields.Char("Log level")
    values = fields.Text("Values of message", copy=False)
    reference = fields.Char(
        string="Reference", compute="_compute_reference", readonly=True, store=False
    )
    backend_id = fields.Many2one("synchro.backend", "Backend", copy=False)

    @api.depends("res_model", "res_id")
    def _compute_reference(self):  # pragma: no cover
        for res in self:
            res.reference = "%s,%s" % (res.res_model, res.res_id)

    def pretty_print(self, values):  # pragma: no cover
        def to_str(obj):
            x = str(obj)
            return x if (hasattr(obj, "len") and len(x) < 512) else "[...]"

        if isinstance(values, dict):
            return (
                json.dumps(
                    {
                        k: (
                            v[0:60] + "[...]"
                            if isinstance(v, str) and len(v) > 64
                            else v
                        )
                        for k, v in values.items()
                    },
                    default=to_str,
                    indent=2,
                )
                .replace(": false", ": False")
                .replace(": true", ": True")
            )
        return json.dumps(values, indent=2)

    def logger(
        self,
        hdr_msg,
        body_msg,
        errcode,
        res_model,
        loglevel,
        recloglevel,
        upd_log=None,
        res_rec=None,
        res_id=None,
        backend=None,
    ):
        now = datetime.now()
        if not PY3:
            now = now.strftime("%Y-%m-%d %H:%M:%S.%f")
        vals = {}
        if upd_log:
            if not self.res_model:
                vals["res_model"] = res_model
            if not self.errcode and errcode:
                vals["errcode"] = errcode
            if not self.res_id and res_id:
                vals["res_id"] = res_id
            if not self.backend_id and backend:
                vals["backend_id"] = backend.id
            if hdr_msg:
                vals["errmsg"] = hdr_msg
            if not self.values:
                vals["values"] = body_msg
            elif body_msg:
                vals["values"] = self.values + "\n\n--------\n" + body_msg
            try:
                self.write_log(vals)
                logrec = self
            except BaseException:
                return self.logger(
                    hdr_msg,
                    body_msg,
                    errcode,
                    res_model,
                    loglevel,
                    recloglevel,
                    upd_log=False,
                    res_rec=res_rec,
                    res_id=res_id,
                    backend=backend,
                )
        else:
            vals["timestamp"] = now
            vals["res_model"] = res_model
            vals["errcode"] = errcode
            vals["res_id"] = res_id
            for name, lev in self.loglevel2num.items():
                if int(lev) == (recloglevel or loglevel):
                    vals["loglevel"] = name
                    break
            if backend:
                vals["backend_id"] = backend.id
            vals["errmsg"] = hdr_msg or _("No Error")
            if res_rec and len(res_rec) > 1:
                vals["errmsg"] += " # (%s)" % ",".join([str(x.id) for x in res_rec])
            vals["values"] = body_msg
            logrec = self.create_log(vals)
        if res_rec and hasattr(res_rec, "timestamp") and hasattr(res_rec, "errmsg"):
            res_rec.write({"timestamp": now, "errmsg": hdr_msg})
        return logrec or self.env["synchro.log"]

    def purge_log(self):
        for day in (15, 8, 7, 5, 3, 2, 1):
            last = (datetime.today() - timedelta(day)).strftime("%Y-%m-%d %H:%M:%S")
            domain = [("timestamp", ">=", last)]
            nrecs = self.search_count(domain)
            domain = [("timestamp", "<", last)]
            if nrecs < 10000:
                break
        max_recs_per_session = 1000
        for rec in self.search(domain, order="timestamp desc"):  # pragma: no cover
            rec.unlink()
            max_recs_per_session -= 1
            if not max_recs_per_session:
                break

    def logmsg(
        self,
        loglevel,
        msg_text,
        res_rec=None,
        res_model=None,
        res_id=None,
        values=None,
        backend=None,
        errcode=None,
        errmsg=None,
        ctx=None,
    ):
        # ctx values:
        # - model: res_model
        # - id: res_id
        # - backend: backend.name
        # - lgi_ep: login endpoint
        # - data_ep: data endpoint
        # - host: backend.hostname
        # - vals: values to print
        # - pfx: backend prefix
        # - prot: backend.method
        # - db: backend.database
        # - e: errmsg
        # - E: errcode
        #
        def get_backend_value(backend, field, key=None):
            key = key or field
            return (getattr(backend, field) if backend else ctx.get(key)) or False

        Cache = self.env["synchro.cache"]
        ctx = ctx or {}
        loglevel = loglevel or 2
        # Current self could be in delete cache if prior ORM error happened
        # so in this case we have to create rather tha update record
        # try:
        #     upd_log = False
        #     if self.exists():
        #         upd_log = self.id and self.loglevel
        # except BaseException:
        #     self.env.cr.rollback()  # pylint: disable=invalid-commit
        #     upd_log = False
        self = self.search([("id", "=", self.id)])
        upd_log = self
        if res_rec and len(res_rec) > 1:
            res_rec0 = res_rec[0]
        else:
            res_rec0 = res_rec
        res_model = (
            self.res_model
            if upd_log
            else ""
            or (
                res_model
                or ctx.get("res_model")
                or (res_rec0._name if res_rec0 else "")
            )
        )
        res_id = (
            self.res_id
            if (upd_log and self.res_id)
            else False
            or (
                res_id
                or ctx.get("res_id")
                or (res_rec0.id if res_rec0 else "")
                or False
            )
        )
        ctx["e"] = errmsg
        ctx["E"] = errcode
        backend = backend or self.backend_id or False
        if not backend and res_model == "synchro.backend" and res_id:
            backend = (
                res_rec0 if res_rec0 else self.env["synchro.backend"].browse(res_id)
            )
        ctx["model"] = res_model
        ctx["id"] = res_id
        ctx["backend"] = backend.name if backend else ""
        if backend:
            curloglevel = int(backend.tracelevel or "0")
            Cache.set_loglevel(curloglevel)
        else:
            curloglevel = Cache.get_attr(1, "LOGLEVEL", loglevel)
        if not isinstance(curloglevel, int):
            curloglevel = 4
        reqloglevel = 0
        if isinstance(loglevel, str):
            if not loglevel.isdigit():
                reqloglevel = int(self.loglevel2num.get(loglevel, "2"))
            else:
                reqloglevel = loglevel
        recloglevel = 0
        if upd_log:
            if isinstance(self.loglevel, str) and not self.loglevel.isdigit():
                recloglevel = int(self.loglevel2num.get(self.loglevel, "0"))
            else:
                recloglevel = int(self.loglevel)
        if reqloglevel >= 4:
            Cache.clean_cache()
        if max(reqloglevel, recloglevel) >= 4 - curloglevel:
            ctx["lgi_ep"] = get_backend_value(backend, "counterpart_url", key="lgi_ep")
            ctx["data_ep"] = get_backend_value(
                backend, "counterpart_data_url", key="data_ep"
            )
            ctx["host"] = get_backend_value(backend, "hostname", key="host")
            ctx["prot"] = get_backend_value(backend, "method", key="prot")
            ctx["db"] = get_backend_value(backend, "database", key="db")
            ctx["pfx"] = get_backend_value(backend, "prefix", key="pfx")
            ctx["vals"] = (
                {
                    k: (
                        v[0:28] + "[...]"
                        if isinstance(v, str) and len(v) > 32
                        else v
                    )
                    for k, v in values.items()
                }
                if isinstance(values, dict)
                else values if values else ""
            )
            try:
                if ctx["E"] and ctx["e"] and not msg_text.startswith("!"):
                    hdr_msg = (
                        "!%(e)s %(E)s!: " + _u(_(msg_text).replace("%(vals)s", "\n%%s"))
                    ) % ctx
                else:
                    hdr_msg = _u(_(msg_text).replace("%(vals)s", "%(vals)32.32s")) % ctx
            except BaseException as e:  # pragma: no cover
                raise UserError(e)
            body_msg = _u(msg_text.replace("%(vals)s", "\n%%s")) % ctx
            if "%s" in body_msg:
                values = (
                    self.pretty_print(values)
                    if isinstance(values, dict)
                    else str(values) if values is not None else ""
                )
                body_msg = body_msg % values
            if reqloglevel >= 4 - curloglevel:
                _logger.info(hdr_msg)
            logrec = self.logger(
                hdr_msg,
                body_msg,
                errcode,
                res_model,
                reqloglevel,
                recloglevel,
                upd_log=upd_log,
                res_rec=res_rec,
                res_id=res_id,
                backend=backend,
            )
            # if logrec and logrec != self:
            #     res_model = logrec.res_model or res_model
            #     ctx = self._compute_reference["logrec"]
            #     if "logrec" not in ctx:
            #         ctx["logrec"] = {}
            #         ctx["logrec"][res_model] = logrec
            #     elif res_model in ctx["logrec"]:
            #         ctx["logrec"][res_model] = logrec
            #     elif False in ctx["logrec"]:
            #         ctx["logrec"][res_model] = logrec
            #         del ctx[logrec][False]
            return logrec

    def clean_values(self, values):
        for (k, v) in values.copy().items():
            if v is None or v is False:
                del values[k]

    def autocommit_sql(self, query, values, fetch_id=False):
        # db = odoo.sql_db.db_connect(self.env.cr.dbname)
        # registry = odoo.registry(self.env.cr.dbname)
        id_new = None
        # with db.cursor() as log_cr:
        with self.env.registry.cursor() as log_cr:
            log_cr.execute(query, values)
            if fetch_id:
                id_new, = log_cr.fetchone()
            log_cr._cnx.commit()
            # log_cr.close()
        return id_new

    def write_log(self, values):
        self.clean_values(values)
        # query = "UPDATE %s SET %s WHERE ID = %s" % (
        #     self._table,
        #     ",".join(["%s=%%(%s)s" % (k, k) for k in list(values.keys())]),
        #     self.id,
        # )
        # self.autocommit_sql(query, values)
        # #return self.browse(self.id)
        # with api.Environment.manage():
        #     log_cr = api.Environment(
        #         self.env.registry.cursor(), self.env.user.id, {})[self._name]
        #     # log_cr.env.cr.execute(query, values)
        #     # id_new, = log_cr.env.cr.fetchone()
        #     try:
        #         log_cr.browse(self.id).write(values)
        #     except BaseException as e:
        #         pass
        #     log_cr.env.cr.commit()
        #     if not log_cr.env.cr.closed:
        #         log_cr.env.cr.close()
        # return self.browse(self.id)
        # return self.env["synchro.log"].browse(self.id).write(values)
        # log_id = False
        # with self.pool.cursor() as new_cr:
        #     new_env = api.Environment(new_cr, 1, self.env.context)
        #     new_env["synchro.log"].browse(self.id).write(values)
        # return self.browse(self.id)
        return self.write(values)

    def create_log(self, values):
        self.clean_values(values)
        # query = "INSERT INTO %s (%s) VALUES (%s) RETURNING id" % (
        #     self._table,
        #     ",".join(list(values.keys())),
        #     ",".join(["%%(%s)s" % k for k in list(values.keys())])
        # )
        # id_new = self.autocommit_sql(query, values, fetch_id=True)
        # with api.Environment.manage():
        #     log_cr = api.Environment(
        #         self.env.registry.cursor(), self.env.user.id, {})[self._name]
        #     # log_cr.env.cr.execute(query, values)
        #     # id_new, = log_cr.env.cr.fetchone()
        #     try:
        #         id_new = log_cr.create(values).id
        #     except BaseException as e:
        #         pass
        #     log_cr.env.cr.commit()
        #     if not log_cr.env.cr.closed:
        #         log_cr.env.cr.close()
        # return self.browse(id_new)
        # log_id = False
        # with self.pool.cursor() as new_cr:
        #     new_env = api.Environment(new_cr, 1, self.env.context)
        #     log_id = new_env["synchro.log"].create(values).id
        # # return self.env["synchro.log"].create(values)
        # return self.browse(log_id)
        return self.create(values)
