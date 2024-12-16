#
# Copyright 2019-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
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

from odoo import _, api, fields, models
from python_plus import _u

_logger = logging.getLogger(__name__)


class IrModelSynchroLog(models.Model):
    _name = "ir.model.synchro.log"
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
    model = fields.Char("Model")
    res_id = fields.Integer("Model ID")
    errmsg = fields.Char("Error message", copy=False)
    errcode = fields.Integer("Error code", copy=False)
    loglevel = fields.Char("Log level")
    values = fields.Text("Values of message", copy=False)
    reference = fields.Char(
        string="Reference", compute="_compute_reference", readonly=True, store=False
    )
    backend_id = fields.Many2one(
        "synchro.channel",
        "Backend",
        copy=False,
    )

    @api.depends("model", "res_id")
    def _compute_reference(self):  # pragma: no cover
        for res in self:
            res.reference = "%s,%s" % (res.model, res.res_id)

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
        res_model,
        res_rec,
        errmsg,
        errcode,
        loglevel,
        logrec=None,
        res_id=None,
        backend=None,
        values=None,
    ):
        now = datetime.now()
        if not PY3:
            now = now.strftime("%Y-%m-%d %H:%M:%S.%f")
        vals = {
            "timestamp": now,
            "model": (
                res_model
                if res_model in self.env
                else res_rec._namme if res_rec else False
            ),
            "res_id": res_id,
            "errcode": errcode,
        }
        for name, lev in self.loglevel2num.items():
            if int(lev) == loglevel:
                vals["loglevel"] = name
                break
        if backend:
            vals["backend_id"] = backend.id
        elif vals["model"] == "synchro.channel" and vals["res_id"]:
            vals["backend_id"] = vals["res_id"]
        vals["values"] = self.pretty_print(values) if values else False
        if logrec:
            # logrec should be delete if prior rollback
            try:
                getattr(logrec, "errmsg")
            except BaseException:
                self.env.cr.rollback()  # pylint: disable=invalid-commit
                logrec = None
        if logrec:
            if errmsg:
                vals["errmsg"] = logrec.errmsg + " | " + errmsg
            logrec.write(vals)
        else:
            vals["errmsg"] = errmsg or _("No Error")
            logrec = self.create(vals)
        if res_rec and hasattr(res_rec, "timestamp") and hasattr(res_rec, "errmsg"):
            res_rec.write({"timestamp": now, "errmsg": errmsg})
        return logrec

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
        id=None,
        values=None,
        logrec=None,
        backend=None,
        errcode=None,
        errmsg=None,
        ctx=None,
    ):
        # ctx values:
        # model: res_model
        # id: res_id
        # backend: backend.name
        # lgi_ep: login endpoint
        # data_ep: data endpoint
        # host: backend.hostname
        # vals: values to print
        # pfx: backend prefix
        # prot: backend.method
        # db: backend.database
        #
        Cache = self.env["ir.model.synchro.cache"]
        ctx = ctx or {}
        ctx["model"] = (
            ctx.get("model") or res_model or (res_rec._name if res_rec else "")
        )
        ctx["id"] = (
            id
            or ctx.get("id")
            or (
                res_rec
                and (
                    (len(res_rec) == 1 and res_rec.id)
                    or (len(res_rec) > 1 and res_rec.ids[0])
                )
            )
            or False
        )
        if res_rec and len(res_rec) > 1:
            msg_text += " # " + str(res_rec.ids)
        ctx["e"] = errmsg
        ctx["E"] = errcode
        ctx["backend"] = backend.name if backend else ctx.get("backend") or ""
        ctx["lgi_ep"] = backend.counterpart_url if backend else ctx.get("lgi_ep") or ""
        ctx["data_ep"] = (
            backend.counterpart_data_url if backend else ctx.get("data_ep") or ""
        )
        ctx["host"] = backend.hostname if backend else ctx.get("host") or ""
        ctx["prot"] = backend.method if backend else ctx.get("prot") or ""
        ctx["db"] = backend.database if backend else ctx.get("db") or ""
        ctx["pfx"] = backend.prefix if backend else ctx.get("pfx") or ""
        ctx["vals"] = (
            {
                k: v[0:28] + "[...]" if isinstance(v, str) and len(v) > 32 else v
                for k, v in values.items()
            }
            if isinstance(values, dict)
            else values if values else ""
        )
        if not isinstance(values, str):
            ctx["vals"] = str(ctx["vals"])
        elif len(ctx["vals"]) > 40:
            ctx["vals"] = ctx["vals"][:36] + " ..."
        if backend:
            curloglevel = int(backend.tracelevel or "0")
            Cache.set_loglevel(curloglevel)
        else:
            curloglevel = Cache.get_attr(1, "LOGLEVEL", loglevel)
        if isinstance(loglevel, str):
            if not loglevel.isdigit():
                reqloglevel = int(self.loglevel2num.get(loglevel, "2"))
            else:
                reqloglevel = int(loglevel)
        if reqloglevel >= 4:
            Cache.clean_cache()
        if reqloglevel >= 4 - curloglevel:
            try:
                full_msg = _u(msg_text % ctx)
            except BaseException:  # pragma: no cover
                full_msg = _u(msg_text)
            _logger.info(full_msg)
            return self.logger(
                ctx["model"],
                res_rec,
                full_msg,
                errcode,
                reqloglevel,
                logrec=logrec,
                res_id=ctx["id"],
                backend=backend,
                values=values,
            )
