#
# Copyright 2018-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging

from odoo import api, fields, models
from python_plus import _c, unicodes

from .ir_model_synchro_cache import (
    DEF_SKEYS,
    MODEL_LAZY_COMPANY,
    CANDIDATE_KEYS,
    ANCILLARY_KEYS,
    ANCILLARY_LINE_KEYS,
)

_logger = logging.getLogger(__name__)


class SynchroChannelModel(models.Model):
    _name = "synchro.channel.model"
    _description = "Model mapping for Synchronization"
    _order = "sequence, id"

    name = fields.Char(
        "Odoo model name",
        required=True,
        attrs=(
            "{'readonly':"
            "[('synchro_channel_id.state','in',['checked','production'])]}"
        ),
    )
    field_uname = fields.Char("Field for foreign search with unique name")
    search_keys = fields.Char(
        "Pythonic key search sequence",
        help="Sequence to use in search record when not yet synchronized\n"
        'i.e. (["name","company_id"],["name"])\n'
        "will search for record with name and company keys; if not found"
        "search for record just with name",
    )
    search_with_company = fields.Boolean("Search with company", default=False)
    disable_psql_inquire = fields.Boolean("Disable sql inquire", default=False)
    childs_name = fields.Char(
        string="Child records field name",
    )
    parent_name = fields.Char(
        string="Parent record field name",
    )
    counterpart_name = fields.Char("Counterpart model name")
    counterpart_pk = fields.Char("Counterpart primary key name", default="id")
    model_spec = fields.Selection(
        [
            ("delivery", "Delivery Address"),
            ("invoice", "Invoice Address"),
            ("address", "Generic Address"),
            ("customer", "Customer"),
            ("supplier", "Supplier"),
            ("company", "Company"),
        ],
        string="Specific search domain",
    )
    auth_action = fields.Selection(
        [
            ("all", "Everything"),
            ("ins", "Only new records"),
            ("upd", "Only Update"),
            ("sync", "Only Synchronization ID"),
            ("lock", "Locked"),
        ],
        string="Authorized actions",
        required=True,
        default="all",
    )
    prefix = fields.Selection(
        [
            ("oe16", "oe16"),
            ("oe12", "oe12"),
            ("oe10", "oe10"),
            ("oe8", "oe8"),
            ("oe7", "oe7"),
        ],
        "Prefix for field names",
        copy=False,
    )
    sequence = fields.Integer("Priority", default=16)
    synchro_channel_id = fields.Many2one("synchro.channel")
    field_ids = fields.One2many(
        "synchro.channel.model.field", "model_id", string="Model mapping"
    )
    state = fields.Selection(
        string="Backend State",
        store=True,
        related="synchro_channel_id.state",
        readonly=True,
    )
    rec_counter = fields.Integer(
        "Import Counter", default=0, help="Last imported record number"
    )

    def get_loc_ext_id(self):
        return (
            "%s_id" % self.prefix
            if self.prefix
            else "" or self.synchro_channel_id.get_loc_ext_id()
        )

    def load_ctx(self, ctx):
        ctx = ctx or {}
        company = self.synchro_channel_id.company_id or self.env.user.company_id
        ctx["company_id"] = ctx.get("company_id", company.id)
        if company.country_id:
            ctx["country_id"] = ctx.get("country_id", company.country_id.id)
        if company.currency_id:
            ctx["currency_id"] = ctx.get("currency_id", company.currency_id.id)
        if self.name == "res.partner":
            ctx["type"] = "contact"
            ctx["is_company"] = True
        return ctx

    def select_by_domain(self, vals, domain):
        # TODO
        return vals

    @api.model
    def get_actual_model_name(self, model):  # pragma: no cover
        actual_model = model
        if model in (
            "res.partner.shipping",
            "res.partner.invoice",
            "res.partner.supplier",
            "res.partner.bank.company",
        ):
            actual_model = model.rsplit(".", 1)[0]
        return actual_model

    def synchro_field_from_ext_ref(self, ext_ref, struct, spec=None):
        Cache = self.env["ir.model.synchro.cache"]
        synchro_field = SynchroField = self.env["synchro.channel.model.field"]
        pfx_depr = "%s_" % self.synchro_channel_id.prefix
        pfx_ext = "%s:" % self.synchro_channel_id.prefix
        loc_ext_id = self.get_loc_ext_id()
        if ext_ref == loc_ext_id:
            # Case #1 - field is external id like <oe12_id>
            is_foreign = True
            loc_name = ext_name = ext_ref
        elif ext_ref.startswith(pfx_ext):
            # Case #2 - field like <oe12:order_id>:
            #           both name and value are of counterpart refs
            is_foreign = True
            ext_name = ext_ref.split(":", 1)[1]
            synchro_field = SynchroField.get_synchro_field(
                self, ext_name=ext_name, spec=spec
            )
            loc_name = synchro_field.name if synchro_field else ""
            if loc_name and loc_name.startswith("."):
                loc_name = ""
        elif ext_ref.startswith(pfx_depr):  # pragma: no cover
            # Case #3 - (deprecated) field like <vg7_order_id>:
            #           local name is odoo but value id is of counterpart ref
            self.env["ir.model.synchro.log"].logmsg(
                "debug",
                "Invalid remote field name %(name)s",
                res_model=self.name,
                backend=self.synchro_channel_id,
                ctx={"name": ext_ref},
            )
            is_foreign = True
            loc_name = ext_ref[len(pfx_depr) :]
            if loc_name == "id":
                loc_name = ext_name = ext_ref
            else:
                synchro_field = SynchroField.get_synchro_field(
                    self, loc_name=loc_name, spec=spec
                )
                ext_name = synchro_field.counterpart_name if synchro_field else ""
                if ext_name.startswith("."):
                    ext_name = ""
        else:
            # Case #4 - field and value are Odoo
            is_foreign = False
            if ext_ref.startswith(":"):
                ext_name = loc_name = ext_ref[1:]
            else:
                ext_name = loc_name = ext_ref
        ftype = struct.get(loc_name, {}).get("type", "char")
        default, apply4, spec2 = synchro_field.get_default_n_apply(ftype=ftype)
        return {
            "id": synchro_field,
            "loc_name": loc_name,
            "ext_name": ext_name,
            "is_foreign": is_foreign,
            "spec": spec or spec2,
            "default": default,
            "apply4": apply4,
            "loc_ext_id": loc_ext_id,
            "type": ftype,
            "protect_update": (
                synchro_field.protect_update
                if synchro_field
                else str(
                    Cache.TABLE_DEF.get(self.name, {})
                    .get(loc_name, {})
                    .get("protect_update", 0)
                )
            ),
            "store": struct.get(loc_name, {}).get("store", True),
            "relation": struct.get(loc_name, {}).get("relation"),
            "selection": struct.get(loc_name, {}).get("selection"),
        }

    @api.model
    def get_offset_value(self, ext_id):  # pragma: no cover
        if isinstance(ext_id, int):
            vmodel = self.name
            if vmodel == "res.partner.invoice":
                offset = 200000000
            elif vmodel == "res.partner.shipping":
                offset = 100000000
            else:
                offset = 0
            if ext_id < offset:
                return ext_id + offset
        return ext_id

    @api.model
    def get_external_pk(self, ext_id):  # pragma: no cover
        if isinstance(ext_id, int):
            return ext_id % 100000000
        return ext_id

    def priority_fields(self, vals, struct, spec=None):
        loc_ext_id = self.get_loc_ext_id()
        childs_name = self.childs_name
        field_list = vals.keys()
        fields = {}
        list_1 = []
        list_2 = []
        list_3 = []
        list_6 = []
        list_8 = []
        list_9 = []
        with_company_id = False
        for ext_ref in field_list:
            field = self.synchro_field_from_ext_ref(ext_ref, struct, spec=spec)
            loc_name = field["loc_name"]
            # ext_name = field["ext_name"]
            ftype = field["type"]
            fields[ext_ref] = field
            if loc_name in (loc_ext_id, "id"):
                list_1.append(ext_ref)
            elif loc_name == "company_id":
                with_company_id = True
                list_2.append(ext_ref)
            elif loc_name == "country_id":
                list_2.append(ext_ref)
            elif self.parent_name and loc_name == self.parent_name:
                list_3.insert(0, ext_ref)
            elif (
                loc_name
                in (
                    "is_company",
                    "electronic_invoice_subjected",
                )
                or ftype == "many2one"
            ):
                list_8.append(ext_ref)
            elif loc_name == childs_name or ftype in ("one2many", "many2many"):
                list_9.append(ext_ref)
            else:
                list_6.append(ext_ref)
        return (
            list_1 + list_2 + list_3 + list_6 + list_8 + list_9,
            with_company_id,
            fields,
        )

    def map_2many_to_local(
        self, vals, field, ext_ref, ttl, only_minimal, incomplete_record, ctx=None
    ):
        Cache = self.env["ir.model.synchro.cache"]
        backend = self.synchro_channel_id
        loc_name = field["loc_name"]
        is_foreign = field["is_foreign"]
        loc_ext_id = self.get_loc_ext_id()
        comodel = field["relation"]
        if comodel in self.env:
            synchro_comodel = self.get_synchro_model_from_loc(backend, comodel)
            vals[loc_name] = []
            if (
                isinstance(vals[ext_ref], str)
                and "." in vals[ext_ref]
                and " " not in vals[ext_ref]
            ):
                # Field is external reference like 'module.reference'
                rec = self.xmlid_to_object(vals[ext_ref], raise_if_not_found=False)
                if rec:
                    vals[loc_name].append((4, rec.id))
            elif is_foreign:
                if isinstance(vals[ext_ref], int):
                    vals[ext_ref] = [vals[ext_ref]]
                if isinstance(vals[ext_ref], (list, tuple)):
                    for item in vals[ext_ref]:
                        if isinstance(item, int):
                            rec = self.env[comodel].bind_external_ref(loc_ext_id, item)
                            if not rec:
                                if (
                                    not synchro_comodel.counterpart_name
                                ):  # pragma: no cover
                                    self.env["ir.model.synchro.log"].logmsg(
                                        "warning",
                                        "No counterpart table for %(model)s",
                                        res_model=comodel,
                                        errcode=-8,
                                    )
                                else:
                                    Cache.que_push(
                                        backend,
                                        "trigger",
                                        synchro_comodel.counterpart_name,
                                        item,
                                        ttl,
                                        ctx,
                                        prio=1 if loc_name == self.childs_name else 2,
                                    )
                        elif isinstance(item, str) and "." in item and " " not in item:
                            # Item is external reference like 'module.reference'
                            rec = self.xmlid_to_object(item, raise_if_not_found=False)
                            if rec:
                                vals[loc_name].append((4, rec.id))
            if vals.get(loc_name) == []:
                del vals[loc_name]
        return vals, incomplete_record

    def map_one2many_to_local(
        self, vals, field, ext_ref, ttl, only_minimal, incomplete_record, ctx=None
    ):
        return self.map_2many_to_local(
            vals, field, ext_ref, ttl, only_minimal, incomplete_record, ctx=ctx
        )

    def map_many2many_to_local(
        self, vals, field, ext_ref, ttl, only_minimal, incomplete_record, ctx=None
    ):
        return self.map_2many_to_local(
            vals, field, ext_ref, ttl, only_minimal, incomplete_record, ctx=ctx
        )

    def map_many2one_to_local(
        self, vals, field, ext_ref, ttl, only_minimal, incomplete_record, ctx=None
    ):
        Cache = self.env["ir.model.synchro.cache"]
        backend = self.synchro_channel_id
        loc_name = field["loc_name"]
        is_foreign = field["is_foreign"]
        loc_ext_id = self.get_loc_ext_id()
        comodel = field["relation"]
        if comodel in self.env:
            synchro_comodel = self.get_synchro_model_from_loc(backend, comodel)
            if (
                isinstance(vals[ext_ref], str)
                and "." in vals[ext_ref]
                and " " not in vals[ext_ref]
            ):
                # Field is external reference like 'module.reference'
                rec = self.xmlid_to_object(vals[ext_ref], raise_if_not_found=False)
                if rec:
                    vals[loc_name] = rec.id
            elif isinstance(vals[ext_ref], int) and comodel in self.env:
                if is_foreign:
                    rec = self.env[comodel].bind_external_ref(loc_ext_id, vals[ext_ref])
                    if rec:
                        vals[loc_name] = rec.id
                    elif synchro_comodel.counterpart_name:
                        if (
                            only_minimal
                            and loc_name == "company_id"
                            and backend.company_id
                            and field["id"].required
                            and comodel
                            not in (
                                "res.partner",
                                "res.users",
                                "product.template",
                                "product.product",
                            )
                        ):
                            vals[loc_name] = ctx["company_id"]
                            Cache.que_push(
                                backend,
                                "trigger",
                                synchro_comodel.counterpart_name,
                                vals[ext_ref],
                                ttl,
                                ctx,
                                prio=1,
                            )
                            incomplete_record |= True
                        elif only_minimal and self.name not in MODEL_LAZY_COMPANY:
                            Cache.que_push(
                                backend,
                                "trigger",
                                synchro_comodel.counterpart_name,
                                vals[ext_ref],
                                ttl,
                                ctx,
                                prio=2,
                            )
                            incomplete_record |= True
                        else:
                            Cache.que_push(
                                backend,
                                "trigger",
                                synchro_comodel.counterpart_name,
                                vals[ext_ref],
                                ttl,
                                ctx,
                                prio=2,
                            )
                            incomplete_record = True
                    else:  # pragma: no cover
                        self.env["ir.model.synchro.log"].logmsg(
                            "warning",
                            "No counterpart table for %(model)s",
                            res_model=comodel,
                            errcode=-8,
                        )
                else:
                    rec = self.env[comodel].search([("id", "=", vals[ext_ref])])
                    if rec:
                        vals[loc_name] = rec.id
            if (
                loc_name in vals
                and vals[loc_name]
                and loc_name in ("company_id", "country_id", "currency_id")
            ):
                ctx[loc_name] = vals[loc_name]
        return vals, incomplete_record

    def map_selection_to_local(
        self, vals, field, ext_ref, ttl, only_minimal, incomplete_record, ctx=None
    ):
        Cache = self.env["ir.model.synchro.cache"]
        backend = self.synchro_channel_id
        loc_name = field["loc_name"]
        vals[loc_name] = vals[ext_ref]
        if loc_name in ("lang", "lang_id"):
            comodel = "res.lang"
            rec = self.env[comodel].search([("code", "=", vals[loc_name])])
            if not rec:
                synchro_comodel = self.get_synchro_model_from_loc(backend, comodel)
                Cache.que_push(
                    backend,
                    "synchro",
                    synchro_comodel,
                    {"code": vals[ext_ref]},
                    ttl,
                    ctx,
                    prio=1,
                )
        valid = False
        for item in field["selection"]:
            if (isinstance(item, (list, tuple)) and vals[loc_name] == item[0]) or (
                not isinstance(item, (list, tuple)) and vals[loc_name] == item
            ):
                valid = True
                break
        if not valid:
            self.env["ir.model.synchro.log"].logmsg(
                "error",
                "!%(E)s! Invalid value %(vals)s for %(name)s",
                values=vals[loc_name],
                ctx={"name": loc_name},
                errcode=-7,
            )
            del vals[loc_name]
        return vals, incomplete_record

    def map_base_to_local(
        self, vals, field, ext_ref, ttl, only_minimal, incomplete_record, ctx=None
    ):
        vals[field["loc_name"]] = vals[ext_ref]
        return vals, incomplete_record

    @api.model
    def map_to_internal(self, vals, ttl, only_minimal=None, spec=None, ctx=None):
        self.ensure_one()
        Cache = self.env["ir.model.synchro.cache"]
        IrModel = self.env["ir.model.synchro"]
        ctx = ctx or {}
        actual_model = self.get_actual_model_name(self.name)
        struct = self.env[actual_model].fields_get()
        magic_fields = []
        for bend in self.synchro_channel_id.search([]):
            magic_fields.append(bend.get_loc_ext_id())
        field_list, with_company_id, fields = self.priority_fields(
            vals, struct, spec=spec
        )
        if (
            self.search_with_company
            and not with_company_id
            and actual_model not in MODEL_LAZY_COMPANY
        ):
            vals["company_id"] = ctx["company_id"]
        incomplete_record = False
        for ext_ref in field_list:
            field = fields[ext_ref]
            synchro_field = field["id"]
            loc_name = field["loc_name"]
            ext_name = field["ext_name"]
            loc_ext_id = self.get_loc_ext_id()
            ftype = field["type"]
            if (
                (not loc_name and not synchro_field)
                or loc_name in Cache.SUPERMAGIC_COLUMNS
                or loc_name in magic_fields
            ):
                if ext_name == self.counterpart_pk:
                    vals[loc_ext_id] = self.get_offset_value(
                        IrModel.cast_type(vals[ext_ref], actual_model, field["type"])
                    )
                del vals[ext_ref]
                continue
            vals[ext_ref] = IrModel.cast_type(
                vals[ext_ref], actual_model, field["type"]
            )
            if (not field["is_foreign"] or loc_name != loc_ext_id) and field["apply4"]:
                vals = synchro_field.do_apply(
                    vals,
                    field,
                    ext_ref,
                )
            if ext_name == self.counterpart_pk:
                vals[loc_name] = self.get_offset_value(vals[ext_ref])
            elif (
                loc_name not in vals
                and ext_ref in vals
                and vals[ext_ref]
                and loc_name not in ("id", loc_ext_id)
                and field["store"]
            ):
                method = "map_%s_to_local" % ftype
                method = method if hasattr(self, method) else "map_base_to_local"
                vals, incomplete_record = getattr(self, method)(
                    vals, field, ext_ref, ttl, only_minimal, incomplete_record, ctx=ctx
                )
            if ext_ref in vals and loc_name != ext_ref:
                del vals[ext_ref]
        for loc_name, value in vals.copy().items():
            if value is None:
                del vals[loc_name]
        return vals, incomplete_record

    def build_odoo_synchro_model(self, backend, ext_model=None, model=None):
        # IrModelSynchro = self.env["ir.model.synchro"]
        Cache = self.env["ir.model.synchro.cache"]
        SynchroModelField = self.env["synchro.channel.model.field"]
        SynchroApi = self.env["synchro.api"]

        if (
            backend.identity != "odoo"
            or (not model and not ext_model)
            or (model and not Cache.is_manageable(model))
        ):  # pragma: no cover
            return False

        magic_fields = []
        for bend in backend.search([]):
            magic_fields.append(bend.get_loc_ext_id())
        synchro_model = False
        if not ext_model and model:
            synchro_model = self.search(
                [("name", "=", model), ("synchro_channel_id", "=", backend.id)]
            )
        elif ext_model:
            synchro_model = self.search(
                [
                    ("counterpart_name", "=", ext_model),
                    ("synchro_channel_id", "=", backend.id),
                ]
            )
        if not synchro_model:
            if model:
                actual_model = self.get_actual_model_name(model)
                ext_model = SynchroApi.odoo_tnl_local_model_to_ext(
                    backend, actual_model
                )
            else:
                actual_model = SynchroApi.odoo_tnl_ext_model_to_local(
                    backend, ext_model
                )
            if actual_model not in self.env:  # pragma: no cover
                return False
            if not Cache.is_manageable(actual_model):  # pragma: no cover
                return False
            vals = {
                "synchro_channel_id": backend.id,
                "name": actual_model,
                "counterpart_name": ext_model,
                "sequence": max([x.sequence for x in backend.search([])] or 15) + 1,
                "auth_action": "sync" if actual_model == "res.groups" else "all",
            }
            try:
                synchro_model = self.create(vals)
            except BaseException as e:  # pragma: no cover
                self.env.cr.rollback()  # pylint: disable=invalid-commit
                self.env["ir.model.synchro.log"].logmsg(
                    "error",
                    "!%(E)s! ERROR %(e)s: %(model)s.create(%(vals)s)",
                    res_model=self._name,
                    values=vals,
                    errmsg=e,
                    errcode=-1,
                )
                return False

        actual_model = synchro_model.name
        session = backend.get_session()
        remote_list = self.env["synchro.api"].get_field_list(
            session, backend, actual_model, magic_fields=magic_fields
        )
        for loc_name, ext_name in remote_list:
            SynchroModelField.build_odoo_synchro_model_field(
                synchro_model, loc_name, ext_name
            )
        return synchro_model

    @api.multi
    def analyze_synchro_model(self):
        def is_classified(name):
            return name in unique_fields + candidate_fields + ancillary_fields

        def ignore_field(model, name):
            return (
                name in ("parent_id", "sequence")
                and model in ("res.company", "res.partner.bank")
            ) or (name in ("credit", "debit") and model.startswith("res.partner"))

        def actual_name(name):
            return name[1:] if name.startswith(("+", "!", "%", "_", "-")) else name

        magic_fields = []
        for bend in self.synchro_channel_id.search([]):
            magic_fields.append(bend.get_loc_ext_id())
        self.ensure_one()
        actual_model = self.name
        if actual_model not in self.env:
            if self.auth_action != "lock":
                self.auth_action = "lock"
            return
        elif self.auth_action == "lock":
            self.auth_action = "all"
        struct = self.env[actual_model].fields_get()

        child_models = []
        if actual_model == "product.template":
            child_models = ["product.product"]
        else:
            for suffix in (".line", ".rate", ".state", ".tax"):
                child_models.append(actual_model + suffix)
        for synchro_field in self.field_ids:
            if (
                synchro_field.name in struct
                and struct[synchro_field.name]["type"] == "one2many"
                and struct[synchro_field.name]["relation"] in child_models
            ):
                self.childs_name = synchro_field.name
                break

        if actual_model == "product.product":
            parent_model = "product.template"
        else:
            parent_model = actual_model.rsplit(".", 1)[0]
        if parent_model in self.env:
            for synchro_field in self.field_ids:
                if (
                    synchro_field.name in struct
                    and struct[synchro_field.name]["type"] == "many2one"
                    and struct[synchro_field.name]["relation"] == parent_model
                ):
                    self.parent_name = synchro_field.name
                    break

        if self.synchro_channel_id.identity != "odoo":
            # For Odoo model, protection was set by build_odoo_synchro_model_field()
            for synchro_field in self.field_ids:
                protect_update, required = synchro_field.get_default_protection(
                    magic_fields=magic_fields
                )
                synchro_field.write(
                    {"protect_update": protect_update, "required": required}
                )

        #
        # Try to build the search keys rules; avery rules is a set of search fields,
        # Field are in 3 categories: unique keys, candidate keys and ancillary keys
        # - "Unique" are fields with unique index that is enough to search for record
        # - "Candidate" are field inside unique index with other fields that are,
        #    together, enough to search for record
        # - "Candidate" are also magic fields mostly used which can be used to search
        #    for record with other fields, mainly "Ancillary"
        # - "Ancillary" are supplemental fields which help to build a set of search keys
        #    They could be used in postgres multi-fields unique index
        #
        unique_fields = []
        candidate_fields = []
        ancillary_fields = []
        usable_fields = [x.name for x in self.field_ids if x.name in struct]
        skeys = []
        # From psql get indexes format [{"keys": keys}]
        unique_indexes = (
            []
            if self.disable_psql_inquire
            else self.query_index_fields(actual_model, unique=True)
        )
        for index, item in unique_indexes.items():
            candidates = []
            keys = []
            for candidate in item["key"]:
                if candidate in usable_fields and candidate not in (
                    "company_id",
                    "parent_id",
                    self.parent_name,
                ):
                    candidates.append(_c(candidate))
                    keys.append(_c("+" + candidate))
            if len(candidates) == 1 and candidates[0] not in unique_fields:
                unique_fields.append(_c(candidates[0]))
            if keys:
                for key in keys:
                    key = actual_name(key)
                    if key not in usable_fields or is_classified(key):
                        # Not usable or already classified
                        continue
                    if key in ANCILLARY_KEYS + ANCILLARY_LINE_KEYS:
                        ancillary_fields.append(_c(key))
                        continue
                    if struct[key]["type"] in ("char", "selection", "int", "float"):
                        candidate_fields.append(_c(key))
                    else:
                        ancillary_fields.append(_c(key))
        for loc_name in CANDIDATE_KEYS:
            if (
                loc_name in usable_fields
                and not is_classified(loc_name)
                and loc_name not in candidate_fields
            ):
                candidate_fields.append(_c(loc_name))
        for keys in DEF_SKEYS.get(actual_model, []):
            if keys not in skeys:
                skeys.append(keys)
        if actual_model == "res.users":
            ancillary_fields = []
        else:
            if self.parent_name:
                ancillary_fields.insert(0, self.parent_name)
            for loc_name in ANCILLARY_KEYS:
                # TODO>
                if (
                    loc_name not in usable_fields
                    or loc_name in ANCILLARY_LINE_KEYS
                    or is_classified(loc_name)
                ):
                    continue
                if ignore_field(actual_model, loc_name):
                    continue
                if (
                    loc_name != self.parent_name
                    and loc_name in struct
                    and loc_name not in ancillary_fields
                ):
                    ancillary_fields.append(_c(loc_name))
            if len(ancillary_fields) > 2:
                for loc_name in (
                    "is_company",
                    "left_id",
                    "right_id",
                ):
                    if len(ancillary_fields) > 2 and loc_name in ancillary_fields:
                        del ancillary_fields[ancillary_fields.index(loc_name)]
            if self.parent_name:
                for loc_name in ANCILLARY_LINE_KEYS:
                    if ignore_field(actual_model, loc_name):
                        continue
                    if loc_name in struct and loc_name not in ancillary_fields:
                        ancillary_fields.append(_c(loc_name))
        required_ancillary = []
        for index, item in unique_indexes.items():
            if not item["u"]:
                continue
            required_ancillary += [
                x
                for x in item["key"]
                if x in ancillary_fields
                or x in ("company_id", "parent_id", self.parent_name)
            ]
        for synchro_field in self.field_ids:
            if synchro_field.name in required_ancillary and not synchro_field.required:
                synchro_field.write({"required": True})
        for loc_name in unique_fields:
            skeys.append(_c(["+" + loc_name]) + ancillary_fields)
        name4key = []
        for loc_name in candidate_fields:
            if loc_name == "code" and "default_code" in name4key:
                continue
            if loc_name == "vat" and actual_model == "res.users":
                continue
            if len(name4key) < 2 or loc_name == "name":
                name4key.append(_c(loc_name))
        if len(name4key) > 1:
            skeys.append(name4key + ancillary_fields)
            if "name" in name4key and ancillary_fields:
                if len(name4key) > 2:
                    skeys.append(
                        [
                            "+" + x if i == 0 else "?" + x if x != "name" else x
                            for (i, x) in enumerate(name4key)
                        ]
                        + ancillary_fields
                    )
                skeys.append(
                    ["%" + x if x == "name" else x for x in name4key] + ancillary_fields
                )
                skeys.append(
                    ["+" + x for x in name4key if x != "name"] + ancillary_fields
                )
                skeys.append(
                    ["!" + x if x != "name" else x for x in name4key] + ancillary_fields
                )
        for loc_name in name4key:
            keys = ["+" + loc_name]
            if actual_model != "res.users":
                keys += ancillary_fields
            if keys not in skeys:
                skeys.append(keys)
        if "code" in name4key and ancillary_fields and not self.parent_name:
            skeys.append(["+code"])
        if actual_model == "account.tax":
            skeys.append(["+description", "+type_tax_use"])
            skeys.append(["+amount", "+type_tax_use"])
        if "name" in name4key and ancillary_fields and not self.parent_name:
            skeys.append(["+name"])
        if not skeys and ancillary_fields:
            skeys.append(ancillary_fields)
        required_fields = [
            x.name
            for x in self.field_ids
            if x.required
            and x.name not in ancillary_fields
            and x.name not in ("company_id", "parent_id", self.parent_name)
            and x.name not in magic_fields
        ]
        uname = ""
        for keys in skeys:
            if uname:
                break
            for key in keys:
                if key in required_fields:
                    uname = key
                    break
        if not uname:
            uname = actual_name(skeys[0][0])
        for synchro_field in self.field_ids:
            if synchro_field.name in unique_fields:
                vals = {"search_role": "unique"}
            elif synchro_field.name in candidate_fields:
                vals = {"search_role": "candidate"}
            elif synchro_field.name in ancillary_fields:
                vals = {"search_role": "ancillary"}
            else:
                vals = {}
            if synchro_field.name == uname:
                vals["required"] = True
            if vals:
                synchro_field.write(vals)
        self.field_uname = uname
        self.search_keys = unicodes(str(skeys))
        if "company_id" in struct and actual_model != "res.users":
            self.search_with_company = True
        else:
            self.search_with_company = False

    def get_synchro_model_from_ext(self, backend, ext_model):
        synchro_model = self.search(
            [
                ("synchro_channel_id", "=", backend.id),
                ("counterpart_name", "=", ext_model),
            ]
        )
        if len(synchro_model) == 1:
            return synchro_model
        return self.env["synchro.channel.model"]  # pragma: no cover

    def get_synchro_model_from_loc(self, backend, model):
        synchro_model = self.search(
            [
                ("synchro_channel_id", "=", backend.id),
                ("name", "=", model),
            ]
        )
        if len(synchro_model) == 1:
            return synchro_model
        return self.env["synchro.channel.model"]  # pragma: no cover

    def get_counterpart_response(self, ext_id=False, mode=None):
        """Get data from counterpart"""
        Cache = self.env["ir.model.synchro.cache"]
        SynchroLog = self.env["ir.model.synchro.log"]
        backend = self.synchro_channel_id
        vmodel = self.name
        if backend.state not in ("checked", "production"):  # pragma: no cover
            SynchroLog.logmsg(
                "error",
                "!%(E)s! Cannot get data from backend %(backend)s due invalid state",
                backend=backend,
                model=vmodel,
                errcode=-13,
            )
            return False
        if not Cache.is_manageable(vmodel):  # pragma: no cover
            return False
        # Cache.open(backend=backend, model=vmodel)
        session = backend.get_session()
        return self.env["synchro.api"].get_response(session, self, ext_id=ext_id)

    @api.model
    def query_index_fields(
        self, model, index_name=None, flat=None, unique=None, with_id=False
    ):
        # Inquire postgresql to get unique indexes that can be used to evaluate search
        # keys
        # @model is Odoo model nale
        # @index_name select just the psql index name
        # @flat return field name list, no aggregated by index name
        # @unique return just unique index name or unique field (unique='field')
        # @with_id include index with id field
        #
        # return dict of index names like {"u": unique flag, "keys": field list}
        #
        INDEX_FIELDS = """
        select i.relname as index_name,
               t.relname as table_name,
               a.attname as column_name,
               ix.indisunique as unique
        from pg_class t,
             pg_class i,
             pg_index ix,
             pg_attribute a
        where
             t.oid = ix.indrelid
             and i.oid = ix.indexrelid
             and a.attrelid = t.oid
             and a.attnum = ANY(ix.indkey)
             and t.relkind = 'r'
             and t.relname = '%s'
        order by t.relname, i.relname;"""
        res = {}
        try:
            self._cr.execute(  # pylint: disable=E8103
                INDEX_FIELDS % model.replace(".", "_")
            )
        except BaseException:
            # If postgresql version is not compatible, ignore unique keys analysis
            return res
        for row in self.env.cr.fetchall():
            if index_name and index_name != row[0]:
                continue
            if unique and not row[3]:
                continue
            else:
                if row[0] not in res:
                    res[row[0]] = {}
                    res[row[0]]["u"] = row[3]
                    res[row[0]]["key"] = []
                res[row[0]]["key"].append(row[2])
        if not with_id:
            for index, item in res.copy().items():
                if item["key"] == ["id"]:
                    del res[index]
        if unique:
            for index, item in res.copy().items():
                if not item["u"] or (unique == "field" and len(item["key"]) > 1):
                    del res[index]
        if flat:
            result = []
            for index, item in res.items():
                for field in item["key"]:
                    if field not in result:
                        result.append(field)
            res = result
        return res

    @api.multi
    def write(self, vals):
        self.env["ir.model.synchro.cache"].clean_cache()
        return super().write(vals)
