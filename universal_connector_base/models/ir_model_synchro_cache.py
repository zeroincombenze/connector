#
# Copyright 2018-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging
from datetime import datetime

from odoo import _, api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
try:
    from odoo_score import odoo_score
except ImportError as err:  # pragma: no cover
    _logger.error(err)


DEF_SKEYS = {
    # "res.partner": [
    #     # ["rea_office", "rea_code"],
    #     ["?vat", "name", "is_company", "type"],
    #     ["vat", "%name", "is_company", "type"],
    #     ["+vat", "is_company", "type"],
    #     ["!vat", "name", "type"],
    # ],
    # "res.company": [["vat"], ["name"], ["partner_id"]],
    # "account.account": [
    #     ["code", "company_id"],
    #     ["name", "company_id"],
    # ],
    # "account.account.type": [["type"], ["name"]],
    # "account.invoice": [["number", "company_id"], ["move_name", "company_id"]],
    # "account.invoice.line": [["invoice_id", "sequence"], ["invoice_id", "name"]],
    # "product.template": [
    #     ["name", "default_code"],
    #     ["name", "barcode"],
    #     ["name"],
    #     ["default_code"],
    #     ["barcode"],
    # ],
    # "product.product": [
    #     ["name", "default_code"],
    #     ["name", "barcode"],
    #     ["name"],
    #     ["default_code"],
    #     ["barcode"],
    # ],
    "product.supplierinfo": [["name", "product_tmpl_id", "qty"], "!"],
    "project.project": [["account_analytic_id"]],
    "sale.order": [["name"]],
    "sale.order.line": [["order_id", "sequence"], ["order_id", "name"]],
}
MODEL_LAZY_COMPANY = [
    "res.currency.rate",
    "res.partner",
    "res.users",
    "product.template",
    "product.product",
]
# MAGIC_FIELDS = {
#     "res.partner": {
#         "company_id": False,
#         "is_company": True,
#         "supplier": True,
#     },
# }
# Warning: order is very important!
CANDIDATE_KEYS = [
    "acc_number",
    "sanitized_acc_number",
    "login",
    "default_code",
    "code",
    "key",
    "number",
    "serial_number",
    "vat",
    "move_name",
    # "email",
    "name",
]
ANCILLARY_KEYS = [
    "is_company",
    "left_id",
    "parent_id",
    "right_id",
    "type",
    "type_tax_use",
]
ANCILLARY_LINE_KEYS = [
    "account_id",
    "product_id",
    "product_qty",
    "quantity",
    "product_uom_qty",
    "credit",
    "debit",
    "sequence",
]


class IrModelSynchroCache(models.Model):
    _name = "ir.model.synchro.cache"
    _description = "Internal Universal Connector cache"

    CACHE = odoo_score.SingletonCache()
    SYSTEM_MODEL_ROOT = [
        "base.config.",
        "base_import.",
        "base.language.",
        "base.module.",
        "base.setup.",
        "base.update.",
        "ir.actions.",
        "ir.exports.",
        "ir.model.",
        "ir.module.",
        "ir.qweb.",
        "ir.ui.",
        "report.",
        "res.config.",
        "web_editor.",
        "web_tour.",
        "workflow.",
    ]
    SYSTEM_MODELS = [
        "_unknown",
        "base",
        "base.config.settings",
        "base_import",
        "change.password.wizard",
        # "ir.actions.actions",
        # "ir.actions.act_window",
        # "ir.actions.act_window.view",
        # "ir.actions.report.xml",
        # "ir.actions.server",
        "ir.autovacuum",
        "ir.config_parameter",
        "ir.exports",
        "ir.fields.converter",
        "ir.filters",
        "ir.http",
        "ir.logging",
        "ir.model",
        "ir.needaction_mixin",
        "ir.qweb",
        "ir.rule",
        "ir.translation",
        # "ir.ui.menu",
        # "ir.ui.view",
        "ir.values",
        "mail.alias",
        "mail.followers",
        "mail.message",
        "mail.notification",
        "report",
        "res.config",
        "res.font",
        # "res.groups",
        "res.request.link",
        "res.users.log",
        "web_tour",
        "workflow",
    ]
    SYSTEM_MODELS_2_MAP = [
        "ir.model.data",
        "ir.module.module",
        "res.groups",
        "res.company",
    ]
    SYSTEM_UNMANAGED = []
    BITTER_COLUMNS = [
        "mail_message_id",
        "message_bounce",
        "message_channel_ids",
        "message_follower_ids",
        "message_ids",
        "message_is_follower",
        "message_last_post",
        "message_needaction",
        "message_needaction_counter",
        "message_partner_ids",
        "message_type",
        "message_unread",
        "message_unread_counter",
        "report_rml",
        "report_rml_content",
        "report_rml_content_data",
        "report_sxw",
        "report_sxw_content",
        "report_sxw_content_data",
        "search_view",
        "search_view_id",
        "seen_message_id",
    ]
    LOG_ACCESS_COLUMNS = [
        "create_uid",
        "create_date",
        "write_uid",
        "write_date",
        "__last_update",
    ]
    MAGIC_COLUMNS = ["id"] + LOG_ACCESS_COLUMNS
    SUPERMAGIC_COLUMNS = MAGIC_COLUMNS + BITTER_COLUMNS
    BLACKLIST_COLUMNS = SUPERMAGIC_COLUMNS + ["parent_left", "parent_right", "state"]
    DEF_INCL_FLDS = [
        "action",
        # "category_id",
        "code",
        # "company_id",
        # "company_ids",
        # "country_id",
        "description",
        "default_code",
        "journal_id",
        "location_id",
        "location_dest_id",
        "login",
        "name",
        "parent_id",
        "partner_id",
        "picking_type_id",
        "product_id",
        "product_uom",
        "type",
        "user_type_id",
    ]
    TABLE_DEF = {
        "base": {
            # Unmanaged fields
            "create_date": {"readonly": True},
            "create_uid": {"readonly": True},
            "display_name": {"readonly": True},
            "id": {"readonly": True, "protect_update": 3},
            "message_channel_ids": {"readonly": True},
            "message_follower_ids": {"readonly": True},
            "message_ids": {"readonly": True},
            "message_is_follower": {"readonly": True},
            "message_last_post": {"readonly": True},
            "message_needaction": {"readonly": True},
            "message_needaction_counter": {"readonly": True},
            "message_unread": {"readonly": True},
            "message_unread_counter": {"readonly": True},
            "password": {"protect_update": 2},
            "password_crypt": {"protect_update": 2},
            "write_date": {"readonly": True},
            "write_uid": {"readonly": True},
        },
        "account.account": {
            "user_type_id": {"required": True},
            "internal_type": {"readonly": False},
        },
        "account.invoice": {
            "account_id": {"readonly": False},
            "comment": {"readonly": False},
            "date": {"readonly": False},
            "date_due": {"readonly": False},
            "date_invoice": {"readonly": False},
            "fiscal_position_id": {"readonly": False},
            "name": {"readonly": False},
            "number": {"readonly": False, "required": False},
            "partner_id": {"readonly": False},
            "partner_shipping_id": {"readonly": False},
            "payment_term_id": {"readonly": False},
            "registration_date": {"readonly": False},
            "type": {"readonly": False},
            "user_id": {"readonly": False},
        },
        "account.payment.term": {},
        "ir.sequence": {"number_next_actual": {"protect_update": 4}},
        "product.category": {},
        "product.product": {
            "company_id": {"readonly": True},
            "type": {"protect_update": "3"},
            "categ_id": {"protect_update": "3"},
            "uom_id": {"protect_update": "3"},
            "uom_po_id": {"protect_update": "3"},
            "purchase_method": {"protect_update": "3"},
            "invoice_policy": {"protect_update": "3"},
        },
        "product.template": {
            "company_id": {"readonly": True},
            "type": {"protect_update": "3"},
            "categ_id": {"protect_update": "3"},
            "uom_id": {"protect_update": "3"},
            "uom_po_id": {"protect_update": "3"},
            "purchase_method": {"protect_update": "3"},
            "invoice_policy": {"protect_update": "3"},
        },
        "purchase.order": {"name": {"required": False}},
        "res.company": {
            "default_picking_type_for_package_preparation_id": {"readonly": True},
            "due_cost_service_id": {"readonly": True},
            "email": {"protect_update": 2},
            "fiscalyear_last_month": {"ancillary": False},
            "font": {"ancillary": False},
            "internal_transit_location_id": {"readonly": True},
            "logo_web": {"protect_update": 2},
            "name": {"protect_update": 2},
            "of_account_end_vat_statement_interest_account_id": {"readonly": True},
            "of_account_end_vat_statement_interest": {"readonly": True},
            "paperformat_id": {"readonly": True},
            "po_double_validation": {"ancillary": False},
            "po_lock": {"ancillary": False},
            "parent_id": {"readonly": True},
            "po_lead": {"readonly": True},
            "project_time_mode_id": {"readonly": True},
            "rml_paper_format": {"ancillary": False},
            "sp_account_id": {"protect_update": 3, "readonly": True},
            "tax_calculation_rounding_method": {"ancillary": False},
        },
        "res.country": {
            "code": {"protect_update": 3},
            "name": {"protect_update": 2},
        },
        "res.country.state": {
            "code": {"protect_update": 3},
            "name": {"protect_update": 2},
        },
        "res.currency": {
            "rate_ids": {"protect_update": 2},
            "rounding": {"protect_update": 2},
        },
        "res.partner": {
            "company_id": {"readonly": True},
            "is_company": {"ancillary": True},
            "name": {"required": True},
            "notify_email": {"readonly": True},
            "property_product_pricelist": {"readonly": True},
            "property_stock_customer": {"readonly": True},
            "property_stock_supplier": {"readonly": True},
            "title": {"readonly": True},
            "type": {"required": True},
        },
        "res.partner.bank": {
            "bank_name": {"readonly": False},
            # 'partner_id': {'ancillary': False},
        },
        "res.users": {
            "action_id": {"readonly": True, "protect_update": 3},
            "category_id": {"readonly": True},
            "company_id": {"readonly": True},
            "login_date": {"readonly": True},
            "new_password": {"readonly": True, "protect_update": 3},
            "opt_out": {"readonly": True},
            "password": {"readonly": True, "ancillary": False, "protect_update": 3},
            "password_crypt": {"readonly": True, "protect_update": 3},
        },
        "sale.order": {"name": {"readonly": False, "required": False}},
        "stock.picking.package.preparation": {"ddt_number": {"required": False}},
    }

    # -----------------------
    # Record cache management
    # -----------------------
    @api.model_cr_context
    def que_expired(self, backend):  # pragma: no cover
        for prio in (1, 2, 3):
            que_name = "IN_QUEUE%d" % prio
            if self.get_struct_model_attr(que_name, "XPIRE"):
                self.set_attr(backend.id, que_name, [])

    @api.model_cr_context
    def que_push(self, backend, action, model, values, ttl, ctx, prio=2):
        que_name = "IN_QUEUE%d" % prio
        ttl -= 1 if isinstance(ttl, int) else 0
        if ttl > 0:
            if action in ("synchro", "trigger", "push"):
                in_queue = self.get_attr(backend.id, que_name) or []
                found_in_que = False
                for que_action, que_model, que_values, que_ttl, que_ctx in in_queue:
                    if (action, model, values) == (que_action, que_model, que_values):
                        found_in_que = True
                        break
                if not found_in_que:
                    in_queue.append((action, model, values, ttl, ctx))
                    self.set_attr(backend.id, que_name, in_queue)
            else:
                raise UserError(_("Invalid action %s to push in queue" % action))

    @api.model_cr_context
    def que_pop(self, backend):
        self.que_expired(backend)
        item = (False, False, False, False, False)
        for prio in (1, 2, 3):
            que_name = "IN_QUEUE%d" % prio
            in_queue = self.get_attr(backend.id, que_name) or []
            if len(in_queue):
                item = in_queue.pop(0)
                self.set_attr(backend.id, que_name, in_queue)
                break
        return item

    @api.model_cr_context
    def que_waiting_len(self, backend):
        self.que_expired(backend)
        que_len = 0
        for prio in (1, 2, 3):
            que_name = "IN_QUEUE%d" % prio
            que_len += len(self.get_attr(backend.id, que_name) or [])
        return que_len

    @api.model_cr_context
    def get_que_list(self, backend):
        self.que_expired(backend)
        que_list = []
        for prio in (1, 2, 3):
            que_name = "IN_QUEUE%d" % prio
            que_list += self.get_attr(backend.id, que_name) or []
        return que_list

    # -------------------------
    # General purpose functions
    # -------------------------
    @api.model
    def is_manageable(self, model_name):
        return model_name in self.SYSTEM_MODELS_2_MAP or not (
            any(map(lambda x: model_name.startswith(x), self.SYSTEM_MODEL_ROOT))
            or model_name in self.SYSTEM_MODELS
            or model_name in self.SYSTEM_UNMANAGED
        )

    @api.model
    def only_to_map(self, model_name):
        return model_name in self.SYSTEM_MODELS_2_MAP

    @api.model
    def set_unmanageable(self, model):  # pragma: no cover
        self.SYSTEM_UNMANAGED.append(model)

    @api.model_cr_context
    def lifetime(self, lifetime):
        return self.CACHE.lifetime(self._cr.dbname, lifetime)

    @api.model_cr_context
    def clean_cache(self, backend_id=None, model=None, lifetime=None):
        cache = self.CACHE
        if lifetime:
            self.lifetime(lifetime)
        if model:
            cache.init_struct_model(self._cr.dbname, model)
        else:
            cache.init_struct(self._cr.dbname)
            for bend in self.get_channel_list():
                bend_id = bend.id
                if not backend_id or bend_id == backend_id:
                    for prio in (1, 2, 3):
                        que_name = "IN_QUEUE%d" % prio
                        cache.init_struct_model(self._cr.dbname, que_name)
        return self.lifetime(0)

    @api.model_cr_context
    def die(self, die=None):  # pragma: no cover
        if die:
            from odoo.cli import start

            start.die("Odoo terminate due connector request")

    @api.model_cr_context
    def set_loglevel(self, loglevel):
        self.set_attr(1, "LOGLEVEL", loglevel)
        return True

    @api.model_cr_context
    def is_struct(self, model):
        return model < "A" or model > "["

    @api.model_cr_context
    def fix_datetime(self, s):
        if not isinstance(s, datetime):
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        return s

    # ------------------
    # Channel primitives
    # ------------------
    #
    # channel_id
    #    \_______ model
    #    \ ...      \____ LOC_FIELDS
    #               |           \____  field_name
    #               |           \ ...
    #               \____ EXT_FIELDS
    #               \ ...
    #
    @api.model_cr_context
    def get_channel_list(self):
        return self.env["synchro.channel"].search([], order="sequence")

    @api.model_cr_context
    def set_channel_base(self, backend_id):
        return self.CACHE.set_channel_base(self._cr.dbname, backend_id)

    @api.model_cr_context
    def get_channel_models(self, backend_id, default=None):
        return self.CACHE.get_channel_models(
            self._cr.dbname, backend_id, default=default
        )

    @api.model_cr_context
    def set_model(self, backend_id, model):
        if model not in self.get_channel_models(backend_id):
            self.init_model(backend_id, model)

    @api.model_cr_context
    def set_attr(self, backend_id, attrib, value):
        self.set_channel_base(backend_id)
        return self.CACHE.set_attr(self._cr.dbname, backend_id, attrib, value)

    @api.model_cr_context
    def get_attr(self, backend_id, attrib, default=None):
        self.set_channel_base(backend_id)
        return self.CACHE.get_attr(self._cr.dbname, backend_id, attrib, default=default)

    @api.model_cr_context
    def get_model_attr(self, backend_id, model, attrib, default=None):
        self.set_model(backend_id, model)
        return self.CACHE.get_model_attr(
            self._cr.dbname, backend_id, model, attrib, default=default
        )

    @api.model_cr_context
    def set_model_attr(self, backend_id, model, attrib, value):
        self.set_model(backend_id, model)
        return self.CACHE.set_model_attr(
            self._cr.dbname, backend_id, model, attrib, value
        )

    @api.model_cr_context
    def del_model_attr(self, backend_id, model, attrib):
        return self.CACHE.del_model_attr(self._cr.dbname, backend_id, model, attrib)

    @api.model_cr_context
    def get_model_field_attr(self, backend_id, model, field, attrib, default=None):
        # Warning! Hierarchy at this level is not linear
        # self.set_model_attr(channel_id, model, field, attrib)
        return self.CACHE.get_model_field_attr(
            self._cr.dbname, backend_id, model, field, attrib, default=default
        )

    @api.model_cr_context
    def set_model_field_attr(self, backend_id, model, field, attrib, value):
        # Warning! Hierarchy at this level is not linear
        # self.set_model_attr(channel_id, model, field, attrib)
        return self.CACHE.set_model_field_attr(
            self._cr.dbname, backend_id, model, field, attrib, value
        )

    @api.model_cr_context
    def age_model(self, backend_id, model):
        self.CACHE.age_model(self._cr.dbname, backend_id, model)

    @api.model_cr_context
    def init_model(self, backend_id, model):
        self.set_channel_base(backend_id)
        self.set_attr(backend_id, model, self.get_attr(backend_id, model) or {})
        self.set_model_attr(backend_id, model, "LOC_FIELDS", {})
        self.set_model_attr(backend_id, model, "EXT_FIELDS", {})
        self.set_model_attr(backend_id, model, "APPLY", {})
        self.set_model_attr(backend_id, model, "PROTECT", {})
        self.set_model_attr(backend_id, model, "SPEC", {})
        self.set_model_attr(backend_id, model, "REQUIRED", {})

    # --------------------------
    # Model structure primitives
    # --------------------------

    @api.model_cr_context
    def model_list(self):
        return self.CACHE.model_list(self._cr.dbname)

    @api.model_cr_context
    def set_struct_model(self, model):
        if model not in self.model_list():
            pass
        self.CACHE.set_struct_model(self._cr.dbname, model)

    @api.model_cr_context
    def set_struct_attr(self, attrib, value):
        self.CACHE.set_struct_model(self._cr.dbname, attrib)
        return self.CACHE.set_struct_attr(self._cr.dbname, attrib, value)

    @api.model_cr_context
    def get_struct_attr(self, attrib, default=None):
        return self.CACHE.get_struct_attr(self._cr.dbname, attrib, default=default)

    @api.model_cr_context
    def get_struct_model_attr(self, model, attrib, default=None):
        self.set_struct_model(model)
        return self.CACHE.get_struct_model_attr(
            self._cr.dbname, model, attrib, default=default
        )

    @api.model_cr_context
    def set_struct_model_attr(self, model, attrib, value):
        self.set_struct_model(model)
        return self.CACHE.set_struct_model_attr(self._cr.dbname, model, attrib, value)

    @api.model_cr_context
    def get_struct_model_field_attr(self, model, field, attrib, default=None):
        return self.CACHE.get_struct_model_field_attr(
            self._cr.dbname, model, field, attrib, default=default
        )
