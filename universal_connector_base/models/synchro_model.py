#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging

from odoo import _, api, fields, models
from odoo.osv import expression
from odoo.exceptions import UserError
from python_plus import _c, unicodes

from .synchro_cache import (
    DEF_SKEYS,
    MODEL_LAZY_COMPANY,
    CANDIDATE_KEYS,
    ANCILLARY_KEYS,
    ANCILLARY_LINE_KEYS,
)

_logger = logging.getLogger(__name__)


class SynchroChannelModel(models.Model):
    _name = "synchro.model"
    _description = "Model mapping for Synchronization"
    _order = "sequence, id"

    _sql_constraints = [
        (
            "model_uniq",
            "unique (backend_id,name,model_spec,counterpart_name)",
            "Local model name, spec and counterpart name must be unique per backend!",
        )
    ]

    model_id = fields.Many2one(
        "ir.model",
        string="Odoo model name",
        # required=True,
        attrs=("{'readonly':" "[('backend_id.state','in',['ready','run'])]}"),
        help="The Odoo model this field belongs to",
    )
    name = fields.Char(
        # related="model_id.model",
        string="Odoo model name",
        # store=True,
        # readonly=True,
        required=True,
        attrs=("{'readonly':" "[('backend_id.state','in',['ready','run'])]}"),
    )
    field_uname = fields.Char(
        "Search by unique name", help="Field for foreign search with unique name"
    )
    search_keys = fields.Char(
        "Pythonic key search sequence",
        help="Sequence to use in search record when not yet synchronized\n"
        'i.e. (["name","company_id"],["name"])\n'
        "will search for record with name and company keys; if not found"
        "search for record just with name",
    )
    search_with_company = fields.Boolean("Search with company", default=False)
    disable_psql_inquire = fields.Boolean(
        "Disable sql inquire",
        default=False,
        help="Disable postgres inquire to get indexes and field information",
    )
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
        string="Model variant",
        help=(
            "Variant for model when Odoo model and counterpart table relationship"
            " is not one 2 one"
        ),
    )
    auth_action = fields.Selection(
        [
            ("all", "Everything"),
            # ("i+u", "New + recent Update"),
            ("ins", "Only new records"),
            ("upd", "Only update"),
            ("sync", "Only ext.ID"),
            ("lock", "Locked"),
        ],
        string="Authorized actions",
        required=True,
        default="all",
        help="This field can limit action on record; values are:\n"
        "Eveything: no limits, records can be update or created\n"
        "New + recent Update: record can be created; update only more recent\n"
        "Only new records: record can be created but not updated\n"
        "Only update: record can be updated but not created\n"
        "Only ext.ID: no action on record, only set counterpart ID\n"
        "Locked: no action on record, model is protected\n",
    )
    prefix = fields.Selection(
        [
            ("odoo16", "odoo16"),
            ("odoo12", "odoo12"),
            ("odoo10", "odoo10"),
            ("oe8", "oe8"),
            ("oe7", "oe7"),
        ],
        "Download Prefix",
        copy=False,
        help="Download prefix which counterparty must use to identify itself.\n"
        "Format is [a-zA-Z]{2}[a-zA-Z0-9]+\n"
        "Counterparty have to issue this prefix when calls trigger_one_record();"
        "it has to add this prefix in data dictionary when calls synchro()"
        " to issue its internal field name and field value.\n"
        "Prefix activates the right translation functions of Universal Connector."
        "i.e. with prefix='odoo8'\n"
        "<partner_id> means ID of current Odoo database\n"
        "<odoo8:partner_id> means counterpart partner ID and name\n",
    )
    use_remote_xref = fields.Selection(
        [
            ("auto", "Automatic"),
            ("no", "Never"),
            ("yes", "Always"),
        ],
        string="Load with Ext.Ref.",
        required=True,
        default="auto",
        help=(
            "If counterparty is Odoo you can synchronize record using"
            " Odoo external reference (ir.model.data)\n"
            "This option slows data download but make easier to find the"
            " right record to link with remote."
        ),
    )
    sequence = fields.Integer("Priority", default=16)
    backend_id = fields.Many2one("synchro.backend", string="Backend")
    field_ids = fields.One2many("synchro.mapper", "model_id", string="Model mapping")
    state = fields.Selection(
        string="Backend State",
        store=True,
        related="backend_id.state",
        readonly=True,
    )
    rec_counter = fields.Integer(
        "Import Counter", default=0, help="Last imported record number"
    )

    @api.multi
    @api.depends("name", "partner_ref")
    def name_get(self):
        result = []
        for dir_mapper in self:
            if dir_mapper.name and dir_mapper.counterpart_name:
                name = "%s / %s " % (dir_mapper.name, dir_mapper.counterpart_name)
            elif dir_mapper.name:
                name = "%s.%s" % (dir_mapper.name, dir_mapper.model_spec or "")
            else:
                name = "%s:%s" % (
                    dir_mapper.model_spec or "",
                    dir_mapper.counterpart_name,
                )
            result.append((dir_mapper.id, name))
        return result

    def get_loc_ext_id(self):
        return (
            "%s_id" % self.prefix
            if self.prefix
            else "" or self.backend_id.get_loc_ext_id()
        )

    def load_ctx(self, ctx):
        ctx = ctx or {}
        ctx["logrec"] = ctx.get("logrec") or self.env["synchro.log"]
        company = self.backend_id.company_id or self.env.user.company_id
        ctx["company_id"] = ctx.get("company_id", company.id)
        if company.country_id:
            ctx["country_id"] = ctx.get("country_id", company.country_id.id)
        if company.currency_id:
            ctx["currency_id"] = ctx.get("currency_id", company.currency_id.id)
        if self.name == "res.partner":
            ctx["type"] = "contact"
            ctx["is_company"] = True
        return ctx

    def update_ctx(self, ctx, loc_name, value):
        if value and loc_name in ("company_id", "country_id", "currency_id"):
            ctx[loc_name] = value
        return ctx

    def select_by_domain(self, vals, domain):
        # TODO
        return vals

    @api.model
    def split_binding_model_n_spec(self, model, spec=False):  # pragma: no cover
        binding_model = model
        if model in (
            "res.partner.shipping",
            "res.partner.invoice",
            "res.partner.supplier",
            "res.partner.bank.company",
        ):
            binding_model, spec = model.rsplit(".", 1)
            if spec == "shipping":
                spec = "delivery"
        return binding_model, spec

    def get_vmodel(self, binding_model, spec):
        if binding_model == "res.partner" and spec:
            vmodel = binding_model + "." + spec
        else:
            vmodel = binding_model
        return vmodel

    def get_mapper(self, loc_name=None, ext_name=None, spec=None):
        Mapper = self.env["synchro.mapper"]
        domain = [("model_id", "=", self.id)]
        if loc_name:
            if ext_name:
                domain.append("|")
                domain.append(("name", "=", False))
            domain.append(("name", "=", loc_name))
        if ext_name:
            if loc_name:
                domain.append("|")
                domain.append(("counterpart_name", "=", False))
            domain.append(("counterpart_name", "=", ext_name))
        if spec is not None:
            domain.append(("spec", "=", spec))
        mapper = Mapper.search(domain)
        return mapper if len(mapper) == 1 else Mapper

    def get_map_from_ext_ref(self, ext_ref, struct, spec=None):
        Cache = self.env["synchro.cache"]
        mapper = self.env["synchro.mapper"]
        pfx_depr = "%s_" % self.backend_id.prefix
        pfx_ext = "%s:" % self.backend_id.prefix
        loc_ext_id = self.get_loc_ext_id()
        if ext_ref == loc_ext_id:
            # Case #1 - field is external id like <odoo12_id>
            is_foreign = True
            loc_name = ext_name = ext_ref
        elif ext_ref.startswith(pfx_ext):
            # Case #2 - field like <odoo12:order_id>:
            #           both name and value are of counterpart refs
            is_foreign = True
            ext_name = ext_ref.split(":", 1)[1]
            if ext_name == self.counterpart_pk:
                loc_name = loc_ext_id
            else:
                mapper = self.get_mapper(ext_name=ext_name)
                loc_name = mapper and mapper.name or ""
                if loc_name and loc_name.startswith("."):
                    loc_name = ""
        elif ext_ref.startswith(pfx_depr):  # pragma: no cover
            # Case #3 - (deprecated) field like <vg7_order_id>:
            #           local name is odoo but value id is of counterpart ref
            self.env["synchro.log"].logmsg(
                "debug",
                "Invalid remote field name %(name)s",
                res_model=self.name,
                backend=self.backend_id,
                ctx={"name": ext_ref},
            )
            is_foreign = True
            loc_name = ext_ref[len(pfx_depr):]
            if loc_name == "id":
                loc_name = ext_name = ext_ref
            else:
                mapper = self.get_mapper(loc_name=loc_name)
                ext_name = mapper and mapper.counterpart_name or ""
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
        default, apply4, spec2 = mapper.extract_default_n_apply(ftype=ftype)
        return {
            "id": mapper,
            "loc_name": loc_name,
            "ext_name": ext_name,
            "is_foreign": is_foreign,
            "spec": spec or spec2,
            "default": default,
            "apply4": apply4,
            "loc_ext_id": loc_ext_id,
            "type": ftype,
            "protect_update": (
                mapper.protect_update
                if mapper
                else str(
                    Cache.TABLE_DEF.get(self.name, {})
                    .get(loc_name, {})
                    .get("protect_update", 0)
                )
            ),
            "sequence": mapper.sequence if mapper else 16,
            "store": struct.get(loc_name, {}).get("store", True),
            "relation": struct.get(loc_name, {}).get("relation"),
            "selection": struct.get(loc_name, {}).get("selection"),
        }

    @api.model
    def get_offset_value(self, ext_id, model_spec=None):  # pragma: no cover
        if isinstance(ext_id, int):
            vmodel = self.name
            binding_model, spec = self.split_binding_model_n_spec(vmodel)
            model_spec = model_spec or spec
            if model_spec == "invoice":
                offset = 200000000
            elif model_spec == "delivery":
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

    @api.model
    def drop_protected_equal_fields(self, vals, rec):
        magic_fields = self.backend_id.get_magic_fields()
        loc_ext_id = self.get_loc_ext_id()
        struct = self.env[rec._name].fields_get()
        for loc_name, value in vals.copy().items():
            if loc_name not in struct or (
                self.auth_action == "sync" and loc_name != loc_ext_id
            ) or loc_name in magic_fields and not vals[loc_name]:
                del vals[loc_name]
                continue
            mapper = self.get_mapper(loc_name=loc_name)
            protect_update = mapper.protect_update
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
            elif ftype == "many2one":
                if (rec[loc_name] and vals[loc_name] == rec[loc_name].id) or (
                    not rec[loc_name] and not vals[loc_name]
                ):
                    del vals[loc_name]
            elif ftype in ("one2many", "many2many"):
                pass
            elif vals[loc_name] == rec[loc_name]:
                del vals[loc_name]
        if hasattr(rec, "active") and not rec.active and "active" not in vals:
            vals["active"] = True
        return vals

    def priority_fields(self, vals, struct):
        # loc_ext_id = self.get_loc_ext_id()
        # childs_name = self.childs_name
        field_list = vals.keys()
        maps = {}
        list_1 = []
        list_2 = []
        list_3 = []
        list_4 = []
        list_6 = []
        list_8 = []
        list_9 = []
        with_company_id = False
        for ext_ref in field_list:
            field = self.get_map_from_ext_ref(ext_ref, struct)
            if field["sequence"] <= 2:
                list_1.append(ext_ref)
            elif field["sequence"] <= 4:
                list_2.append(ext_ref)
            elif field["sequence"] <= 6:
                list_3.append(ext_ref)
            elif field["sequence"] <= 8:
                list_4.append(ext_ref)
            elif field["sequence"] <= 12:
                list_6.append(ext_ref)
            elif field["sequence"] <= 32:
                list_8.append(ext_ref)
            else:
                list_9.append(ext_ref)
            maps[ext_ref] = field
        return (
            list_1 + list_2 + list_3 + list_6 + list_8 + list_9,
            with_company_id,
            maps,
        )

    def map_2many_to_local(
        self, vals, field, ext_ref, ttl, only_minimal, incomplete_record, ctx=None
    ):
        Cache = self.env["synchro.cache"]
        backend = self.backend_id
        loc_name = field["loc_name"]
        is_foreign = field["is_foreign"]
        loc_ext_id = self.get_loc_ext_id()
        comodel = field["relation"]
        if comodel in self.env:
            synchro_comodel = backend.get_dir_mapper(model=comodel)
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
                            if not rec and field["id"].protect_update != "3":
                                if (
                                    not synchro_comodel.counterpart_name
                                ):  # pragma: no cover
                                    self.env["synchro.log"].logmsg(
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
                                        False,
                                        item,
                                        ttl,
                                        ctx,
                                        prio=1 if loc_name == self.childs_name else 3,
                                    )
                        elif (
                            isinstance(item, str)
                            and "." in item
                            and " " not in item
                        ):
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
        Cache = self.env["synchro.cache"]
        backend = self.backend_id
        loc_name = field["loc_name"]
        is_foreign = field["is_foreign"]
        loc_ext_id = self.get_loc_ext_id()
        comodel = field["relation"]
        if comodel in self.env:
            synchro_comodel = backend.get_dir_mapper(model=comodel)
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
                            and (comodel == "res.currency.rate"
                                 or comodel not in MODEL_LAZY_COMPANY)
                        ):
                            vals[loc_name] = ctx["company_id"]
                            Cache.que_push(
                                backend,
                                "trigger",
                                synchro_comodel.counterpart_name,
                                False,
                                vals[ext_ref],
                                ttl,
                                ctx,
                                prio=1,
                            )
                            incomplete_record |= True
                        elif only_minimal and field["id"].protect_update != "3":
                            Cache.que_push(
                                backend,
                                "trigger",
                                synchro_comodel.counterpart_name,
                                False,
                                vals[ext_ref],
                                ttl,
                                ctx,
                                prio=2,
                            )
                            incomplete_record |= True
                    else:  # pragma: no cover
                        self.env["synchro.log"].logmsg(
                            "warning",
                            "No counterpart table for %(model)s",
                            res_model=comodel,
                            errcode=-8,
                        )
                else:  # pragma: no cover
                    rec = self.env[comodel].search([("id", "=", vals[ext_ref])])
                    if rec:
                        vals[loc_name] = rec.id
            self.update_ctx(ctx, loc_name, vals.get(loc_name))
        return vals, incomplete_record

    def map_selection_to_local(
        self, vals, field, ext_ref, ttl, only_minimal, incomplete_record, ctx=None
    ):
        Cache = self.env["synchro.cache"]
        backend = self.backend_id
        loc_name = field["loc_name"]
        vals[loc_name] = vals[ext_ref]
        if loc_name in ("lang", "lang_id"):
            comodel = "res.lang"
            rec = self.env[comodel].search([("code", "=", vals[loc_name])])
            if not rec:
                # synchro_comodel = backend.get_dir_mapper(model=comodel)
                Cache.que_push(
                    backend,
                    "synchro",
                    comodel,
                    False,
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
        if not valid:  # pragma: no cover
            self.env["synchro.log"].logmsg(
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
    def map_to_internal(self, vals, ttl, only_minimal=None, model_spec=None, ctx=None):
        self.ensure_one()
        Cache = self.env["synchro.cache"]
        IrModel = self.env["ir.model.synchro"]
        ctx = ctx or {}
        binding_model = self.split_binding_model_n_spec(self.name)[0]
        struct = self.env[binding_model].fields_get()
        magic_fields = self.backend_id.get_magic_fields()
        field_list, with_company_id, maps = self.priority_fields(vals, struct)
        if (
            self.search_with_company
            and not with_company_id
            and binding_model not in MODEL_LAZY_COMPANY
        ):
            vals["company_id"] = ctx["company_id"]
        if model_spec in ("invoice", "delivery"):
            vals["type"] = model_spec
        incomplete_record = False
        for ext_ref in field_list:
            field = maps[ext_ref]
            mapper = field["id"]
            loc_name = field["loc_name"]
            ext_name = field["ext_name"]
            loc_ext_id = self.get_loc_ext_id()
            ftype = field["type"] if loc_name in struct else ""
            if ext_name == self.counterpart_pk:
                vals[loc_ext_id] = self.get_offset_value(
                    IrModel.cast_type(vals[ext_ref], binding_model, ftype),
                    model_spec=model_spec,
                )
                del vals[ext_ref]
                continue
            elif (
                not loc_name
                or loc_name in Cache.SUPERMAGIC_COLUMNS
                or loc_name in magic_fields
            ):
                del vals[ext_ref]
                continue
            if ftype:
                vals[ext_ref] = IrModel.cast_type(vals[ext_ref], binding_model, ftype)
            if field["apply4"]:
                vals = mapper.do_apply(vals, field, ext_ref, ctx=ctx)
            if (
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

    @api.model
    def compile_required_fields(self, vals, ctx=None):
        self.ensure_one()
        record = self.new(values=vals)
        struct = self.env[self._name].fields_get()
        for loc_name in struct.keys():
            if (
                    (loc_name in vals and vals[loc_name])
                    or not hasattr(record, loc_name)
                    or not getattr(record, loc_name)
            ):
                continue
            if struct[loc_name]["type"] == "many2many":
                vals[loc_name] = [x.id for x in getattr(record, loc_name)]
            elif struct[loc_name]["type"] == "many2one":
                vals[loc_name] = getattr(record, loc_name).id
            else:
                vals[loc_name] = getattr(record, loc_name)
        required_fields = [x for x in self.field_ids
                           if x.required and not x.fields_id[0].related]
        IrApply = self.env["synchro.apply"]
        for mapper in required_fields:
            if mapper.name not in vals:
                for fct in mapper.default.split(","):
                    if "()" not in fct:
                        vals[mapper.name] = fct
                    else:
                        fct = "apply_" + fct.replace("()", "")
                        if hasattr(IrApply, fct):
                            vals = getattr(IrApply, fct)(
                                mapper,
                                vals,
                                mapper.name,
                                mapper.name,
                                ctx=ctx,
                            )
        magic_fields = self.backend_id.get_magic_fields()
        for loc_name, value in vals.copy().items():
            if value is None or loc_name in magic_fields and not vals[loc_name]:
                del vals[loc_name]
        return vals

    def build_dir_mapper(
        self, backend, ext_model=None, model=None, model_spec=None, force=False
    ):
        Cache = self.env["synchro.cache"]
        Mapper = self.env["synchro.mapper"]
        SynchroApi = self.env["synchro.api"]

        magic_fields = backend.get_magic_fields()
        if (
            len(self) == 1
            and model == self.name
            and ext_model == self.counterpart_name
            and (
                model_spec == self.model_spec
                or (not model_spec and not self.model_spec)
            )
        ):
            dir_mapper = self
        else:
            dir_mapper = backend.get_dir_mapper(
                model=model, ext_model=ext_model, spec=model_spec
            )
            if not dir_mapper:
                if not force:
                    raise UserError(
                        _("Missed mapping model %s / %s" % (model, ext_model))
                    )
                if model:
                    binding_model, spec = self.split_binding_model_n_spec(model)
                    model_spec = model_spec or spec
                    if not ext_model and backend.identity_id.code in ("odoo",
                                                                      "openerp"):
                        ext_model = SynchroApi.odoo_tnl_local_model_to_ext(
                            backend, binding_model
                        )
                else:
                    binding_model = SynchroApi.odoo_tnl_ext_model_to_local(
                        backend, ext_model
                    )
                if binding_model not in self.env or not Cache.is_manageable(
                    binding_model
                ):
                    return False  # pragma: no cover
                vals = {
                    "backend_id": backend.id,
                    "name": binding_model,
                    "counterpart_name": ext_model or False,
                    "model_spec": model_spec if model_spec is not None else False,
                    "sequence": max([x.sequence for x in backend.search([])] or 15) + 1,
                    "auth_action": (
                        "sync" if Cache.only_to_map(binding_model) else "all"
                    ),
                    "use_remote_xref": {
                        "ir.model.data": "no",
                        "ir.module.module": "no",
                        "uom.uom": "yes",
                        "uom.category": "yes",
                        "res.country": "no",
                        "res.currency": "no",
                        "res.currency.rate": "no",
                        "res.groups": "yes",
                        "res.lang": "no",
                    }.get(
                        binding_model,
                        "auto" if binding_model.startswith(("ir.", "res.", "product"))
                        else "no",
                    ),
                }
                try:
                    dir_mapper = self.create(vals)
                except BaseException as e:  # pragma: no cover
                    self.env.cr.rollback()  # pylint: disable=invalid-commit
                    self.env["synchro.log"].logmsg(
                        "error",
                        "!%(E)s! ERROR %(e)s: %(model)s.create(%(vals)s)",
                        res_model=self._name,
                        values=vals,
                        errmsg=e,
                        errcode=-1,
                    )
                    return False

        binding_model = dir_mapper.name
        loc_ext_id = dir_mapper.get_loc_ext_id()
        struct = self.env[binding_model].fields_get()
        session = backend.get_session()
        field_list = self.env["synchro.api"].get_field_list(
            session, backend, binding_model, magic_fields=magic_fields
        )
        for loc_name, ext_name in field_list:
            Mapper.build_mapper(
                dir_mapper,
                loc_name,
                ext_name,
                spec=False,
                force=force
                or (loc_name == loc_ext_id)
                or struct.get(loc_name, []).get("required"),
            )
        return dir_mapper

    @api.multi
    def analyze_dir_mapper(self, managed_models):
        def is_classified(name):
            return name in unique_fields + candidate_fields + ancillary_fields

        def ignore_field(model, name):
            return (
                name in ("parent_id", "sequence")
                and model in ("res.company", "res.partner.bank")
            ) or (name in ("credit", "debit") and model.startswith("res.partner"))

        def actual_name(name):
            return name[1:] if name.startswith(("+", "!", "%", "_", "-")) else name

        self.ensure_one()
        magic_fields = self.backend_id.get_magic_fields()
        binding_model = self.name
        if binding_model not in self.env:  # pragma: no cover
            if self.auth_action != "lock":
                self.auth_action = "lock"
            return
        elif self.auth_action == "lock":  # pragma: no cover
            self.auth_action = "all"
        struct = self.env[binding_model].fields_get()

        if self.auth_action not in ("lock", "sync", "upd"):
            missed_fields = list(
                set([k for k, v in struct.items()
                     if v.get("required") and not v.get("related")])
                - {x.name for x in self.field_ids
                   if x.default or x.apply4 or x.name in (self.parent_name,
                                                          self.childs_name)}
            )
            if missed_fields:
                raise UserError(
                    _(
                        "Missed mapping for field %s of %s"
                        % (missed_fields, binding_model)
                    )
                )
        for mapper in self.field_ids:
            if (
                not mapper.name
                or not mapper.counterpart_name
                or struct.get(mapper.name, {}).get("type") in ("one2many", "many2many")
            ):
                continue
            comodel = struct.get(mapper.name, {}).get("relation")
            if comodel and comodel not in managed_models:
                mapper.write({"name": False})

        child_models = []
        if binding_model == "product.template":
            child_models = ["product.product"]
        else:
            for suffix in (".line", ".rate", ".state", ".tax"):
                child_models.append(binding_model + suffix)
        for mapper in self.field_ids:
            if (
                mapper.name in struct
                and struct.get(mapper.name, {}).get("type") == "one2many"
                and struct.get(mapper.name, {}).get("relation") in child_models
            ):
                self.childs_name = mapper.name
                break

        if binding_model == "product.product":
            parent_model = "product.template"
        else:
            parent_model = binding_model.rsplit(".", 1)[0]
        if parent_model in self.env:
            for mapper in self.field_ids:
                if (
                    mapper.name in struct
                    and struct.get(mapper.name, {}).get("type") == "many2one"
                    and struct.get(mapper.name, {}).get("relation") == parent_model
                ):
                    self.parent_name = mapper.name
                    break
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
            else self.query_index_fields(binding_model, unique=True)
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
        for keys in DEF_SKEYS.get(binding_model, []):
            if keys not in skeys:
                skeys.append(keys)
        if binding_model == "res.users":
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
                if ignore_field(binding_model, loc_name):
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
                    if ignore_field(binding_model, loc_name):
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
        for mapper in self.field_ids:
            if mapper.name in required_ancillary and not mapper.required:
                mapper.write({"required": True})
        for loc_name in unique_fields:
            skeys.append(_c(["+" + loc_name]) + ancillary_fields)
        name4key = []
        for loc_name in candidate_fields:
            if loc_name == "code" and "default_code" in name4key:
                continue
            if loc_name == "vat" and binding_model == "res.users":
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
            if binding_model != "res.users":
                keys += ancillary_fields
            if keys not in skeys:
                skeys.append(keys)
        if "code" in name4key and ancillary_fields and not self.parent_name:
            skeys.append(["+code"])
        if binding_model == "account.tax":  # pragma: no cover
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
        for mapper in self.field_ids:
            if mapper.name in unique_fields:
                vals = {"search_role": "unique"}
            elif mapper.name in candidate_fields:
                vals = {"search_role": "candidate"}
            elif mapper.name in ancillary_fields:
                vals = {"search_role": "ancillary"}
            else:
                vals = {}
            if mapper.name == uname:
                vals["required"] = True
            if vals:
                mapper.write(vals)
        self.field_uname = uname
        self.search_keys = unicodes(str(skeys))
        if "company_id" in struct and binding_model != "res.users":
            self.search_with_company = True
        else:
            self.search_with_company = False

    def get_counterpart_response(self, ext_id=False, mode=None):
        """Get data from counterpart"""
        Cache = self.env["synchro.cache"]
        SynchroLog = self.env["synchro.log"]
        backend = self.backend_id
        vmodel = self.name
        if backend.state not in ("ready", "run"):  # pragma: no cover
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
        except BaseException:  # pragma: no cover
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

    def atomic_search(self, Binder, domain, company_id=None, company_lev=0):
        if not domain:
            return []
        if company_id is None:
            full_domain = domain
        elif company_lev == 0:
            full_domain = domain + [("company_id", "=", company_id)]
        elif company_lev == 1:
            full_domain = domain + [("company_id", "=", False)]
        else:
            full_domain = domain + [
                "|",
                ("company_id", "=", company_id),
                ("company_id", "=", False),
            ]
        try:
            if hasattr(Binder, "sequence"):
                rec = Binder.search(
                    full_domain, order="sequence,id", limit=2 if company_lev < 2 else 16
                )
            else:
                rec = Binder.search(full_domain, limit=2 if company_lev < 2 else 16)
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR %(e)s: %(model)s.atomic_search(%(domain)s)",
                res_model=Binder._name,
                errmsg=e,
                ctx={"domain": domain},
            )
            return []
        if len(rec) != 1 and company_id is not None and not company_lev < 2:
            return self.atomic_search(
                Binder,
                domain,
                company_id=company_id,
                company_lev=company_lev + 1 if company_lev else company_lev + 2,
            )
        self.env["synchro.log"].logmsg(
            "debug",
            "%(model)s.atomic_search(%(domain)s)",
            res_rec=rec,
            res_model=Binder._name,
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

    def browse_from_id_in_vals(self, Binder, vals):
        id = 0
        rec = False
        if "id" in vals:
            id = vals.pop("id")
            if isinstance(id, str):  # pragma: no cover
                rec = self.xmlid_to_object(id, raise_if_not_found=False)
            else:
                recs = Binder.search([("id", "=", id)])
                if recs:
                    rec = recs[0]
                    self.env["synchro.log"].logmsg(
                        "debug",
                        "Found record %(model)s[%(id)s]",
                        res_rec=rec,
                    )
        if id and not rec:
            self.env["synchro.log"].logmsg(
                "error",
                "Record %(model)s[%(id)s] not found!",
                res_model=Binder._name,
                res_id=id,
            )
        return rec

    def browse_from_ext_id_in_vals(self, dir_mapper, Binder, vals):
        # External "id" became loc_ext_id after mapping to internal
        loc_ext_id = dir_mapper.get_loc_ext_id()
        rec = False
        if loc_ext_id in vals:
            ext_id = vals[loc_ext_id]
            recs = Binder.bind_external_ref(loc_ext_id, ext_id)
            if recs:
                rec = recs[0]
                self.env["synchro.log"].logmsg(
                    "debug",
                    "Found record %(model)s[%(id)s](ext_id=%(ext_id)s)",
                    res_rec=rec,
                    ctx={"ext_id": ext_id},
                )
        return rec

    def browse_from_ext_xmlref(self, dir_mapper, Binder, vals):
        # External "id" became loc_ext_id after mapping to internal
        SynchroApi = self.env["synchro.api"]
        backend = dir_mapper.backend_id
        loc_ext_id = dir_mapper.get_loc_ext_id()
        rec = None
        if backend.identity_id.code in ("odoo", "openerp") and (
            dir_mapper.use_remote_xref == "yes"
            or (
                dir_mapper.use_remote_xref == "auto"
                and vals.get(loc_ext_id)
                and vals[loc_ext_id] < 100
            )
        ):
            xref = SynchroApi.get_ext_xref_from_ext_id(
                backend.get_session(), dir_mapper, vals[loc_ext_id]
            )
            if xref:
                xref = SynchroApi.odoo_tnl_xref_from_ext_to_loc(
                    backend,
                    xref,
                )
                rec = self.env["ir.model.data"].xmlid_to_object(
                    xref, raise_if_not_found=False
                )
                if rec:
                    self.env["synchro.log"].logmsg(
                        "debug",
                        "Found record %(model)s[%(x)s]",
                        res_rec=rec,
                        ctx={"x": xref},
                    )
        return rec

    def bind_record(self, Binder, vals, model_spec=None, ctx=None):
        rec = self.browse_from_id_in_vals(Binder, vals)
        if rec:
            return rec
        rec = self.browse_from_ext_id_in_vals(self, Binder, vals)
        if rec:
            return rec
        rec = self.browse_from_ext_xmlref(self, Binder, vals)
        if rec:
            return rec
        ctx = ctx or {}
        loc_ext_id = self.get_loc_ext_id()
        candidate = None
        if self.name == "res.company":
            rec = Binder.search(["|", (loc_ext_id, "=", False), (loc_ext_id, "=", 0)])
            if len(rec) == 1:
                candidate = rec[0]
                rec = []
        prio = 8
        for keys in unicodes(eval(self.search_keys)):
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
                    else:
                        domain = []
                        break
                elif (
                    isinstance(vals[key], str)
                    and vals[key] == ""
                    and ilike == "?"
                ):
                    domain.append("|")
                    domain.append((key, "=", False))
                    domain.append((key, "=", ""))
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
                if model_spec in ("invoice", "delivery"):
                    domain.append(("type", "=", model_spec))
                if loc_ext_id in vals:
                    domain.append("|")
                    domain.append((loc_ext_id, "=", False))
                    domain.append((loc_ext_id, "=", 0))
                company_id = None
                if self.search_with_company:
                    if vals.get("company_id"):
                        company_id = vals["company_id"]
                    elif ctx.get("company_id"):
                        company_id = ctx["company_id"]
                    elif self.name not in MODEL_LAZY_COMPANY:
                        company_id = False
                rec = self.exec_search(Binder, domain, company_id=company_id)
                if len(rec) == 1:
                    break
                elif 1 < len(rec) < prio:
                    candidate = rec[0]
                    rec = []
                    prio = len(rec)
                else:
                    rec = []
        if rec:
            loc_name = {
                "res.company": "company_id",
                "res.country": "country_id",
                "res.currency": "currency_id",
            }.get(rec._name)
            if loc_name:
                ctx[loc_name] = rec.id
        if not rec and candidate:
            rec = candidate
        return rec

    @api.model
    def get_odoo_model_id(self):
        models = self.env["ir.model"].search([("model", "=", self.name)])
        if not models:
            return False
        return models[0].id

    @api.model
    def create(self, vals):
        self.env["synchro.cache"].clean_cache()
        model = super().create(vals)
        if not model.model_id:
            model.write({"model_id": model.get_odoo_model_id()})
        return model

    @api.multi
    def write(self, vals):
        self.env["synchro.cache"].clean_cache()
        res = super().write(vals)
        if "model_id" not in vals:
            for model in self:
                if not model.model_id:
                    model.write({"model_id": model.get_odoo_model_id()})
        return res
