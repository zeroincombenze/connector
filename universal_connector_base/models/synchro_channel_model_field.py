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

from python_plus import str2bool

_logger = logging.getLogger(__name__)


class SynchroChannelModelFields(models.Model):
    _name = "synchro.channel.model.field"
    _description = "Field mapping for Synchonization"
    _order = "name"

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
            ("customer", "Customer"),
            ("supplier", "Suplier"),
            ("company", "Company"),
        ],
        string="Specific search",
    )
    protect_update = fields.Selection(
        [
            ("0", "Always Update"),
            ("1", "But new value not empty"),
            ("2", "But current value is empty"),
            ("3", "Protected field"),
            ("4", "Max counter"),
        ],
        string="Protect field against update",
        default="0",
    )
    required = fields.Boolean("Required field", default=False)
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
        self, loc_name, vmodel=None, fix_protect_update=None, fix_required=None
    ):
        Cache = self.env["ir.model.synchro.cache"]
        synchro_model = self.env["synchro.channel.model"]
        vmodel = vmodel or self.model_id.name
        actual_model = synchro_model.get_actual_model_name(vmodel)
        struct = self.env[actual_model].fields_get()
        field_def = Cache.TABLE_DEF.get(actual_model, {}).get(loc_name, {})
        global_def = Cache.TABLE_DEF.get("base", {}).get(loc_name, {})
        if Cache.is_manageable(actual_model):
            protect_update = str(
                field_def.get(
                    "protect_update",
                    global_def.get(
                        "protect_update",
                        3 if struct[loc_name].get("readonly", False) else 0,
                    ),
                )
            )
        else:
            protect_update = "3"
        required = field_def.get(
            "required",
            global_def.get("required", struct[loc_name].get("required", False)),
        )
        return (
            fix_protect_update or protect_update,
            fix_required if fix_required is not None else required,
        )

    def build_odoo_synchro_model_field(
        self,
        synchro_model,
        loc_name,
        ext_name,
        fix_protect_update=None,
        fix_required=None,
    ):
        if not synchro_model.id:
            return False
        res = self.search(
            [
                ("model_id", "=", synchro_model.id),
                ("name", "=", loc_name),
                ("counterpart_name", "=", ext_name),
            ]
        )
        if res:
            return True
        if loc_name == synchro_model.parent_name:
            fix_required = True
        protect_update, required = self.get_default_protection(
            loc_name,
            vmodel=synchro_model.name,
            fix_protect_update=(
                fix_protect_update if synchro_model.auth_action != "Sync" else "3"
            ),
            fix_required=fix_required,
        )
        if loc_name == synchro_model.get_loc_ext_id():
            protect_update = "0"
        actual_model = synchro_model.get_actual_model_name(synchro_model.name)
        struct = self.env[actual_model].fields_get()
        apply4 = ""
        if required and struct[loc_name]["type"] == "char":
            apply4 += ",set_tmp_name()"
        if required and struct[loc_name]["type"] == "bool":
            apply4 += ",bool()"
        if struct[loc_name].get("relation") in ("res.company", "res.country"):
            apply4 += ",get_global()"
        if struct[loc_name].get("relation") in ("product.uom", "uom.uom"):
            apply4 += ",uom()"
        if struct[loc_name].get("relation") == "account.tax":
            apply4 += ",oe_account_tax_amount(),tax()"
        if loc_name == "type" and actual_model == "account.account.type":
            apply4 += ",oe_account_account_type_nam()"
        if loc_name == "vat":
            apply4 += ",vat()"
        if apply4.startswith(","):
            apply4 = apply4[1:]
        vals = {
            "model_id": synchro_model.id,
            "name": loc_name,
            "counterpart_name": ext_name,
            "apply": apply4,
            "spec": "",
            "protect_update": protect_update,
            "required": required,
        }
        try:
            return self.create(vals)
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["ir.model.synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR %(e)s: %(model)s.create(%(vals)s)",
                res_model=synchro_model.name,
                values=vals,
                errmsg=e,
                errcode=-1,
            )
        return False

    def get_synchro_field(self, synchro_model, loc_name=None, ext_name=None, spec=None):
        domain = [
            ("model_id", "=", synchro_model.id),
        ]
        if loc_name:
            domain.append(("name", "=", loc_name))
        if ext_name:
            domain.append(("counterpart_name", "=", ext_name))
        if spec:
            domain.append(("spec", "=", spec))
        return self.search(domain)

    @api.model
    def get_default_n_apply(self, ftype=None):
        if len(self) != 1:
            return True if ftype == "boolean" else "", "", ""
        Cache = self.env["ir.model.synchro.cache"]
        synchro_model = self.model_id
        backend = synchro_model.synchro_channel_id
        vmodel = synchro_model.name
        if not Cache.get_attr(backend.id, vmodel):
            Cache.open(
                backend=backend.id,
                model=vmodel,
            )
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
        vmodel,
    ):
        self.ensure_one()
        IrApply = self.env["ir.model.synchro.apply"]
        Api = self.env["synchro.api"]
        synchro_model = self.model_id
        backend = synchro_model.synchro_channel_id
        loc_name = field["loc_name"]
        for fct in field["apply4"].split(","):
            if fct == "apply_odoo_migrate":
                vals[loc_name] = Api.odoo_tnl_value_from_to(
                    backend, synchro_model, vals[ext_ref], loc_name
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
