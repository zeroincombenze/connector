#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
"""
INTRODUCTION

This software provides to ability of exchange records with different
remote counterparties. It is base on internal synchro function that returns the Odoo
id record or a error code (read below).

Synchro runs 3 steps:
1. Counterpart names are translated into local Odoo names, and the <*2many>
   records are mapped into local records.
   During the mapping process, synchro function on <*2many> relation could be run again
   in order to bind or create a linked record. So synchro is a recursive function.
2. After translation and mapping, data is used to binding local record.
   The searching is mainly based on counterpart id (read below) when matched;
   otherwise a complex finding process is engaged depending on the specific
   model structure.
3. If local Odoo record is found, the <write> is engaged otherwise the
   <create> is executed. Because counterparty ignores the Odoo structure,
   it can issue incomplete or wrong data so the <create> can fail and breaks
   recursive calls stack. In order to minimize the errors, the <create> is split
   into a simple create followed by a write function. The <create> uses the
   minimal data required by Odoo while the <write> uses the full data supplied
   by the counterparty. In this way, the <create> should terminate quite ever
   with success and return a valid id.


EXTERNAL REFERENCE

On every Odoo record there is an id field to link external record, which is
a unique key to avoid synchronization troubles.
Odoo's models and counterpart tables can have different relationships:

* One to one: this relationship just requires the field mapping
* Many (Odoo) to one (partner): it managed like previous case because
  external ids never conflicts
* One (Odoo) to many (partner): it requires sub models (w/o records) and/or
  more external id on the actual record.

Imagine this scenario: Odoo exchanges "res.partner" with a counterparty called
Gamma which have 2 tables, named "customer" and "supplier". A one Odoo record
may have to link to customer record and/or the supplier record.
Also imagine that the remote customer table contains shipping data which
are in a separate "res.partner" records of Odoo.
So we meet some conflicts. The first one when both "customer" and "supplier"
can have the same id (because the counterparty has 2 different tables)
or when a partner is both customer and supplier at the same time.
We can solve this conflict adding a new field on the actual "res.partner"
record, and we use a "res.partner.supplier" sub-model.
We meet another conflict when we write two "res.partner" records, one with the
customer data and the other one with the shipping data. Both records refer to
the same id of counterpart record, but we cannot use the same id due unique key
constraint.
We solve this conflict adding a bias value (default is 1000000000) to the
shipping Odoo's record.
At the last but no least we need of a preprocessing function to recognize
a customer record from a supplier record and to extract shipping data from the
customer record.

In this software we use the follow terms and structures:
+---------------+-------------+----------------------+----------------------+
| prefix     (1)| gamma       | gamma                | gamma                |
| bind       (2)| customer    |                      | supplier             |
| binding_model | res.partner | res.partner          | res.partner          |
| loc_ext_id (4)| gamma_id    | gamma_id             | gamma_id             |
| ext_id     (7)| 1234        | 1234                 | 1234                 |
| ext_key_id (5)| id          | id                   | id                   |
| offset     (6)| 0           | 100000000            | 0                    |
+---------------+-------------+----------------------+----------------------+
(1) Prefix of every field supplied by the counterparty (this is just an example)
(2) Name of remote counterpart table
(3) Odoo model, sub model of actual model
(4) Odoo field, unique key, with external partner id; default is "{prefix}_id"
(5) External partner field with the external id; default is "id"
(6) Offset to store external id, when does not exist external counterpart table
(7) External id, usually should be an integer but could be a string

During the pre-processing to extract the shipping data from the customer data,
the shipping data is stored in the cache and then retrieved after the customer
record is written.


PROTECTION

Every field can be protect against update. There are 4 protection levels:
0 -> 'Always Update': field may be update by counterparty (default)
1 -> 'But new value not empty':
      field may be update only by not null counterparty value
2 -> 'But current value is empty': field may be update only if local is null
3 -> 'Protected field': field cannot be update by counterparty
4 -> 'Counter field': field is an integer and value is the max(local, remote)


EXCHANGE MODE AND STRUCTURED MODELS

Data may be exchanged with counterpart in two ways:
1. Push mode: counterparty sends data to Odoo. It prefixes its dictionary name
2. Pull mode: Odoo gets data from the counterparty.

Parent/child models like invoice and sale order are managed in 3 ways:
A. Parent without child reference. After the parent record is written, children
   must be sent by the counterparty (push mode) or must be get from the
   counterparty (pull mode).
B. Parent contains "line_ids" field with list of children ids. In this case
   "line _ids" is extracted from the parent record during pre-processing and
   the list of children is stored in the cache.
   After the parent record is written, "line_ids" is retrieved and every id in
   the list is used to get data from the counterparty (only pull mode).
C. Header contains "line_ids" with dictionary data and operation is <create>.
   In this case data are enough to create children records too. "line_ids"
   field is changed adding "(0, 0" prefix that is the way used by Odoo itself
   to create new parent/child records.


CACHE

Data stored in cache:
- 'gamma:shipping': sub-model res.partner.shipping
- 'gamma:billing': sub-model res.partner.invoice
- '_QUEUE_SYNC': queue records
- '__{{model}}': full data of model to write the created record (read above)


LOG MESSAGES
Log message level are:
    'error': log only error messages
    'info': log error and info messages
    'warning': log warning + info + error messages
    'debug': log debug + warning + info + error messages
    'any': log any message (most verbose, slow execution)
    'trace': deprecated

RETURN CODES

Return code are:
    -1: Error creating record
    -2: Error writing record
    -3: Record with passed id does not exist
    -4: Insufficient permission to update record
    -5: Invalid structure header/details
    -6: No backend to manage counterparty
    -7: Unrecognized counterparty data
    -8: Unrecognized external table
    -9: No data updated
   -10: Cannot update record state
   -11: Unmanaged table
   -12: Internal error
   -13: Invalid remote response
   -14: No enough data to create record
   -15: Invalid company
   -16: Backend not ready
  -100: if return code < -100 means error on child records
"""
from future.utils import PY3
from datetime import datetime
import time
import logging

from odoo import api, models
from python_plus import str2bool, _u

from .synchro_cache import MODEL_LAZY_COMPANY

_logger = logging.getLogger(__name__)


class IrModelSynchro(models.Model):
    _name = "ir.model.synchro"
    _inherit = "ir.model"
    _description = "Additional model functions"

    def preprocess(self, backend, vmodel, vals):
        return vals, ""

    @api.model
    def _cast_2many(self, binding_model, value):
        def value2list(value):
            if isinstance(value, str):  # pragma: no cover
                value = [x for x in value.split(",")]
            elif not hasattr(value, "__iter__"):  # pragma: no cover
                value = [value]
            return value

        res = []
        items = value2list(value)
        for item in items:
            if isinstance(item, str) and (item.isdigit() or item == "-1"):
                res.append(int(value))  # pragma: no cover
            else:
                res.append(item)
        return res

    @api.model
    def _cast_field_many2many(self, binding_model, value):  # pragma: no cover
        return self._cast_2many(binding_model, value)

    @api.model
    def _cast_field_one2many(self, binding_model, value):
        return self._cast_2many(binding_model, value)

    @api.model
    def _cast_field_many2one(self, binding_model, value):
        if isinstance(value, (list, tuple)):
            value = value[0]
        if isinstance(value, str) and (value.isdigit() or value == "-1"):
            value = int(value)  # pragma: no cover
        return value

    @api.model
    def _cast_field_datetime(self, binding_model, value):
        if value and isinstance(value, str):
            if len(value) == 10:
                value += " 00:00:00"
            if PY3:
                value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        return value

    @api.model
    def _cast_field_date(self, binding_model, value):
        if value and isinstance(value, str) and len(value) == 10:
            if PY3:
                value = datetime.strptime(value[:10], "%Y-%m-%d").date()
        return value

    @api.model
    def _cast_field_float(self, binding_model, value):
        if value and isinstance(value, str):
            value = eval(value)
        return value

    @api.model
    def _cast_field_monetary(self, binding_model, value):  # pragma: no cover
        return self._cast_field_float(binding_model, value)

    @api.model
    def _cast_field_integer(self, binding_model, value):
        if (
            value
            and isinstance(value, str)
            and (value.isdigit() or value == "-1")
        ):
            value = int(value)
        return value

    @api.model
    def _cast_field_boolean(self, binding_model, value):
        return str2bool(value, True)

    @api.model
    def _cast_field_base(self, binding_model, value):
        return _u(value)

    def cast_type(self, value, binding_model, ftype):
        method = "_cast_field_%s" % ftype
        method = method if hasattr(self, method) else "_cast_field_base"
        return getattr(self, method)(binding_model, value)

    def manage_language(self, vals, overwrite=True):
        if "code" not in vals:  # pragma: no cover
            self.env["synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR Invalid language code",
                res_model="res.lang",
                errcode=-7,
            )
            return -7

        iso = vals["code"]
        load = False
        Language = self.env["res.lang"]
        languages = Language.search([("code", "=", iso)])
        if not languages:  # pragma: no cover
            languages = Language.search([("code", "=", iso), ("active", "=", False)])
            if languages:
                languages.write({"active": True})
                load = True
        if not languages or load:
            vals = {
                "lang": iso,
                "overwrite": overwrite,
            }
            self.env["base.language.install"].create(vals).lang_install()
            languages = self.env["res.lang"].search([("code", "=", iso)])
        return languages[0].id if languages else -7

    def manage_module(self, vals):
        if "name" not in vals:   # pragma: no cover
            self.env["synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR Invalid module name",
                res_model="ir.module.module",
                errcode=-7,
            )
            return -7

        Module = self.env["ir.module.module"]
        modules = Module.search([("name", "=", vals["name"])])
        if not modules:  # pragma: no cover
            self.env["synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR Module %(vals)s does not exist",
                res_model="ir.module.module",
                values=vals["name"],
                errcode=-3,
            )
            return -3

        module = modules[0]
        ext_state = vals.get("state", "installed")
        if ext_state != "installed":
            return module.id

        if module.state == "uninstalled":  # pragma: no cover
            try:
                modules.button_immediate_install()
            except BaseException as e:  # pragma: no cover
                self.env.cr.rollback()  # pylint: disable=invalid-commit
                self.env["synchro.log"].logmsg(
                    "error",
                    "!%(E)s! ERROR %(e)s Module %(vals)s not installable",
                    res_model="ir.module.module",
                    values=vals["name"],
                    errcode=-4,
                    errmsg=e,
                )
                return -4

            max_ctr = len(module.dependencies_id) + 3
            query = ("SELECT id FROM ir_module_module WHERE"
                     " name='%s' AND state='installed'" % module.name)
            # Check for state by sql to avoid cache trouble
            while max_ctr > 0:
                self.env.cr.execute(query)
                res = self.env.cr.fetchall()
                if res:
                    module.state = "installed"
                    break
                max_ctr -= 1
                time.sleep(0.5)
            time.sleep(1)
        if module.state != "installed":   # pragma: no cover
            self.env["synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR Module %(vals)s not installed",
                res_model="ir.module.module",
                values=vals["name"],
                errcode=-4,
            )
            return -4
        return module.id

    @api.model
    def create_new(self, Binder, vals, only_minimal=False, ctx=None):
        ctx = ctx or {}
        ctx["logrec"] = ctx.get("logrec") or self.env["synchro.log"]
        if Binder._name.startswith("account.move") and not ctx:
            ctx = {"check_move_validity": False}
        try:
            if ctx:
                rec = Binder.create(vals)
            else:
                rec = Binder.create(vals)
            ctx["logrec"].logmsg("warning", "", res_rec=rec, values=vals)
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            rec = -1
            self.env["synchro.log"].logmsg(
                "error",
                "%(model)s.create(%(vals)s)",
                res_model=Binder._name,
                values=vals,
                errmsg=e,
                errcode=-1,
            )
        return rec

    def rewrite(self, rec, vals, dir_mapper, only_minimal=False, ctx=None):
        ctx = ctx or {}
        ctx["logrec"] = ctx.get("logrec") or self.env["synchro.log"]
        if vals:
            vals = dir_mapper.drop_protected_equal_fields(vals, rec)
        if vals:
            try:
                if rec._name.startswith("account.move"):
                    rec.with_context(check_move_validity=False).write(vals)
                else:
                    rec.write(vals)
                ctx["logrec"].logmsg("warning", "", res_rec=rec, values=vals)
            except BaseException as e:  # pragma: no cover
                self.env.cr.rollback()  # pylint: disable=invalid-commit
                self.env["synchro.log"].logmsg(
                    "error",
                    "%(model)s.write(%(vals)s)",
                    res_rec=rec,
                    values=vals,
                    errmsg=e,
                    errcode=-2,
                )
                return -2
        else:
            ctx["logrec"] = ctx["logrec"].logmsg("warning", "", res_rec=rec, errcode=-9)
        return rec

    def _make_record(
            self, Binder, dir_mapper, model_spec,
            only_minimal, incomplete_record, running_in_queue, ttl, vals, saved_vals,
            ctx=None
    ):
        postponed = False
        Cache = self.env["synchro.cache"]
        backend = dir_mapper.backend_id
        binding_model = dir_mapper.name
        rec = (
            dir_mapper.bind_record(Binder, vals, model_spec=model_spec, ctx=ctx)
            if vals
            else None
        )
        if not rec:
            rec = -14
            loc_ext_id = dir_mapper.get_loc_ext_id()
            min_vals = {}
            if dir_mapper.auth_action not in ("upd", "lock"):
                vals = dir_mapper.compile_required_fields(
                    vals,
                    ctx=ctx,
                )
                if only_minimal or incomplete_record:
                    for loc_name in vals.keys():
                        mapper = dir_mapper.get_mapper(loc_name=loc_name)
                        if mapper.required or loc_name in (
                            loc_ext_id,
                            dir_mapper.parent_name,
                            "name",
                        ):
                            min_vals[loc_name] = vals[loc_name]
                    struct = self.env[binding_model].fields_get()
                    valid = True if min_vals else False
                    if valid and incomplete_record:
                        for loc_name in struct.keys():
                            if (
                                loc_name == "company_id"
                                and binding_model in MODEL_LAZY_COMPANY
                            ):
                                continue
                            mapper = dir_mapper.get_mapper(loc_name=loc_name)
                            if (
                                mapper.required
                                or loc_name in (loc_ext_id, dir_mapper.parent_name)
                            ) and loc_name not in min_vals:
                                valid = False
                                break
                    if min_vals != vals:
                        Cache.que_push(
                            backend,
                            "synchro",
                            binding_model,
                            model_spec,
                            saved_vals,
                            ttl,
                            ctx,
                            prio=3 if valid else 2,
                        )
                    if valid:
                        rec = self.create_new(
                            Binder, min_vals, only_minimal=True, ctx=ctx
                        )
                    else:   # pragma: no cover
                        ctx["logrec"].logmsg(
                            "warning",
                            "No enough data to create record",
                        )
                        if not running_in_queue and backend.load_mode == "direct":
                            postponed = vals
                elif vals:  # pragma: no cover
                    rec = self.create_new(Binder, vals, only_minimal=False, ctx=ctx)
        else:
            if dir_mapper.auth_action in ("ins", "lock"):  # pragma: no cover
                rec = -4
            else:
                rec = self.rewrite(rec, vals, dir_mapper, only_minimal=False, ctx=ctx)
        return rec, postponed

    @api.model
    def synchro(
        self,
        Binder,
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
        Cache = self.env["synchro.cache"]
        ctx = ctx or {}
        ctx["logrec"] = ctx.get("logrec") or self.env["synchro.log"]
        DirMapper = self.env["synchro.model"]

        if isinstance(jacket, str):
            vals = self.env["synchro.backend"].vals_with_jacket(vals, prefix=jacket)
        elif jacket and not backend and dir_mapper:   # pragma: no cover
            backend = dir_mapper.backend_id
            vals = backend.vals_with_jacket(vals)
        elif jacket and backend:
            vals = backend.vals_with_jacket(vals)
        elif jacket and not backend:  # pragma: no cover
            ctx["logrec"].logmsg(
                "error",
                "%(model)s.synchro() w/o remote identification",
                res_model=Binder if isinstance(Binder, str) else Binder._name,
                errcode=-7,
            )
            return -7

        if isinstance(Binder, str):  # pragma: no cover
            # vmodel = Binder
            binding_model, model_spec = DirMapper.split_binding_model_n_spec(
                Binder, spec=model_spec
            )
            if binding_model in self.env:
                Binder = self.env[binding_model].with_context(
                    {"lang": backend.default_lang_id.code}
                )
            else:
                Cache.clean_cache()
                ctx["logrec"].logmsg(
                    "error",
                    "Invalid or unknown model %(model)s on synchro()!",
                    res_model=binding_model,
                    errcode=-11,
                )
                return -11
        else:
            binding_model, model_spec = DirMapper.split_binding_model_n_spec(
                Binder._name, spec=model_spec
            )
            # vmodel = DirMapper.get_vmodel(Binder._name, model_spec)
            if binding_model not in self.env:  # pragma: no cover
                ctx["logrec"].logmsg(
                    "error",
                    "Invalid or unknown model %(model)s on synchro()!",
                    res_model=binding_model,
                    errcode=-11,
                )
                return -11
            Binder = self.env[binding_model].with_context(
                {"lang": backend.default_lang_id.code}
            )

        backend = backend or self.env["synchro.backend"].assign_backend(vals)
        if not backend:  # pragma: no cover
            Cache.clean_cache()
            ctx["logrec"].logmsg(
                "error",
                "No backend found on synchro(%(model)s,%(vals)s,ttl=%(t)s))",
                res_model=binding_model,
                values=vals,
                errcode=-6,
                ctx={"t": ttl},
            )
            return -6
        if backend.state == "draft":  # pragma: no cover
            return -16
        if backend.state in ("ready", "failed"):
            backend.write({"state": "run"})
        dir_mapper = backend.get_dir_mapper(model=binding_model, spec=model_spec)
        # if not dir_mapper:
        #     # Compatibility with old release of UC
        #     dir_mapper = backend.get_dir_mapper(model=vmodel)
        saved_vals = vals.copy()
        ctx = dir_mapper.load_ctx(ctx if running_in_queue else {})
        ttl = ttl or (4 if only_minimal else 2)
        ctx["logrec"] = ctx["logrec"].logmsg(
            "warning" if ctx["logrec"] else "info",
            "%(model)s.synchro(%(vals)s,backend=%(backend)s,min=%(m)s),ttl=%(t)s",
            res_model=binding_model,
            values=vals,
            backend=backend,
            ctx={"m": only_minimal, "t": ttl},
        )

        vals, incomplete_record = dir_mapper.map_to_internal(
            vals,
            ttl,
            only_minimal=only_minimal,
            model_spec=model_spec,
            ctx=ctx,
        )
        if (
            backend.company_id
            and "company_id" in vals
            and vals["company_id"]
            and vals["company_id"] != backend.company_id.id
        ):  # pragma: no cover
            rec = -15
            return rec
        postponed = False
        if binding_model == "res.lang":
            rec = self.manage_language(vals)
        elif binding_model == "ir.module.module":
            rec = self.manage_module(vals)
        else:
            rec, postponed = self._make_record(
                Binder, dir_mapper, model_spec,
                only_minimal, incomplete_record, running_in_queue, ttl,
                vals, saved_vals,
                ctx=ctx
            )
        if not running_in_queue and backend.load_mode == "direct":
            if Cache.que_waiting_len(backend):
                commit_rate = 16 if backend.deferred_payload > "0" else 1024
                if Cache.que_waiting_len(backend) > commit_rate:
                    # commit every table to avoid too big transaction
                    self.env.cr.commit()  # pylint: disable=invalid-commit
                backend.synchro_queue()
                # Sometimes record cannot be created due missed required fields that
                # could be loaded by above synchro_que(); inside queue current record
                # can be created so we should test for this case
                if postponed and rec == -14:
                    rec = dir_mapper.bind_record(Binder, postponed, ctx=ctx)
        if not running_in_queue and self.state == "run":
            self.state = "ready"
        return rec.id if hasattr(rec, "id") else rec

    def push_record(
        self,
        ext_model,
        prefix,
        vals,
        ttl=None,
        ctx=None,
        dir_mapper=None,
        running_in_queue=None,
    ):
        ctx = ctx or {}
        logrec = ctx.get("logrec") or self.env["synchro.log"]
        Cache = self.env["synchro.cache"]

        if dir_mapper:
            backend = dir_mapper.backend_id
        else:  # pragma: no cover
            backend = self.env["synchro.backend"].assign_backend(
                {"%s:" % prefix: prefix}
            )
            if backend:
                dir_mapper = backend.get_dir_mapper(ext_model=ext_model)
        if not backend:  # pragma: no cover
            logrec.logmsg(
                "error",
                "No backend found on push_record(%(model)s,%(vals)s,%(t)s))",
                res_model=ext_model,
                values=vals,
                errcode=-6,
                ctx={"t": ttl},
            )
            return -6
        if not dir_mapper:  # pragma: no cover
            Cache.clean_cache()
            logrec.logmsg(
                "error",
                "Unmanaged model on push_record(%(model)s,%(vals)s,%(t)s)",
                res_model=ext_model,
                values=vals,
                errcode=-8,
                ctx={"t": ttl},
            )
            return -8
        # Cache.open(backend=backend, ext_model=ext_model)
        if (isinstance(vals, dict) and dir_mapper.counterpart_pk not in vals) or (
            not isinstance(vals, dict) and not hasattr(vals, dir_mapper.counterpart_pk)
        ):  # pragma: no cover
            logrec.logmsg(
                "error",
                "Received data of model %(model)s w/o %(pk)s",
                backend=backend,
                res_model=dir_mapper._name,
                errcode=-13,
                ctx={"pk": dir_mapper.counterpart_pk},
            )
            return -13
        binding_model = dir_mapper.name
        model_spec = dir_mapper.model_spec
        return self.env[binding_model].synchro(
            vals,
            ttl=ttl,
            running_in_queue=running_in_queue,
            jacket=True,
            model_spec=model_spec,
            backend=backend,
            ctx=ctx,
        )

    @api.model
    def trigger_one_record(
        self, ext_model, prefix, ext_id, ttl=None, running_in_queue=None, ctx=None
    ):
        ctx = ctx or {}
        logrec = ctx.get("logrec") or self.env["synchro.log"]
        Cache = self.env["synchro.cache"]

        if not prefix:  # pragma: no cover
            logrec.logmsg(
                "error",
                "Unrecognized prefix on trigger_one_record(%(xmodel)s,%(xid)s,%(t)s)",
                errcode=-7,
                ctx={"xmodel": ext_model, "xid": ext_id, "t": ttl},
            )
            return -7
        backend = self.env["synchro.backend"].assign_backend({"%s:" % prefix: prefix})
        if not backend:  # pragma: no cover
            logrec.logmsg(
                "error",
                "No backend found on trigger_one_record(%(xmodel)s,%(xid)s,ttl=%(t)s)",
                errcode=-6,
                ctx={"xmodel": ext_model, "xid": ext_id, "t": ttl},
            )
            return -6

        dir_mappers = backend.get_dir_mapper(ext_model=ext_model, multiple=True)
        if not dir_mappers:  # pragma: no cover
            Cache.clean_cache()
            logrec.logmsg(
                "error",
                "Unmanaged model on trigger_one_record(%(xmodel)s,%(xid)s,ttl=%(t)s)",
                errcode=-8,
                ctx={"xmodel": ext_model, "xid": ext_id, "t": ttl},
            )
            return -8
        vals = False
        for dir_mapper in dir_mappers:
            if not vals:
                ctx["logrec"] = logrec.logmsg(
                    "info",
                    "trigger_one_record(%(xmodel)s,%(pfx)s,ext_id=%(xid)s,ttl=%(t)s)",
                    res_model=dir_mapper.name,
                    backend=backend,
                    ctx={"xmodel": ext_model, "xid": ext_id, "t": ttl},
                )
                vals = dir_mapper.get_counterpart_response(ext_id)
                if not vals:    # pragma: no cover
                    return -13
                if isinstance(vals, (tuple, list)):
                    if len(vals) != 1:  # pragma: no cover
                        return -13
                    vals = vals[0]
            res_id = self.push_record(
                ext_model,
                prefix,
                vals,
                ttl=ttl,
                ctx=ctx,
                dir_mapper=dir_mapper,
                running_in_queue=running_in_queue,
            )
        return res_id

    @api.model
    def synchro_all_queues(self):  # pragma: no cover
        for backend in self.env["synchro.backend"].search([]):
            backend.synchro_queue()
