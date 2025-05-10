#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import _, api, fields, models
from odoo.exceptions import UserError

from python_plus import str2bool


class SynchroMapper(models.Model):
    _name = "synchro.mapper"
    _description = "Field mapping for Synchronization"
    _order = "sequence, name"

    _sql_constraints = [
        (
            "field_uniq",
            "unique (model_id,name,spec,counterpart_name)",
            "Local field name, spec and counterpart name must be unique per model!",
        )
    ]
    fields_id = fields.Many2one("ir.model.fields", string="Odoo field name")
    name = fields.Char("Odoo field name")
    counterpart_name = fields.Char("Counterpart field name")
    apply4 = fields.Char(
        string="Apply function from counterpart value",
        help="Declare 1+ functions, comma separated, to apply on counterpart value\n"
        "Function names are in format 'name()'.\n"
        "Some available functions are:\n"
        "vat(), upper(), lower(), street_number(), bool()\n"
        "person(), journal(), account(), uom(), tax()\n",
        default="",
    )
    default = fields.Char(
        string="Default value",
        help="Default value or function to apply for default value.\n"
        "To declare function set name ending with '()'\n"
        "i.e. 'foo' means value 'foo'\n"
        "'foo()' means function foo() to set default\n",
        default="",
    )
    spec = fields.Selection(
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
    protect_update = fields.Selection(
        [
            ("0", "Always Update"),
            ("1", "But new value not empty"),
            ("2", "But current value is empty"),
            ("3", "Protected field"),
            ("4", "Max counter"),
        ],
        string="Protect against update",
        default="0",
    )
    required = fields.Boolean("Required field", default=False)
    search_role = fields.Selection(
        [
            ("unique", "Field with unique index"),
            ("candidate", "Search keys candidate"),
            ("ancillary", "Ancillary search keys"),
        ],
        string="Role in search keys",
    )
    model_id = fields.Many2one("synchro.model")
    model_counterpart_name = fields.Char(
        "Counterpart Model Name", store=True, related="model_id.counterpart_name"
    )
    backend_id = fields.Many2one(
        "synchro.backend",
        related="model_id.backend_id",
        store=True,
        string="Backend",
    )
    ttype = fields.Selection(
        string="Odoo type", store=True, related="fields_id.ttype"
    )
    sequence = fields.Integer("Priority", default=16)

    def get_loc_fname(self, fct):
        return "apply_%s" % fct[:-2]

    def get_default_protection(
        self, fix_protect_update=None, fix_required=None, magic_fields=None
    ):
        Cache = self.env["synchro.cache"]
        magic_fields = magic_fields or []
        loc_name = self.name
        binding_model = self.model_id.split_binding_model_n_spec(self.model_id.name)[0]
        struct = self.env[binding_model].fields_get()
        field_def = Cache.TABLE_DEF.get(binding_model, {}).get(loc_name, {})
        global_def = Cache.TABLE_DEF.get("base", {}).get(loc_name, {})
        if not Cache.is_manageable(binding_model) or not loc_name:
            # Field protect because model is not managed
            protect_update = "3"
        elif loc_name not in struct:
            raise UserError(
                _("Field %s does not exist in %s!" % (loc_name, binding_model))
            )
        elif loc_name in (self.model_id.parent_name, self.model_id.get_loc_ext_id()):
            # External ID must be always updatable
            protect_update = "0"
        elif self.model_id.auth_action == "sync" or loc_name in magic_fields:
            # Avoid update for only synchronized models
            protect_update = "3"
        elif loc_name != self.model_id.childs_name and struct[loc_name]["type"] in (
                "one2many", "many2many"):
            # Avoid propagation for smart links, like orders in res.partner
            protect_update = "3"
        else:
            # Evaluate default protection pattern
            protect_update = str(
                field_def.get(
                    "protect_update",
                    global_def.get(
                        "protect_update",
                        3 if struct[loc_name].get("readonly", False) else 0,
                    ),
                )
            )

        # if loc_name in (self.model_id.parent_name, self.model_id.get_loc_ext_id()):
        #     # External ID is mandatory
        #     required = True
        if not loc_name or loc_name in magic_fields:
            required = False
        else:
            required = field_def.get(
                "required",
                global_def.get("required", struct[loc_name].get("required", False)),
            )

        return (
            fix_protect_update if fix_protect_update is not None else protect_update,
            fix_required if fix_required is not None else required,
        )

    def get_default_apply(self, magic_fields=None):
        def append_fct(fct):
            if fct and fct not in apply4:
                apply4.append(fct)

        def append_def(fct):
            if (not default or "()" in default[0]) and fct and fct not in default:
                default.append(fct)

        Cache = self.env["synchro.cache"]
        magic_fields = magic_fields or []
        loc_name = self.name
        binding_model = self.model_id.split_binding_model_n_spec(self.model_id.name)[0]
        struct = self.env[binding_model].fields_get()
        field_def = Cache.TABLE_DEF.get(binding_model, {}).get(loc_name, {})
        global_def = Cache.TABLE_DEF.get("base", {}).get(loc_name, {})
        apply4 = self.apply4 or ""
        default = self.default or ""
        if not Cache.is_manageable(binding_model) or not loc_name:
            pass
        elif loc_name not in struct:
            raise UserError(
                _("Field %s does not exist in %s!" % (loc_name, binding_model))
            )
        elif loc_name in (self.model_id.parent_name,
                          self.model_id.get_loc_ext_id()) or loc_name in magic_fields:
            apply4 = default = ""
        elif self.model_id.auth_action == "sync":
            default = ""
        else:
            def_apply = field_def.get("apply", global_def.get("apply", ""))
            def_value = field_def.get("default", global_def.get("default", ""))
            if def_apply and "()" not in def_apply:
                raise UserError(
                    _("Interal error: apply %s for field %s.%s is not a function!"
                      % (def_apply, binding_model, loc_name))
                )
            apply4 = [x.strip() for x in apply4.split(",") if x]
            default = [x.strip() for x in default.split(",") if x]
            if (
                    self.backend_id.identity_id.code in ("odoo", "openerp")
                    and loc_name not in magic_fields
                    and struct[loc_name]["type"] not in ("many2one",
                                                         "one2many",
                                                         "many2many"
                                                         "date",
                                                         "datetime",
                                                         "boolean",
                                                         "binary")
            ):
                append_fct("odoo_migrate()")
            for fct in def_apply.split(","):
                append_fct(fct)
            for fct in def_value.split(","):
                append_def(fct)
            fct = "sanitize_" + loc_name
            if hasattr(self.env["synchro.apply"], self.get_loc_fname(fct)):
                append_fct(fct + "()")
            fct = "default_" + loc_name
            if hasattr(self.env["synchro.apply"], self.get_loc_fname(fct)):
                append_def(fct + "()")
            if struct[loc_name].get("required"):
                fct = {
                    "char": "set_tmp_name()",
                    "bool": "bool()",
                    "integer": "integer()",
                    "float": "float()",
                    "monetary": "float()",
                    "datetime": "now()",
                    "date": "today()",
                    "many2one": "property()",
                    "selection": "selection()",
                }.get(struct[loc_name]["type"])
                if fct:
                    append_def(fct)
            if struct[loc_name].get("relation") and (
                struct[loc_name]["relation"] != "res.company"
                or binding_model != "res.users"
            ):
                fct = {
                    "res.company": "get_global()",
                    "res.country": "get_global()",
                }.get(struct[loc_name]["relation"])
                if fct:
                    append_def(fct)
            if loc_name == "type" and binding_model == "account.account.type":
                append_def("oe_account_account_type_nam()")
            elif (
                    loc_name == "product_variant_ids"
                    and binding_model == "product.template"
            ):
                append_def("none()")
            for fct in apply4:
                if not hasattr(self.env["synchro.apply"], self.get_loc_fname(fct)):
                    self.env["synchro.log"].logmsg(
                        "error",
                        "Function %(f)s not found for field %(model)s.%(name)s",
                        res_model=binding_model,
                        ctx={"f": fct, "name": loc_name},
                    )
            apply4 = ",".join(apply4)
            for fct in default:
                if "()" in fct and not hasattr(self.env["synchro.apply"],
                                               self.get_loc_fname(fct)):
                    self.env["synchro.log"].logmsg(
                        "error",
                        "Function %(f)s not found for field %(model)s.%(name)s",
                        res_model=binding_model,
                        ctx={"f": fct, "name": loc_name},
                    )
            default = ",".join(default)
        return apply4, default

    def get_default_priority(self, magic_fields=None, apply=None):
        binding_model = self.model_id.split_binding_model_n_spec(self.model_id.name)[0]
        struct = self.env[binding_model].fields_get()
        sequence = 32
        loc_name = self.name
        if apply and "()" not in apply:
            sequence = 2
        elif not loc_name or not self.counterpart_name:
            sequence = 8
        elif loc_name in ("id", self.model_id.get_loc_ext_id()):
            sequence = 4
        elif loc_name == "company_id":
            sequence = 6
        elif loc_name == "country_id":
            sequence = 10
        elif loc_name in self.env["synchro.cache"].LOG_ACCESS_COLUMNS:
            sequence = 12
        elif loc_name == self.model_id.parent_name:
            sequence = 24
        elif loc_name in magic_fields:
            sequence = 44
        elif loc_name in ("is_company", "electronic_invoice_subjected"):
            sequence = 32
        elif struct[loc_name]["type"] in ("datetime", "date"):
            sequence = 28
        elif struct[loc_name]["type"] == "many2one":
            sequence = 36
        elif struct[loc_name]["type"] in ("one2many", "many2many"):
            sequence = 40
        return sequence

    def build_mapper(
        self,
        dir_mapper,
        loc_name,
        ext_name,
        fix_protect_update=None,
        fix_required=None,
        magic_fields=None,
        spec=None,
        force=False,
    ):
        if not dir_mapper.id:
            return False
        mapper = dir_mapper.get_mapper(loc_name=loc_name, ext_name=ext_name, spec=spec)
        if not mapper:
            if not force:
                return mapper
            mapper = self.create(
                {
                    "model_id": dir_mapper.id,
                    "name": loc_name,
                    "spec": spec,
                    "counterpart_name": ext_name,
                }
            )
            force = True
        magic_fields = magic_fields or []
        if force:
            protect_update, required = mapper.get_default_protection(
                fix_protect_update=fix_protect_update,
                fix_required=fix_required,
                magic_fields=magic_fields,
            )
            apply4, default = mapper.get_default_apply(magic_fields=magic_fields)
            sequence = mapper.get_default_priority(
                magic_fields=magic_fields, apply=apply4
            )
            mapper.write(
                {
                    "protect_update": protect_update,
                    "required": required,
                    "apply4": apply4,
                    "default": default,
                    "sequence": sequence,
                }
            )
        return mapper

    @api.model
    def extract_default_n_apply(self, ftype=None):
        if len(self) != 1:
            return True if ftype == "boolean" else "", "", ""
        default = self.apply4 or ""
        if default.endswith("()"):
            apply4 = [self.get_loc_fname(fct) for fct in default.split(",")]
            default = False
        elif default:
            apply4 = ["apply_set_value"]
        else:
            apply4 = ""
        if ftype == "boolean":
            default = str2bool(default, True)
        spec = self.spec
        return default, apply4, spec

    @api.model
    def do_apply(self, vals, field, ext_ref, ctx=None):
        self.ensure_one()
        IrApply = self.env["synchro.apply"]
        dir_mapper = self.model_id
        vmodel = dir_mapper.name
        loc_name = field["loc_name"]
        if loc_name == ext_ref or loc_name not in vals or not vals[loc_name]:
            for fct in field["apply4"]:
                if hasattr(IrApply, fct):
                    vals = getattr(IrApply, fct)(
                        self,
                        vals,
                        loc_name,
                        ext_ref,
                        default=field["default"],
                        ctx=ctx,
                    )
                else:
                    self.env["synchro.log"].logmsg(
                        "error",
                        "Function %(f)s not found for field %(model)s.%(name)s",
                        res_model=vmodel,
                        ctx={"f": fct[6:] + "()", "name": loc_name},
                    )
        return vals

    @api.model
    def get_odoo_fields_id(self):
        fields = self.env["ir.model.fields"].search(
            [("model_id", "=", self.model_id.model_id.id), ("name", "=", self.name)]
        )
        if not fields:
            return False
        return fields[0].id

    @api.model
    def create(self, vals):
        self.env["synchro.cache"].clean_cache()
        field = super().create(vals)
        if not field.fields_id:
            field.write({"fields_id": field.get_odoo_fields_id()})
        return field

    @api.multi
    def write(self, vals):
        self.env["synchro.cache"].clean_cache()
        res = super().write(vals)
        if "fields_id" not in vals:
            for field in self:
                if not field.fields_id:
                    field.write({"fields_id": field.get_odoo_fields_id()})
        return res
