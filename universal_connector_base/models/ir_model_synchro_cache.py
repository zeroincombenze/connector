#
# Copyright 2019-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging
from datetime import datetime, timedelta
import itertools

from odoo import api, models
from odoo import release

_logger = logging.getLogger(__name__)
try:
    from clodoo import transodoo
except ImportError as err:  # pragma: no cover
    _logger.error(err)
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
    "account.account": [
        ["code", "company_id"],
        ["name", "company_id"],
        # ["dim_name", "company_id"],
    ],
    "account.account.type": [["type"], ["name"], ["dim_name"]],
    "account.invoice": [["number", "company_id"], ["move_name", "company_id"]],
    "account.invoice.line": [["invoice_id", "sequence"], ["invoice_id", "name"]],
    "product.template": [
        ["name", "default_code"],
        ["name", "barcode"],
        ["name"],
        ["default_code"],
        ["barcode"],
        ["dim_name"],
    ],
    "product.product": [
        ["name", "default_code"],
        ["name", "barcode"],
        ["name"],
        ["default_code"],
        ["barcode"],
        ["dim_name"],
    ],
    "product.supplierinfo": [["name", "product_tmpl_id", "qty"], "!"],
    "project.project": [["account_analytic_id"]],
    "sale.order": [["name"]],
    "sale.order.line": [["order_id", "sequence"], ["order_id", "name"]],
}
# MAGIC_FIELDS = {
#     "res.partner": {
#         "company_id": False,
#         "is_company": True,
#         "supplier": True,
#     },
# }
# Warning: order is very important!
CANDIDATE_KEYS = (
    "acc_number",
    "login",
    "default_code",
    "code",
    "key",
    "serial_number",
    "vat",
    # "description",
    # "comment",
    "name",
)
ANCILLARY_KEYS = (
    "is_company",
    "left_id",
    "parent_id",
    "right_id",
    "sequence",
    "type",
    "type_tax_use",
)
ANCILLARY_LINE_KEYS = (
    "account_id",
    "product_id",
    "product_qty",
    "quantity",
    "product_uom_qty",
    "credit",
    "debit",
)


class IrModelSynchroCache(models.Model):
    _name = "ir.model.synchro.cache"

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
        "ir.actions.actions",
        "ir.actions.act_window",
        "ir.actions.act_window.view",
        "ir.actions.report.xml",
        "ir.actions.server",
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
        "ir.ui.menu",
        "ir.ui.view",
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
    def expired_cache(self, backend_id, vmodel, model):  # pragma: no cover
        cache_model = "_QUEUE_SYNC"
        if self.get_struct_model_attr(cache_model, "XPIRE"):
            self.set_struct_model(cache_model)
            self.CACHE.set_struct_cache(self._cr.dbname, cache_model)
        if self.get_model_attr(backend_id, cache_model, "XPIRE"):
            self.set_attr(backend_id, cache_model, {})
            self.CACHE.set_model_cache(self._cr.dbname, backend_id, cache_model)

    @api.model_cr_context
    def push_id(self, backend_id, vmodel, model, loc_id=None, ext_id=None):
        self.expired_cache(backend_id, vmodel, model)
        cache_model = "_QUEUE_SYNC"
        if loc_id:
            rec_list = self.get_struct_model_attr(cache_model, model, default=[])
            if loc_id not in rec_list:
                rec_list.append(loc_id)
                self.set_struct_model_attr(cache_model, model, rec_list)
        if ext_id:
            rec_list = self.get_model_attr(backend_id, cache_model, vmodel, default=[])
            if ext_id not in rec_list:
                rec_list.append(ext_id)
                self.set_model_attr(backend_id, cache_model, vmodel, rec_list)

    @api.model_cr_context
    def pop_id(self, backend_id, vmodel, model, loc_id=None, ext_id=None):
        self.expired_cache(backend_id, vmodel, model)
        cache_model = "_QUEUE_SYNC"
        if loc_id:
            rec_list = self.get_struct_model_attr(cache_model, model, default=[])
            if loc_id in rec_list:
                rec_list.pop(rec_list.index(loc_id))
                self.set_struct_model_attr(cache_model, model, rec_list)
        if ext_id:
            rec_list = self.get_model_attr(backend_id, cache_model, vmodel, default=[])
            if ext_id in rec_list:
                rec_list.pop(rec_list.index(ext_id))
                self.set_model_attr(backend_id, cache_model, vmodel, rec_list)

    @api.model_cr_context
    def id_is_in_cache(self, backend_id, vmodel, model, loc_id=None, ext_id=None):
        self.expired_cache(backend_id, vmodel, model)
        cache_model = "_QUEUE_SYNC"
        return (
            loc_id
            and loc_id in self.get_struct_model_attr(cache_model, model, default=[])
        ) or (
            ext_id
            and ext_id
            in self.get_model_attr(backend_id, cache_model, vmodel, default=[])
        )

    @api.model_cr_context
    def que_push(self, backend, action, model, values, ttl):
        ttl -= 1 if isinstance(ttl, int) else 0
        if ttl > 0:
            if action in ("synchro", "trigger"):
                in_queue = self.get_attr(backend.id, "IN_QUEUE") or []
                found_in_que = False
                for que_action, que_model, que_values, que_ttl in in_queue:
                    if (action, model, values) == (que_action, que_model, que_values):
                        found_in_que = True
                        break
                if not found_in_que:
                    in_queue.append((action, model, values, ttl))
                    self.set_attr(backend.id, "IN_QUEUE", in_queue)
            else:
                raise RuntimeError("Invalid action %s to push in queue" % action)

    @api.model_cr_context
    def que_priority_push(self, backend, action, model, values, ttl):
        ttl -= 1 if isinstance(ttl, int) else 0
        if ttl > 0:
            if action in ("synchro", "trigger"):
                in_queue = self.get_attr(backend.id, "IN_QUEUE") or []
                found_in_que = False
                for que_action, que_model, que_values, que_ttl in in_queue:
                    if (action, model, values) == (que_action, que_model, que_values):
                        found_in_que = True
                        break
                if not found_in_que:
                    in_queue.insert(0, (action, model, values, ttl))
                    self.set_attr(backend.id, "IN_QUEUE", in_queue)
            else:
                raise RuntimeError("Invalid action %s to push in queue" % action)

    @api.model_cr_context
    def que_pop(self, backend):
        in_queue = self.get_attr(backend.id, "IN_QUEUE") or []
        if len(in_queue):
            item = in_queue.pop(0)
            self.set_attr(backend.id, "IN_QUEUE", in_queue)
        else:
            item = (False, False, False, False)
        return item

    @api.model_cr_context
    def que_waiting_len(self, backend):
        in_queue = self.get_attr(backend.id, "IN_QUEUE") or []
        return len(in_queue)

    # -------------------------
    # General purpose functions
    # -------------------------
    @api.model
    def is_manageable(self, model_name):
        return not (
            any(map(lambda x: model_name.startswith(x), self.SYSTEM_MODEL_ROOT))
            or model_name in self.SYSTEM_MODELS
            or model_name in self.SYSTEM_UNMANAGED
        )

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
        for channel in self.get_channel_list():
            chn_id = channel.id
            if not backend_id or chn_id == backend_id:
                cache.init_channel(self._cr.dbname, chn_id)
        if model:
            cache.init_struct_model(self._cr.dbname, model)
        else:
            cache.init_struct(self._cr.dbname)
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

    def get_indexes(self, model):
        query = """select c.name from ir_model m, ir_model_constraint c
        where c.model = m.id and m.model = '%s'"""
        self._cr.execute(query % model)  # pylint: disable=E8103
        res = []
        for row in self.env.cr.fetchall():
            res.append(row[0])
        return res

    def get_index_fields(self, model, index_name=None):
        # index_name = index_name.replace('.', '_') if index_name else None
        # INDEX_FIELDS = """select pgc.conname as constraint_name,
        #                   ccu.table_name,
        #                   ccu.column_name,
        #                   pgc.consrc as definition
        # from pg_constraint pgc
        # join pg_namespace nsp on nsp.oid = pgc.connamespace
        # join pg_class  cls on pgc.conrelid = cls.oid
        # left join information_schema.constraint_column_usage ccu
        # on pgc.conname = ccu.constraint_name and
        # nsp.nspname = ccu.constraint_schema
        # where contype ='u' and table_name='%s'
        # order by constraint_name,table_name"""
        INDEX_FIELDS = """
        select i.relname as index_name,
               t.relname as table_name,
               a.attname as column_name
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
        self._cr.execute(  # pylint: disable=E8103
            INDEX_FIELDS % model.replace(".", "_")
        )
        res = {}
        for row in self.env.cr.fetchall():
            if index_name and index_name != row[0]:
                continue
            if row[0] not in res:
                res[row[0]] = []
            res[row[0]].append(row[2])
        return res

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

    # ----------------
    # Cache management
    # ----------------

    def get_index_keys(self, model, uname, skeys):
        if "!" in skeys:
            pos = skeys.index("!")
            del skeys[pos]
            return uname, skeys
        elif [] in skeys:
            pos = skeys.index([])
            del skeys[pos]
        else:
            pos = -1
        for index_name in self.get_indexes(model):
            keys = []
            indexes = self.get_index_fields(model, index_name=index_name)
            if not indexes:
                continue
            for fieldname in indexes[index_name]:
                keys.append(fieldname)
            if not keys:
                # print('@@@ Invalid index %s' % index_name)  # debug
                continue
            if len(keys) == 1 and not uname:
                uname = keys[0]
            found = False
            for kk in skeys:
                if set(keys) == set(kk):
                    found = True
                    break
            if not found:
                if pos < 0:
                    skeys.append(keys)
                else:
                    skeys.insert(pos, keys)
        return uname, skeys

    @api.model_cr_context
    def store_model_field(
        self,
        channel_id,
        model,
        loc_name,
        ext_name,
        apply,
        protect_update,
        spec,
        required,
    ):
        if model == "res.partner" and loc_name == "assigned_bank":
            pass
        self.set_model_field_attr(channel_id, model, loc_name, "LOC_FIELDS", ext_name)
        self.set_model_field_attr(channel_id, model, ext_name, "EXT_FIELDS", loc_name)
        if apply:
            self.set_model_field_attr(channel_id, model, loc_name, "APPLY", apply)
        if protect_update and protect_update != "0":
            self.set_model_field_attr(
                channel_id, model, loc_name, "PROTECT", protect_update
            )
        if spec:
            self.set_model_field_attr(channel_id, model, loc_name, "SPEC", spec)
        self.set_model_field_attr(channel_id, model, loc_name, "REQUIRED", required)

    def store_field_from_rec(self, backend_id, model, field):
        if field.name:
            loc_name = field.name
        else:
            loc_name = ".%s" % field.counterpart_name
        if field.counterpart_name:
            ext_name = field.counterpart_name
        else:
            ext_name = ".%s" % field.name
        required = (
            self.get_struct_model_field_attr(model, loc_name, "required")
            or field.required
        )
        apply = field.apply
        if (
            loc_name
            in itertools.chain.from_iterable(self.get_struct_model_attr(model, "SKEYS"))
            and loc_name in CANDIDATE_KEYS
        ):
            if not apply:
                apply = "set_tmp_name()"
            elif apply.find("set_tmp_name()") < 0:
                apply += ",set_tmp_name()"
        self.store_model_field(
            backend_id,
            model,
            loc_name,
            ext_name,
            apply,
            field.protect_update,
            field.spec,
            required,
        )
        if apply != field.apply:
            field.write({"apply": apply})

    @api.model_cr_context
    def store_odoo_field_from_rec(self, backend_id, model, field):
        if not self.is_struct(field) or field == "id":
            return
        # diff = False
        ext_ref = "%s_id" % self.get_attr(backend_id, "PREFIX")
        required = self.get_struct_model_field_attr(model, field, "required")
        if field == ext_ref:
            self.store_model_field(
                backend_id, model, "id", field, "", False, False, required
            )
        else:
            ext_odoo_ver = self.get_attr(backend_id, "ODOO_FVER")
            if ext_odoo_ver:
                ext_name = transodoo.translate_from_to(
                    self.get_attr(backend_id, "TNL"),
                    model,
                    field,
                    release.major_version,
                    ext_odoo_ver,
                )
            else:
                ext_name = field
            field_def = self.TABLE_DEF.get(model, {}).get(field, {})
            apply = ""
            if "APPLY" in field_def:
                apply = field_def["APPLY"]
            if (
                field
                in itertools.chain.from_iterable(
                    self.get_struct_model_attr(model, "SKEYS")
                )
                and field in CANDIDATE_KEYS
            ):
                if not apply:
                    apply = "set_tmp_name()"
                elif apply.find("set_tmp_name()") < 0:
                    apply += ",set_tmp_name()"
                # diff = True
            if not apply:
                apply = "odoo_migrate()"
            elif apply.find("odoo_migrate()") < 0:
                apply += ",odoo_migrate()"
            self.store_model_field(
                backend_id, model, field, ext_name, apply, False, False, required
            )
            synchro_model = self.env["synchro.channel.model"].search(
                [("name", "=", model), ("synchro_channel_id", "=", backend_id)]
            )
            vals = {
                "name": field,
                "counterpart_name": ext_name,
                "apply": apply,
                "protect_update": "0",
                "required": required,
                "model_id": synchro_model.id,
            }
            self.env["synchro.channel.model.field"].create(vals)

    @api.model_cr_context
    def setup_channel_model_fields(self, synchro_model):
        model = synchro_model.name
        channel_id = synchro_model.synchro_channel_id.id
        channel = self.env["synchro.channel"].browse(channel_id)
        for field in self.env["synchro.channel.model.field"].search(
            [("model_id", "=", synchro_model.id)]
        ):
            self.store_field_from_rec(channel_id, model, field)
        if channel.identity == "odoo":
            for field in self.get_struct_attr(model):
                if (
                    (
                        self.is_struct(field)
                        and field not in ("id", "vg7_id", "oe7_id", "oe8_id", "oe10_id")
                    )
                    and not self.get_model_attr(channel_id, model, "XPIRE")
                    and field
                    not in self.get_model_attr(channel_id, model, "LOC_FIELDS")
                ):
                    self.store_odoo_field_from_rec(channel_id, model, field)
        # special names
        ext_ref = "%s_id" % self.get_attr(channel_id, "PREFIX")
        self.set_model_field_attr(channel_id, model, "id", "LOC_FIELDS", "")
        self.set_model_field_attr(channel_id, model, ext_ref, "LOC_FIELDS", "id")
        self.set_model_field_attr(channel_id, model, "id", "EXT_FIELDS", ext_ref)

    @api.model_cr_context
    def store_model_1_channel(self, backend_id, rec):
        model = rec.name
        # if rec.cron_sync:
        #     self.set_model_attr(backend_id, model, "2PULL", True)
        if not self.get_attr(backend_id, "TNL"):
            tnldict = {}
            transodoo.read_stored_dict(tnldict)
            self.set_attr(backend_id, "TNL", tnldict)
        # TODO: debug -> minutes=1 production -> minutes=9900
        deltatime = ((self.lifetime(0) / 20) + 1) ** 2
        if (
            self.fix_datetime(rec.write_date) + timedelta(minutes=deltatime)
        ) < datetime.now():
            if not self.get_struct_model_attr(model, "SKEYS"):
                actual_model = self.env["ir.model.synchro"].get_actual_model(
                    model, only_name=True
                )
                uname, skeys = self.get_default_keys(actual_model)
                # self.set_struct_model_attr(model, "SKEYS", skeys)
                self.set_struct_model_attr(model, "SKEYS", eval(rec.search_keys))
                # self.set_struct_model_attr(model, "MODEL_KEY", uname)
                self.set_struct_model_attr(model, "MODEL_KEY", rec.field_uname)
                rec.write({"search_keys": skeys, "field_uname": uname})
        else:
            self.set_struct_model_attr(model, "SKEYS", eval(rec.search_keys))
            self.set_struct_model_attr(model, "MODEL_KEY", rec.field_uname)
        self.set_model_attr(backend_id, model, "BIND", rec.counterpart_name)
        channel = self.env["synchro.channel"].browse(backend_id)
        if rec.model_spec:
            self.set_model_attr(backend_id, model, "MODEL_SPEC", rec.model_spec)
        if channel.identity == "vg7" and model == "res.partner.shipping":
            self.set_model_attr(backend_id, model, "KEY_ID", "customer_shipping_id")
        else:
            self.set_model_attr(backend_id, model, "KEY_ID", "id")
        if channel.identity == "vg7" and model == "res.partner.supplier":
            self.set_model_attr(
                backend_id,
                model,
                "EXT_ID",
                "%s2_id" % self.get_attr(backend_id, "PREFIX"),
            )
        elif channel.identity == "vg7" and model == "res.partner.bank.company":
            self.set_model_attr(
                backend_id,
                model,
                "EXT_ID",
                "%s2_id" % self.get_attr(backend_id, "PREFIX"),
            )
        else:
            self.set_model_attr(
                backend_id,
                model,
                "EXT_ID",
                "%s_id" % self.get_attr(backend_id, "PREFIX"),
            )
        if channel.identity == "vg7":
            if model == "res.partner.invoice":
                self.set_model_attr(backend_id, model, "ID_OFFSET", 200000000)
            elif model == "res.partner.shipping":
                self.set_model_attr(backend_id, model, "ID_OFFSET", 100000000)
        self.setup_channel_model_fields(rec)

    @api.model_cr_context
    def setup_ext_model(self, backend_id, rec):
        if (
            backend_id
            and backend_id == rec.synchro_channel_id.id
            and backend_id in [x.id for x in self.get_channel_list()]
        ):
            return
        model = rec.name
        if not backend_id:
            backend_id = rec.synchro_channel_id.id
        if self.get_model_attr(backend_id, model, "XPIRE"):
            return
        channel = self.env["synchro.channel"].browse(backend_id)
        self.setup_1_channel(channel)
        self.init_model(backend_id, model)
        self.store_model_1_channel(backend_id, rec)
        self.CACHE.set_model_cache(self._cr.dbname, backend_id, model)

    @api.model_cr_context
    def setup_1_channel(self, backend):
        if self.get_attr(backend.id, "XPIRE"):
            return
        self.set_channel_base(backend.id)
        self.set_attr(backend.id, "PRIO", backend.sequence)
        self.set_attr(
            backend.id, "OUT_QUEUE", self.get_attr(backend.id, "OUT_QUEUE", default=[])
        )
        self.set_attr(
            backend.id, "IN_QUEUE", self.get_attr(backend.id, "IN_QUEUE", default=[])
        )
        self.set_attr(
            backend.id,
            "_QUEUE_SYNC",
            self.get_attr(backend.id, "_QUEUE_SYNC", default={}),
        )
        self.set_attr(backend.id, "PREFIX", backend.prefix)
        self.set_attr(
            backend.id,
            "ODOO_FVER",
            {
                "oe6": "6.1",
                "oe7": "7.0",
                "oe8": "8.0",
                "oe9": "9.0",
                "oe10": "10.0",
                "oe11": "11.0",
                "oe12": "12.0",
                "oe13": "13.0",
                "oe14": "14.0",
                "oe15": "15.0",
                "oe16": "16.0",
                "oe17": "17.0",
                "oe18": "18.0",
            }.get(backend.prefix.split(":")[0], ""),
        )
        self.set_attr(backend.id, "IDENTITY", backend.identity)
        self.set_attr(backend.id, "METHOD", backend.method)
        ctx = {}
        if backend.company_id:
            ctx["company_id"] = backend.company_id.id
            ctx["country_id"] = backend.company_id.partner_id.country_id.id
        else:
            ctx["company_id"] = self.env.user.company_id.id
            ctx["country_id"] = self.env.user.company_id.partner_id.country_id.id
        ctx["is_company"] = True
        self.set_attr(backend.id, "CTX", ctx)
        self.set_attr(backend.id, "CLIENT_KEY", backend.client_key)
        self.set_attr(backend.id, "COUNTERPART_URL", backend.counterpart_url)
        self.set_attr(backend.id, "EXCHANGE_PATH", backend.exchange_path)
        self.set_attr(backend.id, "PASSWORD", backend.password)
        if backend.product_without_variants:
            self.set_attr(backend.id, "NO_VARIANTS", True)
        # if channel.trace:
        #     self.set_attr(channel.id, 'LOGLEVEL', 'info')
        # else:
        #     self.set_attr(channel.id, 'LOGLEVEL', 'debug')
        self.set_attr(backend.id, "LOGLEVEL", backend.tracelevel)
        self.CACHE.set_channel_cache(self._cr.dbname, backend.id)

    @api.model_cr_context
    def setup_channels(self, all=None):
        """If channel information are expired, read values from channel table
        and store them into memory"""
        if not len(self.get_channel_list()) or all:
            for channel in self.env["synchro.channel"].search([], order="sequence"):
                self.setup_1_channel(channel)

    @api.model_cr_context
    def setup_model_structure(self, model, actual_model):
        """Store model structure into memory"""
        actual_model = actual_model or model
        model = model or actual_model
        if not model or self.get_struct_model_attr(model, "XPIRE"):
            return
        # ir_model = self.env["ir.model.fields"]
        self.set_struct_model(actual_model)
        for fieldname, field in self.env[actual_model]._fields.items():
            global_def = self.TABLE_DEF.get("base", {}).get(fieldname, {})
            field_def = self.TABLE_DEF.get(model, {}).get(fieldname, {})
            attrs = {}
            for attr in ("required", "readonly", "protect_update"):
                if attr in field_def:
                    attrs[attr] = field_def[attr]
                elif attr in global_def:
                    attrs[attr] = global_def[attr]
                elif hasattr(field, attr):
                    attrs[attr] = getattr(field, attr)
                elif attr == "protect_update":
                    attrs[attr] = "0"
                else:
                    attrs[attr] = False
            if getattr(field, "type") in ("binary", "reference") or (
                field.related and not field.required
            ):
                attrs["readonly"] = True
            elif attrs["required"]:
                attrs["readonly"] = False

            self.set_struct_model_attr(
                actual_model,
                fieldname,
                {
                    "ttype": getattr(field, "type"),
                    "relation": getattr(field, "comodel_name"),
                    "required": attrs["required"],
                    "readonly": attrs["readonly"],
                    "protect_update": attrs["protect_update"],
                },
            )
            if getattr(field, "comodel_name") != actual_model:
                if getattr(field, "comodel_name", "") == ("%s.line" % actual_model):
                    self.set_struct_model_attr(actual_model, "CHILD_IDS", fieldname)
                    self.set_struct_model_attr(
                        actual_model, "MODEL_CHILD", getattr(field, "comodel_name")
                    )
                elif (
                    actual_model.endswith(".line")
                    and getattr(field, "comodel_name")
                    and actual_model.startswith(getattr(field, "comodel_name") or "")
                ):
                    self.set_struct_model_attr(actual_model, "PARENT_ID", fieldname)
                elif actual_model.startswith(getattr(field, "comodel_name") or ""):
                    self.set_struct_model_attr(actual_model, "SUPPL_KEY", fieldname)
                # TODO:avoid recursive loop
                # elif getattr(field, "comodel_name") == actual_model:
                #    constraints = ['id', '<>', fieldname]
            if fieldname == "original_state":
                self.set_struct_model_attr(actual_model, "MODEL_STATE", True)
            elif fieldname == "to_delete":
                self.set_struct_model_attr(actual_model, "MODEL_2DELETE", True)
            elif fieldname == "name":
                self.set_struct_model_attr(actual_model, "MODEL_WITH_NAME", True)
            elif fieldname == "active":
                self.set_struct_model_attr(actual_model, "MODEL_WITH_ACTIVE", True)
            elif fieldname == "dim_name":
                self.set_struct_model_attr(actual_model, "MODEL_WITH_DIMNAME", True)
            elif fieldname == "company_id":
                self.set_struct_model_attr(actual_model, "MODEL_WITH_COMPANY", True)
            elif fieldname == "country_id":
                self.set_struct_model_attr(actual_model, "MODEL_WITH_COUNTRY", True)
        self.CACHE.set_struct_cache(self._cr.dbname, model)

    @api.model_cr_context
    def open(self, backend=None, model=None, ext_model=None, cls=None):
        """Setup cache if needed, setup model cache if required and needed"""
        SynchroModel = self.env["synchro.channel.model"]
        SynchroLog = self.env["ir.model.synchro.log"]
        if not model and backend:
            synchro_model = SynchroModel.get_synchro_model_from_ext(backend, ext_model)
            if synchro_model:
                model = synchro_model.name
        if not model or model not in self.env:
            SynchroLog.logmsg(
                "error",
                "!%(E)s! Invalid (external) model %(model)s on backend %(backend)s",
                res_model=model or ext_model,
                backend=backend,
                errcode=-13,
            )
            return False
        actual_model = model
        self.setup_model_structure(model, actual_model)
        self.set_struct_model("_QUEUE_SYNC")
        if cls is not None:
            if cls.__class__.__name__ != model:
                raise RuntimeError(
                    "Class %s not of declared model %s"
                    % (cls.__class__.__name__, model)
                )
            if hasattr(cls, "CHILD_IDS"):
                self.set_struct_model_attr(
                    actual_model, "CHILD_IDS", getattr(cls, "CHILD_IDS")
                )
            if hasattr(cls, "MODEL_CHILD"):
                self.set_struct_model_attr(
                    actual_model, "MODEL_CHILD", getattr(cls, "MODEL_CHILD")
                )
            if hasattr(cls, "PARENT_ID"):
                self.set_struct_model_attr(
                    actual_model, "PARENT_ID", getattr(cls, "PARENT_ID")
                )
