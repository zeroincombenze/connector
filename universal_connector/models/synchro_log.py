# -*- coding: utf-8 -*-
#
# Copyright 2019-26 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging
from datetime import date, datetime, timedelta
import json
from python_plus import _u
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)


class IrModelSynchroLog(models.Model):
    _name = "ir.model.synchro.log"
    _order = "timestamp desc, id desc"

    @api.multi
    @api.depends("errmsg")
    def _compute_digest(self):
        for log in self:
            log.digest = log.errmsg[:480]

    timestamp = fields.Datetime("Timestamp", copy=False)
    model = fields.Char("Model")
    res_id = fields.Integer("Model ID")
    ext_id = fields.Integer("External ID")
    hdrmsg = fields.Char("Log message", copy=False)
    digest = fields.Text("Message Digest", compute=_compute_digest)
    errmsg = fields.Text("Full message", copy=False)

    @api.model
    def pretty_print(self, values):  # pragma: no cover
        def to_str(obj):
            x = str(obj)
            return obj.id if hasattr(obj, "id") else str(x) if (
                (hasattr(obj, "__len__") or isinstance(obj, (date, datetime)))
                and len(x) < 512) else "[...]"

        if isinstance(values, dict):
            return (
                json.dumps(
                    {
                        k + "_id" if hasattr(v, "id") else k: (
                            "[...]" if k and k.startswith("image")
                            else v[0:60] + "[...]" if isinstance(v, str) and len(v) > 64
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
        elif isinstance(values, (date, datetime)):
            return "\"" + str(values) + "\""
        return json.dumps(values, indent=2)

    def logger(
            self, reqloglevel, errmsg,
            rec=None, model=None, id=None, xid=None, logrec=None, values=None, ctx=None
    ):
        hdrmsg = _u(errmsg)
        if logrec:
            try:
                if not logrec.exists() or not logrec.id:
                    logrec = self.env["ir.model.synchro.log"]
                else:
                    errmsg = errmsg or logrec.errmsg
                    hdrmsg = logrec.hdrmsg
            except BaseException:   # pragma: no cover
                logrec = self.env["ir.model.synchro.log"]
        ctx = _u(ctx or {})
        errmsg = _u(errmsg or "")
        id = id if isinstance(id, (int, long)) else False
        if "id" in ctx and not isinstance(ctx["id"], (int, long)):
            del ctx["id"]
        xid = xid if isinstance(xid, (int, long)) else False
        if isinstance(rec, int) or not hasattr(rec, "__iter__"):
            ctx["rec"] = False
        else:
            ctx["rec"] = fields.first(rec)
        if not model and ctx["rec"]:
            model = ctx["rec"]
        if model:
            ctx["model"] = model if isinstance(model, str) else model._name if hasattr(
                model, "_name") else ""
        else:
            ctx["model"] = ""
        ctx["id"] = (
            id
            or ctx.get("id")
            or (ctx["rec"].id if ctx["rec"] else "")
            or (rec if isinstance(rec, (int, long)) else False)
        )
        ctx["xid"] = xid
        ctx["vals"] = values
        ctx = _u(ctx)
        try:
            if isinstance(ctx["vals"], dict) and len(str(ctx["vals"])) > 40:
                hdrmsg = _(hdrmsg.replace(
                    "%(vals)s", "%(vals)-.40s[...] ")) % ctx
            else:
                hdrmsg = hdrmsg % ctx
        except BaseException:  # pragma: no cover
            pass
        ctx["vals"] = self.pretty_print(values)
        try:
            errmsg = errmsg % ctx
        except BaseException:   # pragma: no cover
            pass

        now = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        vals = {"hdrmsg": hdrmsg}
        if not logrec:
            vals["timestamp"] = now,
            vals["errmsg"] = errmsg
            vals["res_id"] = ctx["id"]
            vals["ext_id"] = ctx["xid"]
            vals["model"] = ctx["model"]
        else:
            vals["errmsg"] = (logrec.errmsg or "") + "\n\n" + errmsg
            if ctx["id"]:
                vals["res_id"] = ctx["id"]
            if ctx["xid"]:
                vals["ext_id"] = ctx["xid"]
            if not logrec.model:
                vals["model"] = ctx["model"]
        _logger.info(hdrmsg)
        if logrec:
            logrec.write(vals)
        else:
            logrec = self.create(vals)
        if rec and hasattr(rec, "timestamp") and hasattr(rec, "errmsg"):
            vals = {"timestamp": now}
            vals["errmsg"] = "\n".join(
                (errmsg + u"\n" + (rec.errmsg or u"")).split("\n")[0:3])
            rec.write(vals)
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
        for rec in self.search(domain, order="timestamp desc"):
            rec.unlink()
            max_recs_per_session -= 1
            if not max_recs_per_session:
                break
