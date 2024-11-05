#
# Copyright 2019-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging

from odoo import api, fields, models

from .ir_model_synchro_cache import (
    DEF_SKEYS,
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
        required=True,
        help="Sequence to use in search record when not yet synchronized\n"
        'i.e. (["name","company_id"],["name"])\n'
        "will search for record with name and company keys; if not found"
        "search for record just with name",
    )
    search_with_company = fields.Boolean("Search with company", default=False)
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
            ("All", "Everything"),
            ("Ins", "Only new records"),
            ("Upd", "Only Update"),
            ("Sync", "Only Synchronization ID"),
        ],
        string="Authorized actions",
        required=True,
        default="All",
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
            if loc_name.startswith("."):
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

    def assign_value_to_local(self, vals, field, ext_ref, ttl, only_minimal=None):
        Cache = self.env["ir.model.synchro.cache"]
        # vmodel = self.name
        # actual_model = self.get_actual_model_name(vmodel)
        # struct = self.env[actual_model].fields_get()
        loc_ext_id = field["loc_ext_id"]
        backend = self.synchro_channel_id
        loc_name = field["loc_name"]
        is_foreign = field["is_foreign"]
        ftype = field["type"]
        if field["store"]:
            if (
                ext_ref in vals
                and loc_name
                and loc_name not in vals
                and (
                    not is_foreign or ftype not in ("many2one", "one2many", "many2many")
                )
            ):
                vals[loc_name] = vals[ext_ref]
            if is_foreign and ftype == "many2one":
                comodel = field["relation"]
                if (
                    isinstance(vals[ext_ref], int)
                    and vals[ext_ref]
                    and comodel in self.env
                ):
                    rec = self.env[comodel].bind_external_ref(loc_ext_id, vals[ext_ref])
                    if rec:
                        vals[loc_name] = rec.id
                    elif self.name not in ("res.partner", "res.users"):
                        Cache.que_priority_push(
                            backend, "trigger", comodel, vals[ext_ref], ttl
                        )
                elif loc_name == "company_id":
                    vals[loc_name] = backend.company_id.id
            elif is_foreign and ftype in ("one2many", "many2many"):
                comodel = field["relation"]
                if comodel in self.env:
                    synchro_comodel = self.get_synchro_model_from_loc(backend, comodel)
                    if isinstance(vals[ext_ref], int):
                        vals[ext_ref] = [vals[ext_ref]]
                    if isinstance(vals[ext_ref], (list, tuple)):
                        for item in vals[ext_ref]:
                            rec = self.env[comodel].bind_external_ref(loc_ext_id, item)
                            if not rec:
                                if loc_name == self.childs_name:
                                    Cache.que_priority_push(
                                        backend,
                                        "trigger",
                                        synchro_comodel.counterpart_name,
                                        item,
                                        ttl,
                                    )
                                else:
                                    Cache.que_push(
                                        backend,
                                        "trigger",
                                        synchro_comodel.counterpart_name,
                                        item,
                                        ttl,
                                    )
                        if loc_name in vals:
                            del vals[loc_name]
            elif loc_name in vals and ftype == "selection" and vals[loc_name]:
                if loc_name in ("lang", "lang_id"):
                    comodel = "res.lang"
                    rec = self.env[comodel].search([("code", "=", vals[loc_name])])
                    if not rec:
                        Cache.que_priority_push(
                            backend, "synchro", comodel, {"code": vals[ext_ref]}, ttl
                        )
                valid = False
                for item in field["selection"]:
                    if (
                        isinstance(item, (list, tuple)) and vals[loc_name] == item[0]
                    ) or (
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
        if ext_ref in vals and loc_name != ext_ref:
            del vals[ext_ref]
        return vals

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
        only_internal = True
        for ext_ref in field_list:
            field = self.synchro_field_from_ext_ref(ext_ref, struct, spec=spec)
            loc_name = field["loc_name"]
            ext_name = field["ext_name"]
            ftype = field["type"]
            fields[ext_ref] = field
            if loc_name != ext_name:
                only_internal = False
            if loc_name in (loc_ext_id, "id"):
                list_1.append(ext_ref)
            elif loc_name in ("country_id", "company_id"):
                list_2.append(ext_ref)
            elif loc_name in ("partner_id", "street"):  # Why street?
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
            only_internal,
            fields,
        )

    @api.model
    def map_to_internal(
        self,
        vals,
        ttl,
        only_minimal=None,
        spec=None,
    ):
        self.ensure_one()
        Cache = self.env["ir.model.synchro.cache"]
        IrModel = self.env["ir.model.synchro"]
        vmodel = self.name
        actual_model = self.get_actual_model_name(vmodel)
        struct = self.env[actual_model].fields_get()
        field_list, only_internal, fields = self.priority_fields(
            vals, struct, spec=spec
        )
        backend = self.synchro_channel_id
        loc_ext_id = self.get_loc_ext_id()
        for ext_ref in field_list:
            field = fields[ext_ref]
            synchro_field = field["id"]
            loc_name = field["loc_name"]
            ext_name = field["ext_name"]
            apply4 = field["apply4"]
            is_foreign = field["is_foreign"]
            if (
                not loc_name and not synchro_field
            ) or loc_name in Cache.SUPERMAGIC_COLUMNS:
                del vals[ext_ref]
                continue
            vals[ext_ref] = IrModel.cast_type(
                vals[ext_ref], actual_model, field["type"]
            )
            if (
                not loc_name
                or (isinstance(vals[ext_ref], str) and not vals[ext_ref].strip())
                or not vals[ext_ref]
            ):
                if is_foreign and apply4:
                    vals = synchro_field.do_apply(
                        vals,
                        field,
                        ext_ref,
                        vmodel,
                    )
                vals = self.assign_value_to_local(
                    vals, field, ext_ref, ttl, only_minimal=only_minimal
                )
                continue
            elif is_foreign:
                # Field like <vg7_id> with external ID in local DB
                if loc_name == loc_ext_id:
                    vals[ext_ref] = IrModel.get_offset_value(
                        backend, vmodel, vals[ext_ref]
                    )
                    vals = self.assign_value_to_local(
                        vals,
                        field,
                        ext_ref,
                        ttl,
                        only_minimal=only_minimal,
                    )
                    continue
                elif loc_name in vals or loc_name == "id":
                    # If counterpart partner supplies both
                    # local and external values, just process local value
                    del vals[ext_ref]
                    continue
                elif ext_name == self.counterpart_pk:
                    # Field like vg7:id
                    continue
                else:
                    if apply4:
                        vals = synchro_field.do_apply(
                            vals,
                            field,
                            ext_ref,
                            vmodel,
                        )
                    vals = self.assign_value_to_local(
                        vals,
                        field,
                        ext_ref,
                        ttl,
                        only_minimal=only_minimal,
                    )
            elif (
                isinstance(vals[ext_ref], str)
                and struct[loc_name]["type"] == "many2one"
                and "." in vals[ext_ref]
                and " " not in vals[ext_ref]
            ):
                rec = self.xmlid_to_object(vals[ext_ref], raise_if_not_found=False)
                if rec:
                    vals[loc_name] = rec.id
                vals = self.assign_value_to_local(
                    vals, field, ext_ref, ttl, only_minimal=only_minimal
                )
            else:
                vals = self.assign_value_to_local(
                    vals, field, ext_ref, ttl, only_minimal=only_minimal
                )
        min_vals = {}
        if self.auth_action == "Sync":
            if loc_ext_id in vals:
                min_vals[loc_ext_id] = vals[loc_ext_id]
        else:
            for loc_name in vals.keys():
                synchro_field = self.env[
                    "synchro.channel.model.field"
                ].get_synchro_field(self, loc_name=loc_name)
                if synchro_field.required:
                    min_vals[loc_name] = vals[loc_name]
        return vals, min_vals

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
                # "field_uname": field_uname,
                "search_keys": "[]",
                "sequence": 16,
                "auth_action": "Sync" if actual_model == "res.groups" else "All",
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
            if not SynchroModelField.build_odoo_synchro_model_field(
                synchro_model,
                loc_name,
                ext_name,
                fix_protect_update="3" if loc_name in magic_fields else None,
                fix_required=False if loc_name in magic_fields else None,
            ):
                return False
        return synchro_model

    @api.multi
    def analyze_synchro_model(self):
        self.ensure_one()
        actual_model = self.name
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

        skeys = DEF_SKEYS.get(actual_model, [])
        if skeys or actual_model == "res.users":
            ancillary = []
        else:
            ancillary = [self.parent_name] if self.parent_name else []
            for loc_name in ANCILLARY_KEYS:
                if (
                    loc_name in ("parent_id", "sequence")
                    and actual_model == "res.company"
                ):
                    continue
                if loc_name != self.parent_name and loc_name in struct:
                    ancillary.append(loc_name)
            if len(ancillary) > 2:
                for loc_name in (
                    "is_company",
                    "left_id",
                    "right_id",
                    "sequence",
                ):
                    if len(ancillary) > 2 and loc_name in ancillary:
                        del ancillary[ancillary.index(loc_name)]
            if self.parent_name:
                for loc_name in ANCILLARY_LINE_KEYS:
                    if loc_name not in ancillary and loc_name in struct:
                        ancillary.append(loc_name)
        if skeys:
            uname = skeys[0][0]
        else:
            primary_keys = []
            for loc_name in CANDIDATE_KEYS:
                if loc_name in struct:
                    # if loc_name in ("description", "comment") and primary_keys:
                    #     continue
                    if loc_name == "name" and actual_model == "account.tax":
                        primary_keys.append("description")
                    if loc_name == "code" and "default_code" in primary_keys:
                        continue
                    if loc_name == "vat" and actual_model == "res.users":
                        continue
                    if len(primary_keys) < 2 or loc_name == "name":
                        primary_keys.append(loc_name)
            if len(primary_keys) > 1:
                skeys.append(primary_keys + ancillary)
                if "name" in primary_keys and ancillary:
                    if len(primary_keys) > 2:
                        skeys.append(
                            [
                                "+" + x if i == 0 else "?" + x if x != "name" else x
                                for (i, x) in enumerate(primary_keys)
                            ]
                            + ancillary
                        )
                    skeys.append(
                        ["%" + x if x == "name" else x for x in primary_keys]
                        + ancillary
                    )
                    skeys.append(
                        ["+" + x for x in primary_keys if x != "name"] + ancillary
                    )
                    skeys.append(
                        ["!" + x if x != "name" else x for x in primary_keys]
                        + ancillary
                    )
            uname = primary_keys[0]
            for loc_name in primary_keys:
                keys = ["+" + loc_name]
                if actual_model != "res.users":
                    keys += ancillary
                if keys not in skeys:
                    skeys.append(keys)
            if "code" in primary_keys and ancillary and not self.parent_name:
                skeys.append(["+code"])
            if "name" in primary_keys and ancillary and not self.parent_name:
                skeys.append(["+name"])
        required_fields = [x for x in self.field_ids if x.required]
        if not required_fields:
            for synchro_field in self.field_ids:
                if synchro_field.name == uname:
                    synchro_field.write({"required": True})
                    break
        self.field_uname = uname
        self.search_keys = str(skeys)
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
        Cache.open(backend=backend, model=vmodel)
        session = backend.get_session()
        return self.env["synchro.api"].get_response(session, self, ext_id=ext_id)

    @api.multi
    def write(self, vals):
        self.env["ir.model.synchro.cache"].clean_cache()
        return super().write(vals)
