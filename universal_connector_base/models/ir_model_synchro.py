#
# Copyright 2019-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
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
| actual_model  | res.partner | res.partner          | res.partner          |
| vmodel     (3)| res.partner | res.partner.shipping | res,partner.supplier |
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
    -1: error creating record
    -2: error writing record
    -3: record with passed id does not exist
    -4: unmodifiable record
    -5: invalid structure header/details
    -6: unrecognized backend
    -7: no valid data supplied
    -8: unrecognized external table
    -9: Record already in queue
   -10: Cannot update record state
   -11: Unmanaged table
   -12: Internal error
   -13: Invalid remote response
   -14: invalid company
  -100: if return code < -100 means error on child records
"""
from future.utils import PY3
from datetime import datetime
import logging

from odoo import api, models
from odoo.osv import expression
from python_plus import str2bool, unicodes

from .ir_model_synchro_cache import MODEL_LAZY_COMPANY

_logger = logging.getLogger(__name__)


class IrModelSynchro(models.Model):
    _name = "ir.model.synchro"
    _inherit = "ir.model"

    @api.model
    def get_offset_value(self, backend, vmodel, ext_id):  # pragma: no cover
        # Cache = self.env["ir.model.synchro.cache"]
        # Cache.open(model=vmodel)
        # offset = Cache.get_model_attr(backend, vmodel, "ID_OFFSET", default=0)
        if vmodel == "res.partner.invoice":
            offset = 200000000
        elif vmodel == "res.partner.shipping":
            offset = 100000000
        else:
            offset = 0
        if ext_id < offset:
            return ext_id + offset
        return ext_id

    def preprocess(self, backend, vmodel, vals):
        return vals, ""

    @api.model
    def _cast_2many(self, actual_model, value):
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
    def _cast_field_many2many(self, actual_model, value):  # pragma: no cover
        return self._cast_2many(actual_model, value)

    @api.model
    def _cast_field_one2many(self, actual_model, value):
        return self._cast_2many(actual_model, value)

    @api.model
    def _cast_field_many2one(self, actual_model, value):
        if isinstance(value, (list, tuple)):
            value = value[0]
        if isinstance(value, str) and (value.isdigit() or value == "-1"):
            value = int(value)  # pragma: no cover
        return value

    @api.model
    def _cast_field_datetime(self, actual_model, value):
        if value and isinstance(value, str):
            if len(value) == 10:
                value += " 00:00:00"
            if PY3:
                value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        return value

    @api.model
    def _cast_field_date(self, actual_model, value):
        if value and isinstance(value, str) and len(value) == 10:
            if PY3:
                value = datetime.strptime(value[:10], "%Y-%m-%d").date()
        return value

    @api.model
    def _cast_field_float(self, actual_model, value):
        if value and isinstance(value, str):
            value = eval(value)
        return value

    @api.model
    def _cast_field_monetary(self, actual_model, value):
        return self._cast_field_float(actual_model, value)

    @api.model
    def _cast_field_integer(self, actual_model, value):
        if value and isinstance(value, str) and (value.isdigit() or value == "-1"):
            value = int(value)
        return value

    @api.model
    def _cast_field_boolean(self, actual_model, value):
        return str2bool(value, True)

    @api.model
    def _cast_field_base(self, actual_model, value):
        return value

    def cast_type(self, value, actual_model, ftype):
        method = "_cast_field_%s" % ftype
        method = method if hasattr(self, method) else "_cast_field_base"
        return getattr(self, method)(actual_model, value)

    def browse_from_id_in_vals(self, actual_cls, vals):
        id = 0
        rec = False
        if "id" in vals:
            id = vals.pop("id")
            if isinstance(id, str):
                rec = self.xmlid_to_object(id, raise_if_not_found=False)
            else:
                recs = actual_cls.with_context({"lang": self.env.user.lang}).search(
                    [("id", "=", id)]
                )
                if recs:
                    rec = recs[0]
                    self.env["ir.model.synchro.log"].logmsg(
                        "debug",
                        "Found record %(model)s[%(id)s]",
                        res_rec=rec,
                    )
        if id and not rec:
            self.env["ir.model.synchro.log"].logmsg(
                "error",
                "Record %(model)s[%(id)s] not found!",
                res_model=actual_cls._name,
                id=id,
            )
        return rec

    def browse_from_ext_id_in_vals(self, synchro_model, actual_cls, vals):
        loc_ext_id = synchro_model.get_loc_ext_id()
        rec = False
        if loc_ext_id in vals:
            ext_id = vals[loc_ext_id]
            recs = actual_cls.bind_external_ref(loc_ext_id, ext_id)
            if recs:
                rec = recs[0]
                self.env["ir.model.synchro.log"].logmsg(
                    "debug",
                    "Found record %(model)s[%(id)s](ext_id=%(ext_id)s)",
                    res_rec=rec,
                    ctx={"ext_id": ext_id},
                )
        return rec

    def atomic_search(self, cls, domain, company_id=None, company_false=None):
        if not domain:
            return []
        if company_id is None:
            full_domain = domain
        elif company_false:
            full_domain = domain + [
                "|",
                ("company_id", "=", company_id),
                ("company_id", "=", False),
            ]
        else:
            full_domain = domain + [("company_id", "=", company_id)]
        try:
            if hasattr(cls, "sequence"):
                rec = cls.search(full_domain, order="sequence,id", limit=16)
            else:
                rec = cls.search(full_domain, limit=16)
        except BaseException as e:
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["ir.model.synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR %(e)s: %(model)s.atomic_search(%(domain)s)",
                res_model=cls._name,
                errmsg=e,
                ctx={"domain": domain},
            )
            return []
        if not rec and company_id and not company_false:
            return self.atomic_search(
                cls, domain, company_id=company_id, company_false=True
            )
        self.env["ir.model.synchro.log"].logmsg(
            "debug",
            "%(model)s.atomic_search(%(domain)s)",
            res_rec=rec,
            res_model=cls._name,
            ctx={"domain": full_domain},
        )
        return rec

    def exec_search(self, cls, domain, company_id=None):
        rec = self.atomic_search(cls, domain, company_id=company_id)
        if not rec and hasattr(cls, "active"):
            rec = self.atomic_search(
                cls,
                expression.AND([domain, [("active", "=", False)]]),
            )
        return rec

    def bind_record(self, synchro_model, actual_cls, vals, ctx=None):
        rec = self.browse_from_id_in_vals(actual_cls, vals)
        if rec:
            return rec
        rec = self.browse_from_ext_id_in_vals(synchro_model, actual_cls, vals)
        if rec:
            return rec
        ctx = ctx or {}
        loc_ext_id = synchro_model.get_loc_ext_id()
        candidate = None
        if synchro_model.name == "res.company":
            rec = actual_cls.search(
                ["|", (loc_ext_id, "=", False), (loc_ext_id, "=", 0)]
            )
            if len(rec) == 1:
                candidate = rec[0]
                rec = []
        prio = 8
        for keys in unicodes(eval(synchro_model.search_keys)):
            domain = []
            if isinstance(keys, str):
                keys = [keys]
            for key in keys:
                ilike = False
                if key.startswith("!"):
                    key = key[1:]
                    domain.append((key, "=", False))
                    continue
                if key.startswith(("%", "_", "?", "+")):
                    ilike = key[0]
                    key = key[1:]
                if key not in vals:
                    if key in ctx:
                        domain.append((key, "=", ctx[key]))
                    elif key == "type" and synchro_model.name == "res.partner":
                        domain.append((key, "=", "contact"))
                    # elif key in MAGIC_FIELDS.get(synchro_model.name, {}):
                    #     if MAGIC_FIELDS[synchro_model.name][key]:
                    #         domain.append(
                    #             (key, "=", MAGIC_FIELDS[synchro_model.name][key])
                    #         )
                    else:
                        domain = []
                        break
                elif isinstance(vals[key], str) and vals[key] == "" and ilike == "?":
                    domain.append("|")
                    domain.append((key, "=", False))
                    domain.append((key, "=", ""))
                # elif (
                #     key == "amount"
                #     and isinstance(vals[key], str)
                #     and not eval(vals[key])
                #     and ilike != "?"
                # ):
                #     domain = []
                #     break
                # elif key == "amount" and not vals[key] and ilike != "?":
                #     domain = []
                #     break
                elif ilike == "+" and not vals[key]:
                    domain = []
                    break
                elif ilike and ilike not in ("?", "+"):
                    domain.append(
                        (
                            key,
                            "ilike",
                            vals[key].replace(" ", ilike).replace(".", ilike),
                        )
                    )
                else:
                    domain.append((key, "=", vals[key]))
            if domain:
                if loc_ext_id in vals:
                    domain.append("|")
                    domain.append((loc_ext_id, "=", False))
                    domain.append((loc_ext_id, "=", 0))
                company_id = None
                if synchro_model.search_with_company:
                    if vals.get("company_id"):
                        company_id = vals["company_id"]
                    elif synchro_model.synchro_channel_id.company_id:
                        company_id = synchro_model.synchro_channel_id.company_id.id
                    elif synchro_model.name not in MODEL_LAZY_COMPANY:
                        company_id = False
                rec = self.exec_search(actual_cls, domain, company_id=company_id)
                if len(rec) == 1:
                    break
                elif 1 < len(rec) < prio:
                    candidate = rec[0]
                    rec = []
                    prio = len(rec)
                else:
                    rec = []
        if not rec and candidate:
            rec = candidate
        return rec

    @api.model
    def drop_protected_equal_fields(self, backend, vals, rec):
        SynchroModel = self.env["synchro.channel.model"]
        synchro_model = SynchroModel.get_synchro_model_from_loc(backend, rec._name)
        struct = self.env[rec._name].fields_get()
        for loc_name, value in vals.copy().items():
            if loc_name not in struct:
                del vals[loc_name]
                continue
            SynchroField = self.env["synchro.channel.model.field"]
            synchro_field = SynchroField.get_synchro_field(
                synchro_model, loc_name=loc_name
            )
            protect_update = synchro_field.protect_update
            if (
                protect_update == "3"
                or (
                    protect_update == "4"
                    and rec[loc_name]
                    and int(vals[loc_name]) <= int(rec[loc_name])
                )
                or (protect_update == "2" and rec[loc_name])
                or (protect_update == "1" and not vals[loc_name])
            ):
                del vals[loc_name]
                continue
            ftype = struct[loc_name]["type"]
            if not hasattr(rec, loc_name):
                del vals[loc_name]
            elif (
                ftype == "many2one"
                and rec[loc_name]
                and vals[loc_name] == rec[loc_name].id
            ):
                del vals[loc_name]
            elif ftype in ("one2many", "many2many"):
                pass
            elif vals[loc_name] == rec[loc_name]:
                del vals[loc_name]
        return vals

    @api.model
    def create_n_commit(self, cls, vals, only_minimal=False, ctx=None):
        SynchroLog = self.env["ir.model.synchro.log"]
        if not only_minimal and hasattr(cls, "assure_values"):
            vals = cls.assure_values(vals, False)
        if cls._name.startswith("account.move") and not ctx:
            ctx = {"check_move_validity": False}
        try:
            if ctx:
                rec = cls.with_context(ctx).create(vals)
            else:
                rec = cls.create(vals)
            SynchroLog.logmsg(
                "warning", "", res_rec=rec, logrec=self.logrec, values=vals
            )
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            rec = -1
            SynchroLog.logmsg(
                "error",
                "!%(E)s! ERROR %(e)s: %(model)s.create(%(vals)s)",
                res_model=cls._name,
                values=vals,
                errmsg=e,
                errcode=-1,
            )
        return rec

    def rewrite(self, rec, vals, backend, only_minimal=False, ctx=None):
        SynchroLog = self.env["ir.model.synchro.log"]
        if not only_minimal and hasattr(rec, "assure_values"):
            vals = rec.assure_values(vals, rec)
        if hasattr(rec, "active") and not rec.active and "active" not in vals:
            vals["active"] = True
        vals = self.drop_protected_equal_fields(backend, vals, rec)
        if vals:
            try:
                if rec._name.startswith("account.move"):
                    rec.with_context(check_move_validity=False).write(vals)
                else:
                    rec.write(vals)
                SynchroLog.logmsg(
                    "warning", "", res_rec=rec, logrec=self.logrec, values=vals
                )
            except BaseException as e:  # pragma: no cover
                self.env.cr.rollback()  # pylint: disable=invalid-commit
                SynchroLog.logmsg(
                    "error",
                    "!%(E)s! ERROR %(e)s: %(model)s.write(%(vals)s)",
                    res_rec=rec,
                    values=vals,
                    errmsg=e,
                    errcode=-2,
                )
                return -2
        return rec

    @api.model
    def synchro(
        self,
        cls,
        vals,
        backend=None,
        only_minimal=True,
        ttl=None,
    ):
        Cache = self.env["ir.model.synchro.cache"]
        SynchroLog = self.env["ir.model.synchro.log"]
        SynchroModel = self.env["synchro.channel.model"]
        ttl = ttl or (2 if only_minimal else 4)
        vmodel = cls._name
        actual_model = SynchroModel.get_actual_model_name(vmodel)
        if not actual_model:  # pragma: no cover
            Cache.clean_cache()
            SynchroLog.logmsg(
                "error",
                "!%(E)s! Invalid or unknown actual model for %(model)s!",
                res_model=vmodel,
                values=vals,
                errcode=-11,
            )
            return -11
        backend = backend or self.env["synchro.channel"].assign_backend(vals)
        if not backend:  # pragma: no cover
            Cache.clean_cache()
            SynchroLog.logmsg(
                "error",
                "!%(E)s! No channel found!",
                values=vals,
                errcode=-6,
            )
            return -6

        # Cache.open(backend=backend, model=actual_model)
        # if vmodel != actual_model:
        #     Cache.open(backend=backend, model=vmodel)

        self.logrec = SynchroLog.logmsg(
            "warning",
            "%(model)s.synchro(%(vals)s,backend=%(backend)s,min=%(m)s),ttl=%(t)s",
            res_model=vmodel,
            values=vals,
            backend=backend,
            ctx={"m": only_minimal, "t": ttl},
        )

        synchro_model = SynchroModel.get_synchro_model_from_loc(backend, vmodel)
        spec = ""
        saved_vals = vals.copy()
        vals, incomplete_record = synchro_model.map_to_internal(
            vals,
            ttl,
            only_minimal=only_minimal,
            spec=spec,
        )
        if (
            backend.company_id
            and "company_id" in vals
            and vals["company_id"]
            and vals["company_id"] != backend.company_id.id
        ):
            rec = -14
            return rec
        rec = self.bind_record(synchro_model, cls, vals) if vals else None
        if not rec:
            rec = -1
            loc_ext_id = synchro_model.get_loc_ext_id()
            min_vals = {}
            if synchro_model.auth_action not in ("upd", "lock"):
                if only_minimal or incomplete_record:
                    if synchro_model.auth_action == "sync":
                        if loc_ext_id in vals:
                            min_vals[loc_ext_id] = vals[loc_ext_id]
                    else:
                        for loc_name in vals.keys():
                            synchro_field = self.env[
                                "synchro.channel.model.field"
                            ].get_synchro_field(synchro_model, loc_name=loc_name)
                            if synchro_field.required or loc_name == loc_ext_id:
                                min_vals[loc_name] = vals[loc_name]
                    struct = self.env[actual_model].fields_get()
                    valid = True if min_vals else False
                    if valid and Cache.que_waiting_len(backend):
                        for loc_name in struct.keys():
                            synchro_field = self.env[
                                "synchro.channel.model.field"
                            ].get_synchro_field(synchro_model, loc_name=loc_name)
                            if synchro_field.required and loc_name not in min_vals:
                                valid = False
                                break
                    if min_vals != vals:
                        Cache.que_push(
                            backend, "synchro", actual_model, saved_vals, ttl
                        )
                    if valid:
                        rec = self.create_n_commit(cls, min_vals, only_minimal=True)
                elif vals:
                    rec = self.create_n_commit(cls, vals, only_minimal=False)
        else:
            if synchro_model.auth_action in ("ins", "lock"):
                rec = -2
            elif vals:
                rec = self.rewrite(rec, vals, backend, only_minimal=False)
        if backend.load_mode == "direct" and Cache.que_waiting_len(backend):
            # commit every table to avoid too big transaction
            self.env.cr.commit()  # pylint: disable=invalid-commit
            backend.synchro_queue()
        return rec.id if hasattr(rec, "id") else rec

    @api.model
    def generic_synchro(
        self,
        cls,
        vals,
        jacket=None,
        backend=None,
        only_minimal=True,
        ttl=None,
    ):
        SynchroLog = self.env["ir.model.synchro.log"]
        # SynchroLog.logmsg(
        #     "debug",
        #     (
        #         "%(model)s.generic_synchro(%(vals)s"
        #         ",backend=%(backend)s,min=%(m)s)),j=%(j)s,ttl=%(t)s"
        #     ),
        #     res_model=cls._name,
        #     values=vals,
        #     backend=backend,
        #     ctx={"j": jacket, "m": only_minimal, "t": ttl},
        # )
        if isinstance(jacket, str):
            jvals = self.env["synchro.channel"].vals_with_jacket(vals, prefix=jacket)
        elif jacket and backend:
            jvals = backend.vals_with_jacket(vals)
        elif jacket and not backend:  # pragma: no cover
            SynchroLog.logmsg(
                "error",
                "!%(E)s! %(model)s.generic_synchro() w/o remote identification",
                res_model=cls._name,
                values=vals,
                errcode=-7,
            )
        else:
            jvals = vals
        if hasattr(cls, "synchro"):
            return cls.synchro(
                jvals,
                backend=backend,
                only_minimal=only_minimal,
                ttl=ttl,
            )
        else:
            return self.synchro(
                cls,
                jvals,
                backend=backend,
                only_minimal=only_minimal,
                ttl=ttl,
            )

    def push_one_record(self, ext_model, prefix, vals, ttl=None, synchro_model=None):
        SynchroModel = self.env["synchro.channel.model"]
        SynchroLog = self.env["ir.model.synchro.log"]
        Cache = self.env["ir.model.synchro.cache"]

        if synchro_model:
            backend = synchro_model.synchro_channel_id
        else:
            backend = self.env["synchro.channel"].assign_backend(
                {"%s:" % prefix: prefix}
            )
            if backend:
                synchro_model = SynchroModel.get_synchro_model_from_ext(
                    backend, ext_model
                )
        if not backend:  # pragma: no cover
            Cache.clean_cache()
            SynchroLog.logmsg(
                "error",
                "!%(E)s! No backend found on push_one_record(%(model)s,%(vals)s)",
                res_model=ext_model,
                values=vals,
                errcode=-6,
            )
            return -6
        if not synchro_model:  # pragma: no cover
            Cache.clean_cache()
            SynchroLog.logmsg(
                "error",
                "!%(E)s! Unmanaged model push_one_record(%(model)s,%(vals)s,%(t)s)",
                res_model=ext_model,
                values=vals,
                errcode=-8,
                ctx={"t": ttl},
            )
            return -8
        # Cache.open(backend=backend, ext_model=ext_model)
        if (isinstance(vals, dict) and synchro_model.counterpart_pk not in vals) or (
            not isinstance(vals, dict)
            and not hasattr(vals, synchro_model.counterpart_pk)
        ):  # pragma: no cover
            SynchroLog.logmsg(
                "error",
                "!%(E)s! Data of model %(model)s received w/o %(pk)s",
                backend=backend,
                res_model=synchro_model._name,
                ctx={"pk": synchro_model.counterpart_pk},
            )
            return -13
        vmodel = synchro_model.name
        return self.generic_synchro(
            self.env[vmodel],
            vals,
            jacket=True,
            backend=backend,
            ttl=ttl,
        )

    @api.model
    def trigger_one_record(self, ext_model, prefix, ext_id, ttl=None):
        SynchroModel = self.env["synchro.channel.model"]
        SynchroLog = self.env["ir.model.synchro.log"]
        Cache = self.env["ir.model.synchro.cache"]

        if not prefix:  # pragma: no cover
            SynchroLog.logmsg(
                "error",
                "!%(E)s! Unrecognized prefix on trigger_one_record(%(model)s,%(id)s)",
                res_model=ext_model,
                id=ext_id,
                errcode=-7,
            )
            return -7
        backend = self.env["synchro.channel"].assign_backend({"%s:" % prefix: prefix})
        if not backend:  # pragma: no cover
            Cache.clean_cache()
            SynchroLog.logmsg(
                "error",
                "!%(E)s! No backend found on trigger_one_record(%(model)s,%(id)s)",
                res_model=ext_model,
                id=ext_id,
                errcode=-6,
            )
            return -6
        # Cache.open(backend=backend, ext_model=ext_model)
        synchro_model = SynchroModel.get_synchro_model_from_ext(backend, ext_model)
        if not synchro_model:  # pragma: no cover
            Cache.clean_cache()
            SynchroLog.logmsg(
                "error",
                "!%(E)s! Unmanaged model trigger_one_record(%(model)s,%(id)s,%(t)s)",
                res_model=ext_model,
                id=ext_id,
                errcode=-8,
                ctx={"t": ttl},
            )
            return -8
        SynchroLog.logmsg(
            "info",
            "trigger_one_record(%(xmodel)s,%(pfx)s,remote_id=%(xid)s, ttl=%(t)s)",
            res_model=synchro_model.name,
            backend=backend,
            ctx={"xmodel": ext_model, "xid": ext_id, "t": ttl},
        )
        vals = synchro_model.get_counterpart_response(ext_id)
        if not vals or len(vals) != 1:
            return -13  # pragma: no cover
        if isinstance(vals, (tuple, list)):
            vals = vals[0]
        return self.push_one_record(
            ext_model, prefix, vals, ttl=ttl, synchro_model=synchro_model
        )

    @api.model
    def synchro_all_queues(self):  # pragma: no cover
        for backend in self.env["synchro.channel"].search([]):
            backend.synchro_queue()
