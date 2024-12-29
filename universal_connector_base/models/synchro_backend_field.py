#
# Copyright 2018-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging
from odoo import _, api, fields, models
from odoo.exceptions import UserError

from python_plus import str2bool

_logger = logging.getLogger(__name__)


class SynchroChannelModelFields(models.Model):
    _name = "synchro.channel.model.field"
    _description = "Field mapping for Synchronization"
    _order = "name"

    _sql_constraints = [
        (
            "field_uniq",
            "unique (model_id,name,spec,counterpart_name)",
            "Local field name, spec and counterpart name must be unique per model!",
        )
    ]

    name = fields.Char("Odoo field name")
    counterpart_name = fields.Char("Counterpart field name")
    apply = fields.Char(
        string="Function to apply for supply value or default value.",
        help='Function are in format "name()".\n'
        "Some avaiable functions are:\n"
        "vat(), upper(), lower(), street_number(), bool()\n"
        "person(), journal(), account(), uom(), tax()\n",
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
            ("ancillary", "Ancillary search file"),
        ],
        string="Role in search keys",
    )
    model_id = fields.Many2one("synchro.channel.model")
    model_counterpart_name = fields.Char(
        "Counterpart Model Name", store=True, related="model_id.counterpart_name"
    )
    backend_id = fields.Many2one(
        "synchro.channel",
        related="model_id.synchro_channel_id",
        store=True,
        string="Backend",
    )
    sequence = fields.Integer("Priority", default=16)

    def get_default_protection(
        self, fix_protect_update=None, fix_required=None, magic_fields=None
    ):
        Cache = self.env["ir.model.synchro.cache"]
        magic_fields = magic_fields or []
        loc_name = self.name
        binding_model = self.model_id.get_binding_model_name(self.model_id.name)
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

    def build_odoo_mapper(
        self,
        dir_mapper,
        loc_name,
        ext_name,
        fix_protect_update=None,
        fix_required=None,
        magic_fields=None,
        spec=None,
    ):
        if not dir_mapper.id:
            return False
        mapper = dir_mapper.get_mapper(loc_name=loc_name, ext_name=ext_name, spec=spec)
        if not mapper:
            mapper = self.create(
                {
                    "model_id": dir_mapper.id,
                    "name": loc_name,
                    "spec": spec,
                    "counterpart_name": ext_name,
                }
            )
        magic_fields = magic_fields or []
        binding_model = dir_mapper.get_binding_model_name(dir_mapper.name)
        struct = self.env[binding_model].fields_get()
        protect_update, required = mapper.get_default_protection(
            fix_protect_update=fix_protect_update,
            fix_required=fix_required,
            magic_fields=magic_fields,
        )
        apply4 = ""
        if required and struct[loc_name]["type"] == "char":
            apply4 += ",set_tmp_name()"
        if required and struct[loc_name]["type"] == "bool":
            apply4 += ",bool()"
        if struct[loc_name].get("relation") in ("res.company", "res.country"):
            apply4 += ",get_global()"
        if struct[loc_name].get("relation") in ("uom.uom",):
            apply4 += ",uom()"
        if struct[loc_name].get("relation") == "account.tax":
            apply4 += ",oe_account_tax_amount(),tax()"
        if loc_name == "type" and binding_model == "account.account.type":
            apply4 += ",oe_account_account_type_nam()"
        if loc_name == "vat":
            apply4 += ",vat()"
        if apply4.startswith(","):
            apply4 = apply4[1:]
        mapper.write(
            {
                "apply": apply4,
                "protect_update": protect_update,
                "required": required,
            }
        )
        return mapper

    @api.model
    def get_default_n_apply(self, ftype=None):
        if len(self) != 1:
            return True if ftype == "boolean" else "", "", ""
        default = self.apply or ""
        if default.endswith("()"):
            apply4 = ",".join(["apply_%s" % fct[:-2] for fct in default.split(",")])
            default = False
        elif default:
            apply4 = "apply_set_value"
        else:
            apply4 = ""
        if ftype == "boolean":
            default = str2bool(default, True)
        spec = self.spec
        return default, apply4, spec

    @api.model
    def do_apply(
        self,
        vals,
        field,
        ext_ref,
    ):
        self.ensure_one()
        IrApply = self.env["ir.model.synchro.apply"]
        Api = self.env["synchro.api"]
        dir_mapper = self.model_id
        backend = dir_mapper.synchro_channel_id
        vmodel = dir_mapper.name
        loc_name = field["loc_name"]
        for fct in field["apply4"].split(","):
            if fct == "apply_odoo_migrate":
                vals[loc_name] = Api.odoo_tnl_value_from_loc_to_ext(
                    backend, dir_mapper, vals[ext_ref], loc_name
                )
            elif hasattr(IrApply, fct):
                vals = getattr(IrApply, fct)(
                    backend,
                    vals,
                    loc_name,
                    ext_ref,
                    field["loc_ext_id"],
                    vmodel,
                    default=field["default"],
                )
        return vals

    @api.multi
    def write(self, vals):
        self.env["ir.model.synchro.cache"].clean_cache()
        return super().write(vals)
