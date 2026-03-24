# -*- coding: utf-8 -*-
#
# Copyright 2019-26 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
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
except ImportError as err:
    _logger.error(err)
try:
    from odoo_score import odoo_score
except ImportError as err:
    _logger.error(err)


DEF_SKEYS = {
    "res.partner": [
        ["vat", "fiscalcode", "type"],
        ["vat", "name", "type"],
        ["fiscalcode", "dim_name", "type"],
        ["vat", "dim_name", "type"],
        ["vat", "type"],
        ["dim_name", "type"],
        ["vat", "fiscalcode", "is_company"],
        ["vat"],
        ["name", "is_company"],
    ],
    "res.company": [["vat"], ["name"], ["partner_id"]],
    "account.account": [
        ["code", "company_id"],
        ["name", "company_id"],
        ["dim_name", "company_id"],
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
# Warning: order is very important!
CANDIDATE_KEYS = (
    "acc_number",
    "login",
    "default_code",
    "code",
    "key",
    "serial_number",
    "description",
    "comment",
    "name",
    "dim_name",
)
SUPPLEMENTAL_KEYS = ("amount", "sequence")
ANCILLARY_KEYS = ("company_id", "type_tax_use")
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
        "res.groups",
        "res.request.link",
        "res.users.log",
        "web_tour",
        "workflow",
    ]
    SYSTEM_UNMANAGED = []
    TABLE_DEF = {
        "base": {
            # 'company_id': {'required': True},
            "create_date": {"readonly": True},
            "create_uid": {"readonly": True},
            "display_name": {"readonly": True},
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
            "fiscalyear_last_month": {"ancillary": False},
            "font": {"ancillary": False},
            "internal_transit_location_id": {"readonly": True},
            "of_account_end_vat_statement_interest_account_id": {"readonly": True},
            "of_account_end_vat_statement_interest": {"readonly": True},
            "paperformat_id": {"readonly": True},
            "po_double_validation": {"ancillary": False},
            "po_lock": {"ancillary": False},
            "parent_id": {"readonly": True},
            "po_lead": {"readonly": True},
            "project_time_mode_id": {"readonly": True},
            "rml_paper_format": {"ancillary": False},
            "sp_account_id": {"readonly": True},
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
            "notify_email": {"readonly": True},
            "property_product_pricelist": {"readonly": True},
            "property_stock_customer": {"readonly": True},
            "property_stock_supplier": {"readonly": True},
            "title": {"readonly": True},
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
    def expired_cache(self, backend_id, vmodel, model):
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
    def set_unmanageable(self, model):
        self.SYSTEM_UNMANAGED.append(model)

    @api.model_cr_context
    def lifetime(self, lifetime):
        return self.CACHE.lifetime(self._cr.dbname, lifetime)

    @api.model_cr_context
    def clean_cache(self, backend_id=None, model=None, lifetime=None):
        _logger.info(
            "> clean_cache(%d,%s,%d)" % ((backend_id or -1), model, (lifetime or -1))
        )
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
    def die(self, die=None):
        if die:
            from odoo.cli import start
            start.die("Odoo terminate due connector request")

    @api.model_cr_context
    def set_loglevel(self, loglevel):
        self.setup_channels(all=True)
        for channel in self.get_channel_list():
            channel_id = channel.id
            self.set_attr(channel_id, "LOGLEVEL", loglevel)
        return True

    @api.model_cr_context
    def is_struct(self, model):
        return model < "A" or model > "["

    # ------------------
    # Backend primitives
    # ------------------
    #
    # backend_id
    #    \_______ model
    #    \ ...      \____ LOC_FIELDS
    #               |           \____  field_name
    #               |           \ ...
    #               \____ EXT_FIELDS
    #               \ ...
    #
    @api.model_cr_context
    def get_channel_list(self):
        return [
            x
            for x in self.env["synchro.channel"].browse(
                self.CACHE.get_channel_list(self._cr.dbname)
            )
        ]

    @api.model_cr_context
    def set_channel_base(self, backend_id):
        return self.CACHE.set_channel_base(self._cr.dbname, backend_id)

    @api.model_cr_context
    def get_channel_models(self, backend_id, default=None):
        return self.CACHE.get_channel_models(
            self._cr.dbname, backend_id, default=default
        )

    # @api.model_cr_context
    # def set_model(self, backend_id, model):
    #     if not self.get_attr(backend_id, model):
    #         self.init_model(backend_id, model)

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
        # self.set_model(backend_id, model)
        return self.CACHE.get_model_attr(
            self._cr.dbname, backend_id, model, attrib, default=default
        )

    @api.model_cr_context
    def set_model_attr(self, backend_id, model, attrib, value):
        # self.set_model(backend_id, model)
        return self.CACHE.set_model_attr(
            self._cr.dbname, backend_id, model, attrib, value
        )

    @api.model_cr_context
    def del_model_attr(self, backend_id, model, attrib):
        return self.CACHE.del_model_attr(self._cr.dbname, backend_id, model, attrib)

    @api.model_cr_context
    def get_model_field_attr(self, backend_id, model, field, attrib, default=None):
        # Warning! Hierarchy at this level is not linear
        return self.CACHE.get_model_field_attr(
            self._cr.dbname, backend_id, model, field, attrib, default=default
        )

    @api.model_cr_context
    def set_model_field_attr(self, backend_id, model, field, attrib, value):
        # Warning! Hierarchy at this level is not linear
        return self.CACHE.set_model_field_attr(
            self._cr.dbname, backend_id, model, field, attrib, value
        )

    @api.model_cr_context
    def init_backend_model(self, backend_id, model):
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
    def get_default_keys(self, model):
        skeys = DEF_SKEYS.get(model, [])
        uname = DEF_SKEYS.get(model, [[[]]])[0][0] or False
        is_child_model = self.get_struct_model_attr(model, "PARENT_ID")
        ancillary = {}
        ancillary_line = {}
        for field in ANCILLARY_KEYS:
            ancillary[field] = field in self.get_struct_attr(model)
        if is_child_model:
            ancillary[self.get_struct_model_attr(model, "PARENT_ID")] = True
            for field in ANCILLARY_LINE_KEYS:
                ancillary_line[field] = field in self.get_struct_attr(model)
        for nm in CANDIDATE_KEYS + SUPPLEMENTAL_KEYS:
            if nm in self.get_struct_attr(model) and (
                is_child_model
                or not self.get_struct_model_field_attr(model, nm, "readonly")
            ):
                keys = [nm]
                for kk in ancillary:
                    if ancillary[kk]:
                        keys.append(kk)
                if is_child_model and nm != "sequence":
                    for kk in ancillary_line:
                        if ancillary_line[kk]:
                            keys.append(kk)
                if self.get_struct_model_attr(model, "SUPPL_KEY"):
                    keys.append(self.get_struct_model_attr(model, "SUPPL_KEY"))
                found = False
                for kk in skeys:
                    if not set(keys) - set(kk):
                        found = True
                        break
                if not found:
                    skeys.append(keys)
                if not uname:
                    uname = nm
        return self.get_index_keys(model, uname, skeys)

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
    def store_model_field(self, channel_id, model, loc_name, ext_name, apply,
                          protect_update, spec, required):
        # if model == "res.partner" and loc_name == "assigned_bank":
        #     pass
        self.set_model_field_attr(channel_id, model, loc_name, "LOC_FIELDS", ext_name)
        self.set_model_field_attr(channel_id, model, ext_name, "EXT_FIELDS", loc_name)
        if apply:
            self.set_model_field_attr(channel_id, model, loc_name, "APPLY", apply)
        if protect_update and protect_update != "0":
            self.set_model_field_attr(
                channel_id, model, loc_name, "PROTECT", protect_update)
        if spec:
            self.set_model_field_attr(channel_id, model, loc_name, "SPEC", spec)
        self.set_model_field_attr(channel_id, model, loc_name, "REQUIRED", required)

    def store_field_from_rec(self, backend_id, model, field):
        if field.name:
            loc_name = field.name.strip()
        else:
            loc_name = ".%s" % field.counterpart_name.strip()
        if field.counterpart_name:
            ext_name = field.counterpart_name.strip()
        else:
            ext_name = ".%s" % field.name.strip()
        required = (
            self.get_struct_model_field_attr(model, loc_name, "required")
            or field.required
        )
        apply = field.apply.strip()
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
            model_rec = self.env["synchro.channel.model"].search(
                [("name", "=", model), ("synchro_channel_id", "=", backend_id)]
            )
            vals = {
                "name": field,
                "counterpart_name": ext_name,
                "apply": apply,
                "protect_update": "0",
                "required": required,
                "model_id": model_rec.id,
            }
            self.env["synchro.channel.model.fields"].create(vals)

    @api.model_cr_context
    def setup_channel_model_fields(self, model_rec):
        model = model_rec.name
        backend = model_rec.synchro_channel_id
        for field in self.env["synchro.channel.model.fields"].search(
            [("model_id", "=", model_rec.id)]
        ):
            self.store_field_from_rec(backend.id, model, field)
        if backend.identity == "odoo":
            for field in self.get_struct_attr(model):
                if (
                    (self.is_struct(field)
                     and field not in ("id", "vg7_id", "oe7_id", "oe8_id", "oe10_id"))
                    and not self.get_model_attr(backend.id, model, "XPIRE")
                    and field
                    not in self.get_model_attr(backend.id, model, "LOC_FIELDS")
                ):
                    self.store_odoo_field_from_rec(backend.id, model, field)
        # special names
        ext_ref = "%s_id" % self.get_attr(backend.id, "PREFIX")
        self.set_model_field_attr(backend.id, model, "id", "LOC_FIELDS", "")
        self.set_model_field_attr(backend.id, model, ext_ref, "LOC_FIELDS", "id")
        self.set_model_field_attr(backend.id, model, "id", "EXT_FIELDS", ext_ref)

    @api.model_cr_context
    def store_model_1_backend(self, backend, rec):
        model = rec.name
        if not self.get_attr(backend.id, "TNL"):
            tnldict = {}
            transodoo.read_stored_dict(tnldict)
            self.set_attr(backend.id, "TNL", tnldict)
        if (
            self.get_struct_model_attr(model, "SKEYS")
            and self.get_struct_model_attr(model, "XPIRE")
        ):
            return
        deltatime = ((self.lifetime(0) / 20) + 1) ** 2
        # TODO: debug -> minutes=1 production -> minutes=9900
        if not rec.search_keys or (
                datetime.strptime(rec.write_date, "%Y-%m-%d %H:%M:%S")
                + timedelta(minutes=deltatime)) < datetime.now():
            actual_model = self.env["ir.model.synchro"].get_actual_model(
                model, only_name=True
            )
            uname, skeys = self.get_default_keys(actual_model)
            # self.set_struct_model_attr(model, "SKEYS", eval(rec.search_keys))
            # self.set_struct_model_attr(model, "MODEL_KEY", rec.field_uname)
            rec.write({"search_keys": skeys, "field_uname": uname})
            self.env["ir.model.synchro"].logmsg(
                "debug",
                "### %(model)s SKEYS=%(skeys)s UNAME=%(uname)s",
                model=model,
                ctx={"skeys": skeys, "uname": uname},
            )
        self.set_model_attr(backend.id, model, "2PULL", rec.cron_sync)
        self.set_struct_model_attr(model, "SKEYS", eval(rec.search_keys))
        self.set_struct_model_attr(model, "MODEL_KEY", rec.field_uname)
        self.set_model_attr(backend.id, model, "BIND", rec.counterpart_name)
        # backend = self.env["synchro.channel"].browse(backend_id)
        if rec.model_spec:
            self.set_model_attr(backend.id, model, "MODEL_SPEC", rec.model_spec)
        if backend.identity == "vg7" and model == "res.partner.shipping":
            self.set_model_attr(backend.id, model, "KEY_ID", "customer_shipping_id")
        else:
            self.set_model_attr(backend.id, model, "KEY_ID", "id")
        if backend.identity == "vg7" and model == "res.partner.supplier":
            self.set_model_attr(
                backend.id,
                model,
                "EXT_ID",
                "%s2_id" % self.get_attr(backend.id, "PREFIX"),
            )
        elif backend.identity == "vg7" and model == "res.partner.bank.company":
            self.set_model_attr(
                backend.id,
                model,
                "EXT_ID",
                "%s2_id" % self.get_attr(backend.id, "PREFIX"),
            )
        else:
            self.set_model_attr(
                backend.id,
                model,
                "EXT_ID",
                "%s_id" % self.get_attr(backend.id, "PREFIX"),
            )
        if backend.identity == "vg7":
            if model == "res.partner.invoice":
                self.set_model_attr(backend.id, model, "ID_OFFSET", 200000000)
            elif model == "res.partner.shipping":
                self.set_model_attr(backend.id, model, "ID_OFFSET", 100000000)
        self.setup_channel_model_fields(rec)

    @api.model_cr_context
    def setup_backend_ext_model(self, backend, rec):
        model = rec.name
        if (
            self.get_struct_model_attr(model, "SKEYS")
            and self.get_struct_model_attr(model, "XPIRE")
        ):
            return
        self.setup_1_backend(backend)
        self.init_backend_model(backend.id, model)
        self.store_model_1_backend(backend, rec)
        self.CACHE.set_model_cache(self._cr.dbname, backend.id, model)

    @api.model_cr_context
    def setup_1_backend(self, backend):
        if (
            self.get_attr(backend.id, "PREFIX")
            and self.get_attr(backend.id, "XPIRE")
        ):
            return
        self.set_channel_base(backend.id)
        self.set_attr(backend.id, "PREFIX", backend.prefix)
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
        self.set_attr(backend.id, "LOGLEVEL", backend.tracelevel)
        self.CACHE.set_channel_cache(self._cr.dbname, backend.id)

    @api.model_cr_context
    def setup_channels(self, all=None):
        """If channel information are expired, read values from channel table
        and store them into memory"""
        if not len(self.get_channel_list()) or all:
            for channel in self.env["synchro.channel"].search([], order="sequence"):
                self.setup_1_backend(channel)

    @api.model_cr_context
    def setup_model_structure(self, model, actual_model):
        """Store model structure into memory"""
        actual_model = actual_model or model
        model = model or actual_model
        if not model or (self.get_struct_model_attr(model, "id")
                         and self.get_struct_model_attr(model, "XPIRE")):
            return
        IrModelFields = self.env["ir.model.fields"]
        self.set_struct_model(actual_model)
        for field in IrModelFields.search([("model", "=", actual_model)]):
            global_def = self.TABLE_DEF.get("base", {}).get(field.name, {})
            field_def = self.TABLE_DEF.get(model, {}).get(field.name, {})
            attrs = {}
            for attr in ("required", "readonly", "protect_update"):
                if attr in field_def:
                    attrs[attr] = field_def[attr]
                elif attr in global_def:
                    attrs[attr] = global_def[attr]
                elif attr == "readonly" and (
                    field.ttype in ("binary", "reference")
                    or (field.related and not field.required)
                ):
                    attrs["readonly"] = True
                else:
                    attrs[attr] = field[attr]
            if attrs["required"]:
                attrs["readonly"] = False
            if not self.is_manageable(model):
                attrs["readonly"] = True
            self.set_struct_model_attr(
                actual_model,
                field.name,
                {
                    "ttype": field.ttype,
                    "relation": field.relation,
                    "required": attrs["required"],
                    "readonly": attrs["readonly"],
                    "protect_update": attrs["protect_update"],
                },
            )
            if field.relation and field.relation != actual_model:
                if field.relation and field.relation == ("%s.line" % actual_model):
                    self.set_struct_model_attr(actual_model, "CHILD_IDS", field.name)
                    self.set_struct_model_attr(
                        actual_model, "MODEL_CHILD", field.relation
                    )
                elif (
                    actual_model.endswith(".line")
                    and field.relation
                    and actual_model.startswith(field.relation)
                ):
                    self.set_struct_model_attr(actual_model, "PARENT_ID", field.name)
                elif field.relation and actual_model.startswith(field.relation):
                    self.set_struct_model_attr(actual_model, "SUPPL_KEY", field.name)
            if field.name == "name":
                self.set_struct_model_attr(actual_model, "MODEL_WITH_NAME", True)
            elif field.name == "dim_name":
                self.set_struct_model_attr(actual_model, "MODEL_WITH_DIMNAME", True)
            elif field.name == "company_id":
                self.set_struct_model_attr(actual_model, "MODEL_WITH_COMPANY", True)
            elif field.name == "country_id":
                self.set_struct_model_attr(actual_model, "MODEL_WITH_COUNTRY", True)
        # Refresh cache
        # self.set_struct_model("_QUEUE_SYNC")
        self.CACHE.set_struct_cache(self._cr.dbname, model)

    @api.model_cr_context
    def setup_model_in_backends(self, backend, model=None, ext_model=None):
        """Read model value from all active channel model table and store
        them into memory"""
        Backend = self.env["synchro.channel.model"]
        if model:
            domain = [("name", "=", model)]
        elif ext_model:
            domain = [("counterpart_name", "=", ext_model)]
        else:
            return
        domain.append(("synchro_channel_id", "=", backend.id))
        recs = Backend.search(domain)
        if not recs and backend and backend.identity == "odoo":
            if ext_model:
                Backend.build_odoo_synchro_model(backend.id, ext_model)
            elif model:
                Backend.build_odoo_synchro_model(backend.id, None, model=model)
        for rec in Backend.search(domain):
            self.setup_backend_ext_model(backend, rec)

    @api.model_cr_context
    def open(self, backend=None, model=None, ext_model=None, cls=None):
        """Setup cache if needed, setup model cache if required and needed"""
        IrSynchroModel = self.env["ir.model.synchro"]
        if backend and backend.identity == "odoo":
            if ext_model in ("ir.model", "ir.module.module") and not model:
                model = ext_model
            elif model in ("ir.model", "ir.module.module") and not ext_model:
                ext_model = model
        actual_model = model
        if backend and ext_model and not model and backend.identity == "odoo":
            ext_odoo_ver = IrSynchroModel.get_ext_odoo_ver(backend.prefix)
            if ext_odoo_ver:
                tnldict = IrSynchroModel.get_tnldict(backend.id)
                actual_model = transodoo.translate_from_to(
                    tnldict,
                    "ir.model",
                    ext_model,
                    ext_odoo_ver,
                    release.major_version,
                    type="model",
                )
                if ext_model == actual_model:
                    ext_model = transodoo.translate_from_to(
                        tnldict,
                        "ir.model",
                        ext_model,
                        ext_odoo_ver,
                        release.major_version,
                        type="merge",
                    )
        elif model:
            actual_model = self.env["ir.model.synchro"].get_actual_model(
                model, only_name=True
            )
        if actual_model:
            self.setup_model_structure(model, actual_model)
        if backend:
            self.setup_model_in_backends(backend, model=model, ext_model=ext_model)
