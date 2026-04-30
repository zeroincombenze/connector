# -*- coding: utf-8 -*-
#
# Copyright 2019-26 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
"""
INTRODUCTION

This software provides to ability of exchange records with different
external partners we call counterparts. The synchro function returns the Odoo
id record or a error code (read below).

Synchro runs 3 steps:
1. Counterpart names are translated into local Odoo names, and the <*2many>
   records are mapped into local records.
   During the mapping process, a new synchro function on <*2many> relation
   model to bind or create a linked record. So synchro is recursive function.
2. After translation and mapping, data is used to binding local record.
   The searching is mainly based on counterpart id (read below) when matched;
   otherwise a complex finding process is engaged depending on the specific
   model structure.
3. If local Odoo record is found, the <write> is engaged otherwise the
   <create> is executed. Because counterpart can ignore the Odoo structure,
   it can issue incomplete or wrong data so the <create> can fail and breaks
   recursive chain. In order to minimize the errors, the <create> is splitted
   into a simple create followed by a write function. The <create> uses the
   minimal data required by Odoo while the <write> uses the full data supplied
   by the counterpart. In this way, the <create> should terminate quite ever
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

Imagine this scenario: Odoo exchanges "res.partner" with a counterpart called
vg7 which have 2 tables, named "customer" and "supplier". A one Odoo record
may have to link to customer record and/or the supplier record.
Also imagine that the external customer table contains shipping data which
are in a separate "res.partner" records of Odoo.
So we meet some conflicts. The first one when both "customer" and "supplier"
can have the same id (because on the counterpart there are 2 different tables)
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
| prefix     (1)| vg7         | vg7                  | vg7                  |
| bind       (2)| customer    |                      | supplier             |
| actual_model  | res.partner | res.partner          | res.partner          |
| vmodel     (3)| res.partner | res.partner.shipping | res,partner.supplier |
| loc_ext_id (4)| vg7_id      | vg7_id               | vg72_id              |
| ext_key_id (5)| id          | id                   | id                   |
| offset     (6)| 0           | 100000000            | 0                    |
+---------------+-------------+----------------------+----------------------+
(1) Prefix of every field supplied by the counterpart (this is just an example)
(2) Name of external counterpart table
(3) Odoo model, sub model of actual model
(4) Odoo field, unique key, with external partner id; default is "{prefix}_id"
(5) External partner field with the external id; default is "id"
(6) Offset to store external id, when does not exist external counterpart table

During the pre-processing to extract the shipping data from the customer data,
the shipping data is stored in the cache and then retrieved after the customer
record is written.


PROTECTION

Every field can be protect against update. There are 4 protection levels:
0 -> 'Always Update': field may be update by counterpart (default)
1 -> 'But new value not empty':
      field may be update only by not null counterpart value
2 -> 'But current value is empty': field may be update only if is null
3 -> 'Protected field': field cannot be update by counterpart
4 -> 'Counter field': field is an integer and value is the max(local,remote)


EXCHANGE MODE AND STRUCTURED MODELS

Data may be exchanged with counterpart in two ways:
1. Push mode: counterpart sends data to Odoo. It prefixes its dictionary name
2. Pull mode: Odoo gets data from the counterpart.

Parent/child models like invoice and sale order are managed in 3 ways:
A. Parent without child reference. After the parent record is written, children
   must be sent by the counterpart (push mode) or must be get from the
   counterpart (pull mode).
B. Parent contains "line_ids" field with list of children ids. In this case
   "line _ids" is extracted from the parent record during pre-processing and
   the list of children is stored in the cache.
   After the parent record is written, "line_ids" is retrieved and every id in
   the list is used to get data from the counterpart (only pull mode).
C. Header contains "line_ids" with dictionary data and operation is <create>.
   In this case data are enough to create children records too. "line_ids"
   field is changed adding "(0, 0" prefix that is the way used by Odoo itself
   to create new parent/child records.


CACHE

Data stored in cache:
- 'vg7:shipping': sub-model res.partner.shipping
- 'vg7:billing': sub-model res.partner.invoice
- '_QUEUE_SYNC': queue records
- '__{{model}}': full data of model to write the created record (read above)


LOG MESSAGES
Log message level are:
    'error': log only error messages (message in UI log)
    'info': log error and info messages
    'warning': log warning + info + error messages
    'debug': log debug + warning + info + error messages
    'any': log any message (most verbose, slow execution)
    'trace': this message is just stored in UI log

RETURN CODES

Return code:
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
  -100: if return code < -100 means error on child records
"""
import logging
import os
from datetime import date, datetime, timedelta
import time
import csv

import json
import requests
import Levenshtein as lev
from odoo import api, fields, models, _
from odoo import release
from odoo.osv import expression

_logger = logging.getLogger(__name__)
try:
    from python_plus import unicodes, _u, _b, str2bool
except ImportError as err:  # pragma: no cover
    _logger.error(err)
try:
    from unidecode import unidecode
except ImportError as err:  # pragma: no cover
    _logger.error(err)
try:
    from clodoo import transodoo
except ImportError as err:  # pragma: no cover
    _logger.error(err)
try:
    import oerplib
except ImportError as err:  # pragma: no cover
    _logger.error(err)

WORKFLOW = {
    0: {"model": "ir.module.category", "only_minimal": True},
    1: {"model": "ir.module.module"},
    2: {"model": "res.lang"},
    3: {"model": "res.country", "no_deep_fields": ["country_group_ids", "state_ids"]},
    4: {"model": "res.country.state"},
    5: {"model": "res.currency", "no_deep_fields": ["rate_ids"]},
    6: {"model": "res.groups", "only_minimal": True},
    7: {
        "model": "res.partner",
        "select": "new",
        "only_minimal": True,
        "remote_ids": "1-10",
    },
    8: {
        "model": "res.users",
        "only_minimal": True,
        "no_deep_fields": ["*", "partner_id"],
    },
    9: {"model": "res.company", "no_deep_fields": ["*", "partner_id"]},
    10: {"model": "account.account.type"},
    11: {
        "model": "account.account",
        "no_deep_fields": ["*", "company_id", "user_type_id", "tag_ids"],
    },
    12: {"model": "account.tax", "no_deep_fields": ["*", "company_id", "account_id"]},
    13: {"model": "res.bank"},
    14: {"model": "ir.sequence"},
    15: {
        "model": "account.journal",
        "no_deep_fields": [
            "*",
            "company_id",
            "currency_id",
            "default_credit_account_id",
            "default_debit_account_id",
            "sequence_id",
        ],
    },
    16: {"model": "account.payment.term"},
    17: {"model": "account.fiscal.position", "only_minimal": True},
    18: {
        "model": "res.partner",
        "no_deep_fields": [
            "*",
            "company_id",
            "category_id",
            "country_id",
            "parent_id",
            "state_id",
        ],
    },
    19: {"model": "res.partner.bank"},
    20: {"model": "product.uom"},
    21: {"model": "product.category"},
    22: {
        "model": "product.template",
        "no_deep_fields": [
            "*",
            "company_id",
            "categ_id",
            "property_account_expense_id",
            "property_account_income_id",
            "taxes_id",
            "uom_id",
            "uom_po_id",
        ],
    },
    23: {"model": "product.attribute"},
    24: {"model": "product.product"},
    25: {"model": "product.pricelist"},
    26: {"model": "product.supplierinfo"},
    27: {"model": "italy.ade.codice.carica"},
    28: {"model": "italy.ade.invoice.type"},
    29: {"model": "italy.ade.tax.nature"},
    30: {"model": "riba.configuration"},
    31: {"model": "riba.distinta"},
    32: {"model": "withholding.tax"},
    33: {"model": "stock.ddt.type"},
    34: {"model": "stock.picking.carriage_condition"},
    35: {"model": "stock.picking.goods_description"},
    36: {"model": "stock.picking.transportation_method"},
    37: {"model": "stock.picking.transportation_reason"},
    38: {
        "model": "stock.location",
        "no_deep_fields": [
            "*",
            "company_id",
            "location_id",
            "partner_id",
            "valuation_in_account_id",
            "valuation_out_account_id",
        ],
    },
    39: {
        "model": "stock.warehouse",
        "no_deep_fields": ["*", "company_id", "partner_id"],
    },
    40: {
        "model": "stock.move",
        "no_deep_fields": ["*", "company_id", "partner_id", "product_id"],
    },
    41: {
        "model": "stock.picking",
        "no_deep_fields": ["*", "company_id", "move_lines", "partner_id", "product_id"],
    },
    42: {"model": "sale.order"},
    43: {"model": "stock.picking.package.preparation"},
    44: {"model": "procurement.order"},
    45: {"model": "purchase.order"},
    46: {"model": "account.invoice"},
    47: {"model": "stock.production.lot"},
    48: {"model": "stock.quant"},
    49: {"model": "account.move"},
    50: {"model": "account.full.reconcile"},
    51: {"model": "account.partial.reconcile"},
    52: {"model": "fatturapa.attachment.in"},
    53: {"model": "fatturapa.attachment.out"},
    54: {"model": "fatturapa.attachments"},
    55: {
        "model": "account.analytic.account",
        "no_deep_fields": [
            "*",
            "company_id",
            "company_uom_id",
            "currency_id",
            "partner_id",
            "tag_ids",
        ],
    },
    56: {"model": "project.project"},
    57: {"model": "project.task"},
    58: {"model": "delivery.carrier"},
    59: {"model": "res.partner"},
    60: {"model": "account.account"},
    61: {"model": "account.tax"},
    62: {"model": "account.journal"},
    63: {"model": "account.fiscal.position"},
    64: {"model": "causale.pagamento"},
    65: {"model": "account.vat.period.end.statement"},
    66: {"model": "crm.team"},
    67: {"model": "crm.lead"},
    68: {"model": "crm.stage"},
    69: {"model": "crm.activity"},
    70: {"model": "stock.location"},
    71: {"model": "stock.warehouse"},
    72: {"model": "stock.move"},
    73: {"model": "stock.picking"},
    74: {"model": "account.analytic.account"},
    75: {"model": "res.users"},
    76: {"model": "mail.mail"},
    77: {"model": "mail.message"},
}


class IrModelSynchro(models.Model):
    _name = "ir.model.synchro"
    _inherit = "ir.model"

    LOGLEVEL = "debug"
    DEF_INCL_FLDS = [
        "action",
        "category_id",
        "code",
        "company_ids",
        "country_id",
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
    DEF_EXCL_FLDS = ["user_ids", "sale_order_ids", "meeting_ids"]

    def _build_unique_index(self, model, prefix):
        """Build unique index on table to <vg7>_id for performance"""
        if isinstance(model, (list, tuple)):    # pragma: no cover
            table = model[0].replace(".", "_")
        else:
            table = model.replace(".", "_")
        index_name = "%s_unique_%s" % (table, prefix)
        self._cr.execute(  # pylint: disable=E8103
            "SELECT indexname FROM pg_indexes WHERE indexname = '%s'" % index_name
        )
        if not self._cr.fetchone():
            self._cr.execute(  # pylint: disable=E8103
                "CREATE UNIQUE INDEX %s on %s (%s_id) "
                "where %s_id<>0 and %s_id is not null"
                % (index_name, table, prefix, prefix, prefix)
            )
        self._cr.execute(  # pylint: disable=E8103
            "UPDATE %s set %s_id=NULL where %s_id=0" % (table, prefix, prefix)
        )

    def wep_text(self, text):
        return unidecode(text).strip() if text else text

    def dim_text(self, text):
        text = self.wep_text(text)
        if text:
            res = ""
            for ch in text:
                if ch.isalnum():
                    res += ch.lower()
            text = res
        return text

    def logmsg(
        self, reqloglevel, msg_text,
        rec=None, model=None, id=None, logrec=None, ctx=None
    ):

        ctx = ctx or {}
        ctx["model"] = ctx.get("model", model or "")
        ctx["id"] = id or ctx.get("id", rec and rec.id or False)
        loglevel2num = {
            "error": "4",
            "info": "3",
            "warning": "2",
            "debug": "1",
        }
        if logrec:
            reqloglevel = "4"
        elif isinstance(reqloglevel, basestring):
            reqloglevel = loglevel2num.get(reqloglevel, "2")
        elif not reqloglevel.isdigit():
            reqloglevel = self.LOGLEVEL
        try:
            full_msg = _u(msg_text % ctx)
        except BaseException:   # pragma: no cover
            full_msg = _u(msg_text)
        if reqloglevel >= self.LOGLEVEL:
            _logger.info(full_msg)
            return self.env["ir.model.synchro.log"].logger(
                model, rec, full_msg, logrec=logrec, id=ctx["id"]
            )

    @api.model
    def create_n_commit(self, model, vals, logrec=None, context=None):
        # if model.startswith("account.move") and not context:
        #     context = {"check_move_validity": False}
        BindingModel = self.env[model]
        try:
            if context:
                rec = BindingModel.with_context(context).create(vals)
            else:
                rec = BindingModel.create(vals)
            self.logmsg(
                "warning",
                "%s.create()" % model,
                logrec=logrec,
                rec=rec,
            )
            # commit to avoid lost data in recursive write
            # self.env.cr.commit()  # pylint: disable=invalid-commit
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            rec = None
            self.logmsg("error", "ERROR %s: %s.create(%s)" % (e, model, vals))
        return rec

    @api.model
    def get_vmodel(self, model, spec):
        vmodel = model
        if model == "res.partner":
            if spec == "delivery":
                vmodel = "res.partner.shipping"
            elif spec in ("invoice", "supplier"):
                vmodel = "%s.%s" % (model, spec)
        elif model == "res.partner.bank":
            if spec == "company":
                vmodel = "res.partner.bank.company"
        return vmodel

    @api.model
    def get_actual_model(self, model, only_name=False):
        actual_model = model
        if model in (
            "res.partner.shipping",
            "res.partner.invoice",
            "res.partner.supplier",
            "res.partner.bank.company",
        ):
            actual_model = model.rsplit(".", 1)[0]
        if only_name:
            return actual_model
        return self.env[actual_model]

    @api.model
    def get_spec_from_vmodel(self, vmodel):
        if vmodel == "res.partner.shipping":
            return "delivery"
        elif vmodel in (
            "res.partner.invoice",
            "res.partner.supplier",
            "res.partner.bank.company",
        ):
            return vmodel.split(".")[-1]
        return ""

    @api.model
    def get_loc_ext_id_name(self, backend, model, spec=None, force=None):
        """Get local name for external reference
        """
        Cache = self.env["ir.model.synchro.cache"]
        vmodel = self.get_vmodel(model, spec)
        Cache.open(model=vmodel)
        if vmodel in ("res.partner.supplier", "res.partner.bank.company"):
            loc_ext_id_name = Cache.get_model_attr(
                backend.id,
                vmodel,
                "EXT_ID",
                default="%s2_id" % backend.prefix,
            )
        else:
            loc_ext_id_name = Cache.get_model_attr(
                backend.id,
                vmodel,
                "EXT_ID",
                default="%s_id" % backend.prefix,
            )
        return loc_ext_id_name

    @api.model
    def get_loc_ext_id_value(self, backend, model, ext_id, spec=None):
        Cache = self.env["ir.model.synchro.cache"]
        vmodel = self.get_vmodel(model, spec)
        Cache.open(model=vmodel)
        offset = Cache.get_model_attr(backend.id, vmodel, "ID_OFFSET", default=0)
        if ext_id < offset:
            return ext_id + offset
        return ext_id

    @api.model
    def get_actual_ext_id_value(self, backend_id, model, ext_id, spec=None):
        Cache = self.env["ir.model.synchro.cache"]
        vmodel = self.get_vmodel(model, spec)
        Cache.open(model=vmodel)
        offset = Cache.get_model_attr(backend_id, vmodel, "ID_OFFSET", default=0)
        if ext_id > offset:
            return ext_id - offset
        return ext_id

    def get_tnldict(self, backend_id):
        Cache = self.env["ir.model.synchro.cache"]
        tnldict = Cache.get_attr(backend_id, "TNL")
        if not tnldict:
            tnldict = {}
            transodoo.read_stored_dict(tnldict)
            Cache.set_attr(backend_id, "TNL", tnldict)
        return tnldict

    def get_ext_odoo_ver(self, prefix):
        return {
            "oe6": "6.1",
            "oe7": "7.0",
            "oe8": "8.0",
            "oe9": "9.0",
            "oe10:": "10.0",
            "oe11:": "11.0",
            "oe12:": "12.0",
            "oe13:": "13.0",
            "oe14:": "14.0",
        }.get(prefix.split(":")[0], "")

    def drop_fields(self, vals, to_delete):
        for name in to_delete:
            if isinstance(vals, (list, tuple)):     # pragma: no cover
                del vals[vals.index(name)]
            else:
                del vals[name]
        return vals

    def drop_invalid_fields(self, vmodel, vals):
        Cache = self.env["ir.model.synchro.cache"]
        saved_ext_id = None
        actual_model = self.get_actual_model(vmodel, only_name=True)
        if isinstance(vals, (list, tuple)):     # pragma: no cover
            to_delete = list(
                set(vals) - set(Cache.get_struct_attr(actual_model).keys())
            )
        else:
            to_delete = list(
                set(vals.keys()) - set(Cache.get_struct_attr(actual_model).keys())
            )
        if saved_ext_id:
            vals[ext_id_name] = saved_ext_id
        return self.drop_fields(vals, to_delete)

    def drop_protected_fields(self, backend, vmodel, vals, rec, no_del_child=False):
        Cache = self.env["ir.model.synchro.cache"]
        actual_model = self.get_actual_model(vmodel, only_name=True)
        loc_ext_id_name = self.get_loc_ext_id_name(backend, vmodel)
        for field in vals.copy():
            if field not in rec:    # pragma: no cover
                del vals[field]
                continue
            protect_update = max(
                int(
                    Cache.get_struct_model_field_attr(
                        actual_model, field, "protect_update", default="0"
                    )
                ),
                int(
                    Cache.get_model_field_attr(
                        backend.id, vmodel, field, "PROTECT", default="0"
                    )
                ),
            )
            if vmodel == "sale.order.line" and field == "name" and no_del_child:
                del vals[field]
            elif (
                protect_update == 3
                or (protect_update == 4
                    and rec[field] and int(vals[field]) <= int(rec[field]))
                or (protect_update == 2 and rec[field])
                or (protect_update == 1 and not vals[field])
                or (field == loc_ext_id_name
                    and not vals[field]
                    and vals[field] is not False)
            ):
                del vals[field]
            elif isinstance(vals[field], (basestring, int, long, float, bool)):
                if (
                    Cache.get_struct_model_field_attr(actual_model, field, "ttype")
                    == "many2one"
                ):
                    if (rec[field] and vals[field] == rec[field].id) or (
                            not rec[field] and not vals[field]
                    ):
                        del vals[field]
                elif vals[field] == rec[field]:
                    del vals[field]
        return vals

    def set_state_to_draft(self, struct, model, rec, vals):
        if rec:
            self.logmsg(
                "debug",
                "%(model)s[%(id)s].set_state_to_draft()", model=model, rec=rec
            )
        errc = 0
        if "state" in vals:
            vals["original_state"] = vals["state"]
        elif model == "ir.module.module":
            vals["original_state"] = "installed"
        elif rec:
            vals["original_state"] = rec.state
        if "state" in vals:
            del vals["state"]
        if rec and (rec.state in ("draft", "uninstalled")):
            return vals, errc
        if model == "account.invoice":
            if rec:
                rec.set_defaults()
                rec.compute_taxes()
                rec.write({})
                if rec.state == "paid":
                    return vals, -4
                elif rec.state == "open":
                    try:
                        rec.action_invoice_cancel()
                        rec.action_invoice_draft()
                    except BaseException as e:  # pragma: no cover
                        self.env.cr.rollback()  # pylint: disable=invalid-commit
                        self.logmsg(
                            "error",
                            "ERROR %(e)s: %(model)s.set_state_to_draft(%(id)s)",
                            model=model,
                            rec=rec,
                            logrec=self.logrec,
                            ctx={"e": e},
                        )
                elif rec.state == "cancel":
                    try:
                        rec.action_invoice_draft()
                    except BaseException as e:  # pragma: no cover
                        self.env.cr.rollback()  # pylint: disable=invalid-commit
                        self.logmsg(
                            "error",
                            "ERROR %(e)s: %(model)s.set_state_to_draft(%(id)s)",
                            model=model,
                            rec=rec,
                            logrec=self.logrec,
                            ctx={"e": e},
                        )
        elif model == "sale.order":
            if rec:
                rec.set_defaults()
                rec._compute_tax_id()
                rec.write({})
                if rec.invoice_count > 0 or rec.ddt_ids:
                    self.logmsg(
                        "error",
                        "%(model)s.set_state_to_draft(%(id)s)  # Invoiced",
                        model=model,
                        logrec=self.logrec,
                        rec=rec,
                    )
                    return vals, -4
                if rec.state == "done":
                    self.logmsg(
                        "error",
                        "%(model)s.set_state_to_draft(%(id)s)  # Locked",
                        model=model,
                        logrec=self.logrec,
                        rec=rec,
                    )
                    return vals, -4
                elif rec.state == "sale":
                    try:
                        rec.action_cancel()
                        rec.action_draft()
                    except BaseException as e:  # pragma: no cover
                        self.env.cr.rollback()  # pylint: disable=invalid-commit
                        self.logmsg(
                            "error",
                            "ERROR %(e)s: %(model)s.set_state_to_draft(%(id)s)",
                            model=model,
                            rec=rec,
                            logrec=self.logrec,
                            ctx={"e": e},
                        )
                elif rec.state == "cancel":
                    try:
                        rec.action_draft()
                    except BaseException as e:  # pragma: no cover
                        self.env.cr.rollback()  # pylint: disable=invalid-commit
                        self.logmsg(
                            "error",
                            "ERROR %(e)s: %(model)s.set_state_to_draft(%(id)s)",
                            model=model,
                            rec=rec,
                            logrec=self.logrec,
                            ctx={"e": e},
                        )
            if "state" in vals:
                del vals["state"]
        elif model == "purchase.order":
            if rec:
                rec._compute_date_planned()
                rec.write({})
                if rec.invoice_count > 0:
                    self.logmsg(
                        "error",
                        "%(model)s.set_state_to_draft(%(id)s)  # Invoiced",
                        model=model,
                        logrec=self.logrec,
                        rec=rec,
                    )
                    return vals, -4
                if rec.state == "done":
                    self.logmsg(
                        "error",
                        "%(model)s.set_state_to_draft(%(id)s)  # Locked",
                        model=model,
                        logrec=self.logrec,
                        rec=rec,
                    )
                    return vals, -4
                elif rec.state == "purchase":
                    try:
                        rec.button_cancel()
                        rec.button_draft()
                    except BaseException as e:  # pragma: no cover
                        self.env.cr.rollback()  # pylint: disable=invalid-commit
                        self.logmsg(
                            "error",
                            "ERROR %(e)s: %(model)s.set_state_to_draft(%(id)s)",
                            model=model,
                            rec=rec,
                            logrec=self.logrec,
                            ctx={"e": e},
                        )
                elif rec.state == "cancel":
                    try:
                        rec.button_draft()
                    except BaseException as e:  # pragma: no cover
                        self.env.cr.rollback()  # pylint: disable=invalid-commit
                        self.logmsg(
                            "error",
                            "ERROR %(e)s: %(model)s.set_state_to_draft(%(id)s)",
                            model=model,
                            rec=rec,
                            logrec=self.logrec,
                            ctx={"e": e},
                        )
        elif model == "stock.picking.package.preparation":
            if rec:
                if rec.invoice_ids or rec.invoice_id:
                    return vals, -4
                try:
                    rec.set_draft()
                except BaseException as e:  # pragma: no cover
                    self.env.cr.rollback()  # pylint: disable=invalid-commit
                    self.logmsg(
                        "error",
                        "ERROR %(e)s: %(model)s.set_state_to_draft(%(id)s)",
                        model=model,
                        rec=rec,
                        logrec=self.logrec,
                        ctx={"e": e},
                    )
        elif model == "account.move":
            if rec:
                if rec.state == "posted":
                    try:
                        rec.button_cancel()
                    except BaseException as e:  # pragma: no cover
                        self.env.cr.rollback()  # pylint: disable=invalid-commit
                        self.logmsg(
                            "error",
                            "ERROR %(e)s: %(model)s.set_state_to_draft(%(id)s)",
                            model=model,
                            rec=rec,
                            logrec=self.logrec,
                            ctx={"e": e},
                        )
        return vals, errc

    def set_actual_state(self, struct, model, rec):
        self.logmsg(
            "debug", "%(model)s.set_actual_state(%(id)s)", model=model, rec=rec
        )
        if not rec:
            return -3
        if model == "account.invoice":
            rec.compute_taxes()
            # Please, do not remove this write: set default values in header
            rec.write({})
            if rec.state == rec.original_state:
                return rec.id
            elif rec.state != "draft":
                self.logmsg(
                    "error",
                    "### Unauthorized state change of %(model)s[%(id)s]",
                    model=model,
                    rec=rec,
                    logrec=self.logrec,
                )
                return -4
            elif rec.original_state in ("open", "paid"):
                try:
                    rec.action_invoice_open()
                except BaseException as e:  # pragma: no cover
                    self.env.cr.rollback()  # pylint: disable=invalid-commit
                    self.logmsg(
                        "error",
                        "ERROR %(e)s: %(model)s.set_actual_state(%(id)s)",
                        model=model,
                        rec=rec,
                        logrec=self.logrec,
                        ctx={"e": e},
                    )
                    return -10
                if rec.name and rec.name.startswith("Unknown"):
                    rec.write({"name": rec.number})
            elif rec.original_state == "cancel":
                try:
                    rec.action_invoice_cancel()
                except BaseException as e:  # pragma: no cover
                    self.env.cr.rollback()  # pylint: disable=invalid-commit
                    self.logmsg(
                        "error",
                        "ERROR %(e)s: %(model)s.set_actual_state()",
                        model=model,
                        rec=rec,
                        logrec=self.logrec,
                        ctx={"e": e},
                    )
                    return -10
        elif model == "sale.order":
            # Please, do not remove this write: set default values in header
            rec.write({})
            if rec.state == rec.original_state:
                return rec.id
            elif rec.state != "draft":
                self.logmsg(
                    "error",
                    "### Unauthorized state change of %(model)s[%(id)s]",
                    model=model,
                    logrec=self.logrec,
                    rec=rec,
                )
                return -4
            elif rec.original_state == "sale":
                rec._amount_all()
                if "agents" in self.env["sale.order.line"]._fields:
                    rec._compute_commission_total()
                if (
                    hasattr(rec, "delivery_set")
                    and hasattr(rec, "carrier_id")
                    and rec.carrier_id
                ):
                    rec.delivery_set()
                try:
                    rec.action_confirm()
                except BaseException as e:  # pragma: no cover
                    self.env.cr.rollback()  # pylint: disable=invalid-commit
                    self.logmsg(
                        "error",
                        "ERROR %(e)s: %(model)s.set_actual_state(%(id)s)",
                        model=model,
                        rec=rec,
                        logrec=self.logrec,
                        ctx={"e": e},
                    )
                    return -10
            elif rec.original_state == "cancel":
                try:
                    rec.action_cancel()
                except BaseException as e:  # pragma: no cover
                    self.env.cr.rollback()  # pylint: disable=invalid-commit
                    self.logmsg(
                        "error",
                        "ERROR %(e)s: %(model)s.set_actual_state(%(id)s)",
                        model=model,
                        rec=rec,
                        logrec=self.logrec,
                        ctx={"e": e},
                    )
                    return -10
        elif model == "purchase.order":
            # Please, do not remove this write: set default values in header
            rec.write({})
            if rec.state == rec.original_state:
                return rec.id
            elif rec.state != "draft":
                self.logmsg(
                    "error",
                    "### Unauthorized state change of %(model)s[%(id)s]",
                    model=model,
                    logrec=self.logrec,
                    rec=rec,
                )
                return -4
            elif rec.original_state == "purchase":
                rec._amount_all()
                try:
                    rec.button_confirm()
                except BaseException as e:  # pragma: no cover
                    self.env.cr.rollback()  # pylint: disable=invalid-commit
                    self.logmsg(
                        "error",
                        "ERROR %(e)s: %(model)s.set_actual_state(%(id)s)",
                        model=model,
                        rec=rec,
                        logrec=self.logrec,
                        ctx={"e": e},
                    )
                    return -10
            elif rec.original_state == "cancel":
                try:
                    rec.button_cancel()
                except BaseException as e:  # pragma: no cover
                    self.env.cr.rollback()  # pylint: disable=invalid-commit
                    self.logmsg(
                        "error",
                        "ERROR %(e)s: %(model)s.set_actual_state(%(id)s)",
                        model=model,
                        rec=rec,
                        logrec=self.logrec,
                        ctx={"e": e},
                    )
                    return -10
        elif model == "stock.picking.package.preparation":
            try:
                rec.set_done()
            except BaseException as e:  # pragma: no cover
                self.env.cr.rollback()  # pylint: disable=invalid-commit
                self.logmsg(
                    "error",
                    "ERROR %(e)s: %(model)s.set_actual_state(%(id)s)",
                    model=model,
                    rec=rec,
                    logrec=self.logrec,
                    ctx={"e": e},
                )
                return -10
        elif model == "account.move":
            if rec.state == rec.original_state:
                return rec.id
            elif rec.state != "draft":
                self.logmsg(
                    "error",
                    "### Unauthorized state change of %(model)s[%(id)s]",
                    model=model,
                    logrec=self.logrec,
                    rec=rec,
                )
                return -4
            elif rec.original_state == "posted":
                try:
                    rec.post()
                except BaseException as e:  # pragma: no cover
                    self.env.cr.rollback()  # pylint: disable=invalid-commit
                    self.logmsg(
                        "error",
                        "ERROR %(e)s: %(model)s.set_actual_state(%(id)s)",
                        model=model,
                        rec=rec,
                        logrec=self.logrec,
                        ctx={"e": e},
                    )
                    return -10
        # elif model == "ir.module.module":
        #     if rec.state != "installed" and rec.original_state == "installed":
        #         return self.manage_module({"name": rec.name})
        return rec.id

    def get_model_of_channel(self, backend_id, model):
        channel_model = self.env["synchro.channel.model"].search(
            [("synchro_channel_id", "=", backend_id), ("name", "=", model)]
        )
        return channel_model[0] if channel_model else self.env["synchro.channel.model"]

    def sync_rec_from_counterparty(self, backend, model, vg7_id, only_minimal=True):
        if not vg7_id:
            self.logmsg(
                "error", "### Missing id for %(model)s counterpart request", model=model
            )
            return False
        self.logmsg(
            "debug",
            "%(model)s.sync_rec_from_counterpart(%(xid)s)",
            model=model,
            ctx={"xid": vg7_id},
        )
        vals = self.get_model_of_channel(backend.id, model).get_counterpart_response(
            self.get_actual_ext_id_value(backend.id, model, vg7_id)
        )
        if not vals:
            return False
        cls = self.env[model]
        return self.generic_synchro(
            cls, vals, channel_id=backend.id, jacket=True, only_minimal=only_minimal)

    def get_alias(self, actual_model, name, value, type=None):
        translation_model = self.env["synchro.channel.domain.translation"]
        domain = [
            ("model", "=", actual_model),
            ("key", "=", name),
            ("ext_value", "ilike", self.dim_text(value)),
        ]
        rec = translation_model.search(domain)
        if not rec:
            return value
        if rec[0].odoo_value.isdigit():
            res_id = int(rec[0].odoo_value)
            return self.env[actual_model].browse(res_id)[name]
        return rec[0].odoo_value

    def create_new_ref(
        self, backend, actual_model, key_name, value, ext_value, ctx=None, spec=None
    ):
        self.logmsg(
            "debug",
            "%(model)s.create_new_ref(%(key)s,%(id)s,%(ext_id)s)",
            model=actual_model,
            ctx={"key": key_name, "id": value, "ext_id": ext_value},
        )
        ctx = ctx or {}
        Cache = self.env["ir.model.synchro.cache"]
        vmodel = self.get_vmodel(actual_model, spec)
        loc_ext_id_name = self.get_loc_ext_id_name(backend, vmodel)
        suppl_key = Cache.get_struct_model_attr(actual_model, "SUPPL_KEY")
        cls = self.env[vmodel]
        vals = {key_name: value}
        if ext_value and loc_ext_id_name:
            vals[loc_ext_id_name] = self.get_loc_ext_id_value(
                backend, actual_model, ext_value, spec=spec
            )
        if suppl_key and key_name != suppl_key and suppl_key in ctx:
            vals[suppl_key] = ctx[suppl_key]
        if key_name == "code" and ext_value:
            vals[key_name] = "code %s" % ext_value
        if key_name != "name" and Cache.get_struct_model_attr(actual_model, "name"):
            if ext_value:
                vals["name"] = "Unknown %s" % ext_value
            else:
                vals["name"] = "%s=%s" % (key_name, value)
        if actual_model == "res.partner" and spec in ("delivery", "invoice"):
            vals["type"] = spec
        try:
            new_value = self.generic_synchro(cls, vals, chk_in_queue=True)
            if not isinstance(new_value, (int, long)) or new_value < 1:
                new_value = False
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.logmsg(
                "error",
                "ERROR %(e)s: %(model)s.synchro(%(vals)s)",
                model=vmodel,
                ctx={"e": e, "vals": vals},
            )
            new_value = False
        return new_value

    def do_search(
            self, actual_model, req_domain, only_id=None, spec=None, ext_id_name=None):
        def atomic_search(cls, domain, has_sequence):
            if has_sequence:
                res = cls.with_context(lang="it_IT").search(domain, order="sequence,id")
                if not res:
                    res = cls.search(domain, order="sequence,id")
            else:
                res = cls.with_context(lang="it_IT").search(domain)
                if not res:
                    res = cls.search(domain)
            self.logmsg(
                "debug",
                "%(model)s.do_search(%(domain)s) -> %(res)s",
                model=cls._name,
                ctx={"domain": domain, "res": [x.id for x in res] if res else []},
            )
            return res

        def exec_search(cls, domain, has_sequence, has_active):
            rec = atomic_search(cls, domain, has_sequence)
            if not rec and has_active:
                rec = atomic_search(
                    cls,
                    expression.AND([domain, [("active", "=", False)]]),
                    has_sequence,
                )
            return rec

        def reduce_domain(req_domain, req_item):
            domain = []
            do_query = False
            for item in req_domain:
                if item[0] == req_item[0]:
                    do_query = True
                    continue
                domain.append(item)
            if not do_query:
                domain = []
            return domain

        Cache = self.env["ir.model.synchro.cache"]
        cls = self.env[actual_model]
        maybe_dif = False
        has_sequence = Cache.get_struct_model_attr(actual_model, "sequence")
        has_active = Cache.get_struct_model_attr(actual_model, "active")
        if len(req_domain) == 1 and not Cache.get_struct_model_attr(
            actual_model, req_domain[0][0]
        ) and ext_id_name and ext_id_name == req_domain[0][0]:
            domain = [
                ("model", "=", actual_model),
                ("res_id", req_domain[0][1], req_domain[0][2]),
            ]
            rec = self.env["ir.model.synchro.data"].search(domain)
            if rec:
                return (
                    cls.with_context({"lang": self.env.user.lang}).browse(rec.res_id),
                    maybe_dif,
                )
            return rec, maybe_dif
        if only_id:
            return exec_search(cls, req_domain, has_sequence, has_active), maybe_dif
        domain = []
        rec = False
        if actual_model == "res.partner" and spec in ("delivery", "invoice"):
            # expression.AND accepts 2 or more tuples
            domain = expression.AND(
                [req_domain, [("type", "=", spec), ("parent_id", "!=", False)]]
            )
        elif actual_model == "account.tax":
            # expression.OR accepts only 1 tuple
            domain = expression.AND([req_domain, [("type_tax_use", "=", "sale")]])
        if domain:
            rec = exec_search(cls, domain, has_sequence, has_active)
        if not rec:
            rec = exec_search(cls, req_domain, has_sequence, has_active)
        if not rec:
            if actual_model in ("res.partner", "product.product", "product.template"):
                domain = reduce_domain(req_domain, (["company_id", "", ""]))
                if domain:
                    rec = exec_search(cls, domain, has_sequence, has_active)
        if rec:
            if not has_sequence and len(rec) > 8:
                rec = False
            elif len(rec) > 1:
                maybe_dif = True
            if rec:
                rec = rec[0]
        return rec, maybe_dif

    def get_rec_by_reference(
        self, backend, actual_model, name, value, ctx=None, mode=None, spec=None
    ):
        mode = mode or "="
        self.logmsg(
            "debug",
            "%(model)s.get_rec_by_reference(%(name)s,%(xid)s,%(m)s)",
            model=actual_model,
            ctx={"name": name, "xid": value, "m": mode},
        )
        ctx = ctx or {}
        Cache = self.env["ir.model.synchro.cache"]
        if not Cache.is_manageable(actual_model):
            return False
        counterpart_pk = Cache.get_model_attr(
            backend.id, actual_model, "KEY_ID", default="id"
        )
        key_name = Cache.get_struct_model_attr(
            actual_model, "MODEL_KEY", default="name"
        )
        if not key_name:
            return False
        suppl_key = Cache.get_struct_model_attr(actual_model, "SUPPL_KEY")
        vmodel = self.get_vmodel(actual_model, spec)
        loc_ext_id_name = self.get_loc_ext_id_name(backend, vmodel)
        domain = [(name, mode, value)]
        if name not in (counterpart_pk, loc_ext_id_name):
            if Cache.get_struct_model_attr(
                actual_model, "MODEL_WITH_COMPANY"
            ) and ctx.get("company_id"):
                domain.append(("company_id", "=", ctx["company_id"]))
            if suppl_key and ctx.get(suppl_key):
                domain.append((suppl_key, "=", ctx[suppl_key]))
        rec, maybe_dif = self.do_search(actual_model, domain, spec=spec)
        if not rec:
            if mode == "=" and name == key_name:
                return self.get_rec_by_reference(
                    backend,
                    actual_model,
                    name,
                    value,
                    ctx=ctx,
                    mode="ilike",
                    spec=spec,
                )
            elif name in ("code", "description") and Cache.get_struct_model_attr(
                actual_model, "MODEL_WITH_NAME"
            ):
                return self.get_rec_by_reference(
                    backend,
                    actual_model,
                    "name",
                    value,
                    ctx=ctx,
                    mode=mode,
                    spec=spec,
                )
        return rec

    def get_foreign_text(
        self,
        backend,
        actual_model,
        value,
        is_foreign,
        ctx=None,
        spec=None,
        no_create=None,
    ):
        logrec = self.logmsg(
            "debug",
            "%(model)s.get_foreign_text(%(xid)s)",
            model=actual_model,
            ctx={"xid": value},
        )
        if len(value.split(".")) == 2:
            try:
                return self.env.ref(value).id
            except BaseException:  # pragma: no cover
                pass
        Cache = self.env["ir.model.synchro.cache"]
        key_name = Cache.get_struct_model_attr(
            actual_model, "MODEL_KEY", default="name"
        )
        if not key_name:
            return False
        new_value = False
        rec = self.get_rec_by_reference(
            backend, actual_model, key_name, value, ctx=ctx, spec=spec
        )
        if rec:
            new_value = rec[0].id
        if not new_value and not no_create and Cache.is_manageable(actual_model):
            new_value = self.create_new_ref(
                backend, actual_model, key_name, value, False, ctx=ctx, spec=spec
            )
        self.logmsg(
            "debug", "", logrec=logrec, ctx={"id": new_value}
        )
        return new_value

    def get_foreign_ref(
        self,
        backend,
        actual_model,
        value_id,
        is_foreign,
        ctx=None,
        spec=None,
        no_create=True,
    ):
        """Value is a local ID or an external ID (is_foreign=True)"""
        Cache = self.env["ir.model.synchro.cache"]
        loc_ext_id_name = self.get_loc_ext_id_name(
            backend, actual_model, spec=spec, force=True
        )
        new_value = False
        if not value_id or value_id < 1:
            return new_value
        logrec = self.logmsg(
            "debug",
            "%(model)s.get_foreign_ref(%(xid)s,spec=%(spec)s)",
            model=actual_model,
            ctx={"xid": value_id, "spec": spec},
        )
        vmodel = self.get_vmodel(actual_model, spec)
        ext_value = value_id
        if is_foreign:
            if spec:
                value_id = self.get_loc_ext_id_value(
                    backend, actual_model, value_id, spec=spec
                )
            domain = [(loc_ext_id_name, "=", value_id)]
            rec, maybe_dif = self.do_search(actual_model, domain, only_id=True)
        else:
            domain = [("id", "=", value_id)]
            rec, maybe_dif = self.do_search(actual_model, domain, only_id=True)
        if rec and vmodel == "res.partner.shipping" and rec.parent_id:
            if (
                    rec.parent_id.street == rec.street
                    and rec.parent_id.city == rec.city
                    and rec.parent_id.zip == rec.zip
            ):
                rec = rec.parent_id
        if rec:
            if len(rec) > 1:
                self.logmsg(
                    "debug",
                    "### NO SINGLETON %(model)s[%(id)s]",
                    model=actual_model,
                    ctx={"id": value_id},
                )
            new_value = rec[0].id
        if not new_value and not no_create:
            if vmodel:
                new_value = self.sync_rec_from_counterparty(
                    backend, vmodel, ext_value)
        if not new_value and not no_create and Cache.is_manageable(vmodel):
            new_value = self.create_new_ref(
                backend,
                vmodel,
                loc_ext_id_name,
                new_value,
                ext_value,
                ctx=ctx,
                spec=spec,
            )
        self.logmsg(
            "debug",
            "",
            logrec=logrec,
            ctx={"id": new_value}
        )
        return new_value

    def get_foreign_value(
        self,
        backend,
        vmodel,
        value,
        name,
        is_foreign,
        struct,
        ctx=None,
        spec=None,
        fmt=None,
        no_create=None,
    ):
        """Value is an external ID or an external text"""
        ttype = struct[name]["type"]
        if not value:
            return value
        # VG7 wrong data
        if value == -1:
            return False
        Cache = self.env["ir.model.synchro.cache"]
        actual_model = self.get_actual_model(vmodel, only_name=True)
        relation = struct[name]["relation"]
        if not relation:
            raise RuntimeError(_("No relation for field %s of %s" % (name, vmodel)))
        logrec = self.logmsg(
            "debug",
            "%(model)s.get_foreign_value(%(name)s,%(xid)s,%(if)s,%(ty)s,%(spec)s)",
            model=relation,
            ctx={
                "name": name,
                "xid": value,
                "if": is_foreign,
                "ty": ttype,
                "spec": spec,
            },
        )
        if not spec and relation == "res.partner" and actual_model == "purchase.order":
            spec = "supplier"
        if (
                not spec
                and relation == "res.partner"
                and actual_model == "sale.order"
                and name == "partner_shipping_id"
        ):
            spec = "delivery"
        if relation == actual_model and ttype == "one2many":
            # Avoid recursive request, i.e. res.partner
            return []
        if not Cache.is_manageable(relation):
            return []
        tomany = True if ttype in ("one2many", "many2many") else False
        # TODO: channel_id
        Cache.open(backend=backend, model=relation)
        if isinstance(value, basestring):
            new_value = self.get_foreign_text(
                backend,
                relation,
                value,
                is_foreign,
                ctx=ctx,
                spec=spec,
                no_create=no_create,
            )
            if not new_value or new_value < 1:
                new_value = False
            elif tomany:
                new_value = [new_value]
        elif isinstance(value, (list, tuple)):
            new_value = []
            for loc_id in value:
                new_id = self.get_foreign_ref(
                    backend,
                    relation,
                    loc_id,
                    is_foreign,
                    ctx=ctx,
                    spec=spec,
                    no_create=no_create,
                )
                if new_id and new_id > 0:
                    new_value.append(new_id)
        else:
            new_value = self.get_foreign_ref(
                backend,
                relation,
                value,
                is_foreign,
                ctx=ctx,
                spec=spec,
                no_create=no_create,
            )
            if not new_value or new_value < 1:
                new_value = False
            elif tomany:
                new_value = [new_value]
        if fmt == "cmd" and new_value and tomany:
            new_value = [(6, 0, new_value)]
        self.logmsg(
            "debug",
            "",
            model=relation,
            logrec=logrec,
            ctx={"id": new_value, "v": value},
        )
        return new_value

    def name_from_ref(self, backend, vmodel, ext_ref):
        Cache = self.env["ir.model.synchro.cache"]
        pfx_depr = "%s_" % Cache.get_attr(backend.id, "PREFIX")
        pfx_ext = "%s:" % Cache.get_attr(backend.id, "PREFIX")
        loc_ext_id_name = self.get_loc_ext_id_name(backend, vmodel, force=True)
        counterpart_pk = Cache.get_model_attr(
            backend.id, vmodel, "KEY_ID", default="id")
        if ext_ref == loc_ext_id_name:
            # Case #1 - field is external id like <vg7_id>
            is_foreign = True
            loc_name = ext_name = ext_ref

        elif ext_ref.startswith(pfx_ext):
            # Case #3 - field like <vg7:order_id>: both name and value are
            #           of counterpart refs
            is_foreign = True
            ext_name = ext_ref.split(":", 1)[1].strip()
            if ext_name == counterpart_pk and loc_ext_id_name:
                loc_name = loc_ext_id_name
            else:
                loc_name = Cache.get_model_field_attr(
                    backend.id, vmodel, ext_name, "EXT_FIELDS", default=""
                )
            if loc_name.startswith("."):
                loc_name = ""

        elif ext_ref.startswith(pfx_depr):
            # Case #2 - (deprecated) field like <vg7_order_id>:
            #           local name is odoo but value id is of counterpart ref
            is_foreign = True
            loc_name = ext_ref[len(pfx_depr):]
            if loc_name == "id":
                loc_name = ext_name = ext_ref
            else:
                ext_name = Cache.get_model_field_attr(
                    backend.id, vmodel, loc_name, "LOC_FIELDS", default=""
                )
                if ext_name.startswith("."):
                    ext_name = ""
            self.logmsg(
                "warning", "### Deprecated field name %(id)s!", ctx={"id": ext_ref}
            )

        else:
            # Case #4 - field and value are Odoo
            is_foreign = False
            if ext_ref.startswith(":"):
                ext_name = loc_name = ext_ref[1:]
            else:
                ext_name = loc_name = ext_ref
        return ext_name, loc_name, is_foreign

    def declared_default_n_apply(
        self, backend, vmodel, loc_name, ext_name, is_foreign, ttype=None
    ):
        Cache = self.env["ir.model.synchro.cache"]
        actual_model = self.get_actual_model(vmodel, only_name=True)
        if not Cache.get_attr(backend.id, actual_model):
            # TODO: channel_id
            Cache.open(backend, model=actual_model)
        default = Cache.get_model_field_attr(
            backend.id, vmodel, loc_name or ".%s" % ext_name, "APPLY", default=""
        )
        if not default:
            default = Cache.get_model_field_attr(
                backend.id,
                actual_model,
                loc_name or ".%s" % ext_name,
                "APPLY",
                default="",
            )
        if default.endswith("()"):
            apply4 = ",".join(["apply_%s" % fct[:-2]for fct in default.split(",")])
            default = False
        elif default:
            apply4 = "apply_set_value"
        else:
            apply4 = ""
        if ttype == "boolean":
            default = str2bool(default, True)
        spec = Cache.get_model_field_attr(
            backend.id, vmodel, loc_name or ".%s" % ext_name, "SPEC", default=""
        )
        return default, apply4, spec

    def found_ref_in_queue(self, vmodel, vals, ext_ref):
        self.logmsg(
            "warning",
            "### Found %(model)s(%(xid)s) in queue!",
            model=vmodel,
            ctx={"xid": vals[ext_ref]},
        )
        return True

    def drop_unuset_addresses(self, loc_id):
        for rec in self.env["res.partner"].search(
            [
                ("name", "=", False),
                ("parent_id", "=", loc_id),
                ("type", "in", ("delivery", "invoice")),
            ]
        ):
            if not rec.invoice_ids and not rec.sale_order_ids:
                try:
                    rec.unlink()
                    # self.env.cr.commit()  # pylint: disable=invalid-commit
                except BaseException:  # pragma: no cover
                    self.env.cr.rollback()  # pylint: disable=invalid-commit
                    break

    def compare_vals_rec(self, vals, rec, spec):
        diff = False
        fields = (
            "street",
            "zip",
            "city",
        ) if spec == "delivery" else (
            "street",
            "zip",
            "city",
            "state_id",
            "email",
            "country_id",
            "phone",
        )
        for nm in fields:
            if nm.endswith("_id"):
                if getattr(rec, nm) and getattr(rec, nm).id != vals.get(nm, 0):
                    diff = True
                    break
            else:
                if getattr(rec, nm) and getattr(rec, nm) != vals.get(nm, False):
                    diff = True
                    break
        return diff

    def diff_parent(self, vals, spec, rec=None):
        parent = rec or (self.env["res.partner"].browse(vals["parent_id"])
                         if "parent_id" in vals else rec)
        return self.compare_vals_rec(vals, parent, spec) if parent else False

    def translate_from_to(
            self, tnldict, vmodel, src_value, ext_odoo_ver, fld_name=None):
        value = _u(
            transodoo.translate_from_to(
                tnldict,
                vmodel,
                src_value,
                ext_odoo_ver,
                release.major_version,
                type="value",
                fld_name=fld_name,
            )
        )
        if isinstance(value, (list, tuple)):
            best = False
            near = 1999999999
            if isinstance(src_value, basestring):
                src_value = src_value.lower()
            for nm in value:
                if isinstance(nm, basestring):
                    dist = lev.distance(nm.lower(), src_value)
                    if dist < near:
                        best = nm
                        near = dist
            if best and near < 8:
                value = best
        return value

    def map_to_internal(
        self, struct, backend, vmodel, vals, no_deep_fields=None, only_minimal=None
    ):
        def rm_ext_value(vals, loc_name, ext_name, ext_ref, is_foreign):
            if (
                ext_ref in vals
                and loc_name
                and loc_name not in vals
                and (is_foreign or loc_name != ext_name or (ext_ref.startswith(":")))
            ):
                vals[loc_name] = vals[ext_ref]
            if ext_ref in vals and loc_name != ext_ref:
                del vals[ext_ref]
            if (
                loc_name in vals
                and vals[loc_name] is False
                and struct[loc_name]["type"] != "boolean"
            ):
                del vals[loc_name]
            if loc_name in ctx and vals.get(loc_name):
                ctx[loc_name] = vals[loc_name]
            return vals

        def do_apply(
            backend,
            vals,
            loc_name,
            ext_ref,
            loc_ext_id_name,
            apply4,
            default,
            vmodel,
            ctx=None,
        ):
            ir_apply = self.env["ir.model.synchro.apply"]
            for fct in apply4.split(","):
                if fct == "apply_odoo_migrate":
                    ext_odoo_ver = self.get_ext_odoo_ver(ext_ref.split(":")[0])
                    tnldict = self.get_tnldict(backend.id)
                    if ext_odoo_ver:
                        vals[loc_name] = self.translate_from_to(
                            tnldict, vmodel, vals[ext_ref], ext_odoo_ver,
                            fld_name=loc_name)
                    else:
                        vals[loc_name] = vals[ext_ref]
                elif hasattr(ir_apply, fct):
                    vals = getattr(ir_apply, fct)(
                        backend,
                        vals,
                        loc_name,
                        ext_ref,
                        loc_ext_id_name,
                        vmodel,
                        default=default,
                    )
            return vals

        def priority_fields(struct, backend, vals, loc_ext_id, vmodel):
            Cache = self.env["ir.model.synchro.cache"]
            ctx = Cache.get_attr(backend.id, "CTX") or {}
            child_ids = Cache.get_struct_model_attr(
                actual_model, "CHILD_IDS", default=False
            )
            fields = vals.keys()
            for k, v in Cache.get_model_attr(backend.id, vmodel, "LOC_FIELDS").items():
                if v == "id" or k == "id":
                    continue
                key = backend.prefix + ":" + v if v and not v.startswith(
                    ".") else ":" + k
                if key not in fields:
                    fields.append(key)
            list1 = []
            list2 = []
            list3 = []
            list6 = []
            list8 = []
            list9 = []

            for ext_ref in fields:
                if not Cache.is_struct(ext_ref):
                    continue
                ext_name, loc_name, is_foreign = self.name_from_ref(
                    backend, vmodel, ext_ref
                )
                default, apply4, spec = self.declared_default_n_apply(
                    backend,
                    vmodel,
                    loc_name,
                    ext_name,
                    is_foreign,
                    ttype=Cache.get_struct_model_field_attr(
                        actual_model, ext_name, "ttype"
                    ),
                )
                if (
                        apply4 and apply4.startswith("apply_merge_")
                        and isinstance(vals.get(ext_ref), dict)
                ):
                    vals = do_apply(
                        backend,
                        vals,
                        loc_name,
                        ext_ref,
                        loc_ext_id_name,
                        apply4,
                        default,
                        vmodel,
                        ctx=ctx,
                    )
                    if ext_ref in vals:
                        del vals[ext_ref]
                    return vals

            for ext_ref in fields:
                ext_name, loc_name, is_foreign = self.name_from_ref(
                    backend, vmodel, ext_ref
                )
                if loc_name in (loc_ext_id, "id"):
                    list1.append(ext_ref)
                elif loc_name in ("country_id", "company_id"):
                    list2.append(ext_ref)
                elif loc_name in (
                        "partner_id",
                        "street",
                ):
                    list3.append(ext_ref)
                elif loc_name in (
                    "is_company",
                    "product_uom",
                    "partner_invoice_id",
                    "partner_shipping_id",
                    "electronic_invoice_subjected",
                    "category_id",
                ):
                    list8.append(ext_ref)
                elif loc_name in (
                        child_ids,
                        "firstname",
                        "lastname",
                        "fiscal_position_id",
                        "carriage_condition_id",
                        "goods_description_id",
                        "payment_term_id",
                        "pricelist_id",
                        "transportation_method_id",
                ):
                    list9.append(ext_ref)
                else:
                    list6.append(ext_ref)
            return list1 + list2 + list3 + list6 + list8 + list9

        def check_4_double_field_id(vals):
            for nm, nm_id in (
                ("vg7:country", "vg7:country_id"),
                ("vg7:region", "vg7:region_id"),
                ("vg7_um", "vg7:um_id"),
                ("vg7:tax_id", "vg7:tax_code_id"),
                ("vg7:payment", "vg7:payment_id"),
            ):
                if not vals.get(nm_id) and vals.get(nm):
                    vals[nm_id] = vals[nm]
                    self.logmsg(
                        "warning",
                        "### Field <%(nm)s> renamed to <%(new)s>",
                        ctx={"nm": nm, "new": nm_id},
                    )
                elif vals.get(nm_id) and vals.get(nm):
                    self.logmsg(
                        "warning",
                        "### Field <%(nm)s> overtaken by <%(new)s>",
                        ctx={"nm": nm, "new": nm_id},
                    )
                    del vals[nm]
            return vals

        def cast_type(vals, actual_model, loc_name, ext_ref, struct):
            if ext_ref in vals:
                if (
                    struct[loc_name]["type"] in (
                        "many2one", "one2many", "many2many", "integer")
                    and isinstance(vals[ext_ref], basestring)
                    and (vals[ext_ref].isdigit() or vals[ext_ref] == "-1")
                ):
                    vals[ext_ref] = int(vals[ext_ref])
                elif (
                    struct[loc_name]["type"] == "boolean"
                    and isinstance(vals[ext_ref], basestring)
                ):
                    vals[ext_ref] = str2bool(vals[ext_ref], True)
                elif (
                    struct[loc_name]["type"] in ("float", "monetary")
                    and isinstance(vals[ext_ref], basestring)
                ):
                    vals[ext_ref] = eval(vals[ext_ref].replace(",", "."))
            return vals

        Cache = self.env["ir.model.synchro.cache"]
        actual_model = self.get_actual_model(vmodel, only_name=True)
        loc_ext_id_name = self.get_loc_ext_id_name(backend, vmodel)
        counterpart_pk = Cache.get_model_attr(
            backend.id, vmodel, "KEY_ID", default="id")
        child_ids = Cache.get_struct_model_attr(
            actual_model, "CHILD_IDS", default=False
        )
        model_child = Cache.get_struct_model_attr(actual_model, "MODEL_CHILD")
        parent_child_mode = "A" if child_ids and model_child else ""
        vals = check_4_double_field_id(vals)
        field_list = priority_fields(
            struct, backend, vals, loc_ext_id_name, vmodel
        )
        if isinstance(field_list, dict):
            return self.map_to_internal(
                struct, backend, vmodel, field_list,
                no_deep_fields=no_deep_fields, only_minimal=only_minimal)

        ctx = Cache.get_attr(backend.id, "CTX") or {}
        ctx["ext_key_id"] = counterpart_pk
        # ref_in_queue = False
        for ext_ref in field_list:
            if not Cache.is_struct(ext_ref):
                continue
            ext_name, loc_name, is_foreign = self.name_from_ref(
                backend, vmodel, ext_ref
            )

            if loc_name == "company_id" and ctx.get("company_id"):
                vals[loc_name] = ctx["company_id"]
                vals = rm_ext_value(vals, loc_name, ext_name, ext_ref, is_foreign)
                continue

            default, apply4, spec = self.declared_default_n_apply(
                backend,
                vmodel,
                loc_name,
                ext_name,
                is_foreign,
                ttype=Cache.get_struct_model_field_attr(
                    actual_model, ext_name, "ttype"
                ),
            )

            if not loc_name or loc_name not in struct:
                if is_foreign and apply4:
                    vals = do_apply(
                        backend,
                        vals,
                        loc_name,
                        ext_ref,
                        loc_ext_id_name,
                        apply4,
                        default,
                        vmodel,
                        ctx=ctx,
                    )
                vals = rm_ext_value(vals, loc_name, ext_name, ext_ref, is_foreign)
                continue

            if ext_ref in vals and isinstance(vals[ext_ref], basestring):
                vals[ext_ref] = vals[ext_ref].strip()
                if vals[ext_ref]:
                    vals[ext_ref] = self.get_alias(
                        actual_model, loc_name, vals[ext_ref],
                        type=struct[loc_name]["type"])

            vals = cast_type(vals, actual_model, loc_name, ext_ref, struct)
            if apply4:
                vals = do_apply(
                    backend,
                    vals,
                    loc_name,
                    ext_ref,
                    loc_ext_id_name,
                    apply4,
                    default,
                    vmodel,
                    ctx=ctx,
                )

            if not vals.get(ext_ref):
                vals = rm_ext_value(vals, loc_name, ext_name, ext_ref, is_foreign)
                continue

            if loc_name == child_ids:
                lines = []
                for num, item in enumerate(vals[ext_ref]):
                    sequence = num + 1
                    if backend.renum_lines:
                        item[":sequence"] = sequence
                    lines.append(item)
                Cache.set_model_attr(
                    backend.id, vmodel, "__%s_ids" % actual_model, lines
                )
                parent_child_mode = "B"
                del vals[ext_ref]
                continue

            if is_foreign:
                if loc_name in (loc_ext_id_name, "id"):
                    # Field like <vg7_id> with external ID in local DB
                    if loc_name in vals:
                        vals[loc_name] = self.get_loc_ext_id_value(
                            backend, vmodel, vals[loc_name]
                        )
                    else:
                        vals[ext_ref] = self.get_loc_ext_id_value(
                            backend, vmodel, vals[ext_ref]
                        )
                    vals = rm_ext_value(vals, loc_name, ext_name, ext_ref, is_foreign)
                    continue

                if loc_name in vals:
                    # If counterpart partner supplies both
                    # local and external values, just process local value
                    vals = rm_ext_value(vals, loc_name, ext_name, ext_ref, is_foreign)
                    continue

                if ext_ref in vals and struct[loc_name]["type"] in (
                        "many2one",
                        "one2many",
                        "many2many",
                ):
                    if (
                        isinstance(no_deep_fields, (list, tuple))
                        and len(no_deep_fields)
                        and "*" in no_deep_fields
                    ):
                        condition = "include"
                    else:
                        condition = "exclude"
                    if (
                        (condition == "include" and loc_name not in no_deep_fields)
                        or (condition == "exclude" and loc_name in no_deep_fields)
                    ):
                        if ext_ref in vals:
                            del vals[ext_ref]
                        continue
                    loc_id = self.get_foreign_value(
                        backend,
                        vmodel,
                        vals[ext_ref],
                        loc_name,
                        is_foreign,
                        struct,
                        ctx=ctx,
                        spec=spec,
                        fmt="cmd",
                    )
                    if isinstance(loc_id, (tuple, list)):
                        vals[loc_name] = loc_id
                    elif loc_id > 0:
                        vals[loc_name] = loc_id
                    elif loc_name:
                        vals[loc_name] = False
            vals = rm_ext_value(
                vals, loc_name, ext_name, ext_ref, is_foreign)

        prefix = self.env["ir.model.synchro.cache"].get_attr(backend.id, "PREFIX")
        for loc_name in vals.copy().keys():
            if loc_name.startswith(":"):
                vals[loc_name[1:]] = vals[loc_name]
                del vals[loc_name]
            elif loc_name.split(":", 1)[0] == prefix:
                del vals[loc_name]
        for loc_name in ctx:
            if loc_name not in vals and loc_name in Cache.get_struct_attr(actual_model):
                vals[loc_name] = ctx[loc_name]
        ctx.update(Cache.get_attr(backend.id, "CTX"))
        if "ext_key_id" in ctx:
            del ctx["ext_key_id"]
        Cache.set_attr(backend.id, "CTX", ctx)
        return vals, parent_child_mode

    def set_default_values(self, cls, backend, vmodel, vals):
        # backend_id = backend.id
        actual_model = self.get_actual_model(vmodel, only_name=True)
        IrApply = self.env["ir.model.synchro.apply"]
        Cache = self.env["ir.model.synchro.cache"]
        loc_ext_id_name = self.get_loc_ext_id_name(backend, vmodel)
        suppl_key = Cache.get_struct_model_attr(actual_model, "SUPPL_KEY")
        for field in Cache.get_struct_attr(actual_model).keys():
            if not Cache.is_struct(field):
                continue
            ext_name, loc_name, is_foreign = self.name_from_ref(
                backend, vmodel, field
            )
            if loc_name not in vals:
                if loc_name in Cache.get_model_attr(backend.id, vmodel, "LOC_FIELDS"):
                    ttype = Cache.get_struct_model_field_attr(
                        actual_model, loc_name, "ttype"
                    )
                    ext_name = Cache.get_model_field_attr(
                        backend.id, vmodel, loc_name, "LOC_FIELDS"
                    )
                    default, apply4, spec = self.declared_default_n_apply(
                        backend, vmodel, loc_name, ext_name, is_foreign, ttype=ttype
                    )
                    required = Cache.get_struct_model_field_attr(
                        actual_model, field, "required"
                    ) or Cache.get_model_field_attr(
                        backend.id, vmodel, loc_name, "REQUIRED"
                    )
                    if required or ext_name.startswith("."):
                        fcts = apply4.split(",")
                        if required:
                            if ttype == "char" and "apply_set_tmp_name" not in fcts:
                                fcts.append("apply_set_tmp_name")
                            elif (
                                loc_name in (suppl_key, "company_id", "country_id")
                                and "apply_get_global" not in fcts
                            ):
                                fcts.append("apply_get_global")
                        src = field
                        for fct in fcts:
                            if hasattr(IrApply, fct):
                                vals = getattr(IrApply, fct)(
                                    backend.id,
                                    vals,
                                    loc_name,
                                    src,
                                    loc_ext_id_name,
                                    vmodel,
                                    default=default,
                                    ctx=Cache.get_attr(backend.id, "CTX"),
                                )
                                src = field
        if hasattr(cls, "assure_values"):
            vals = cls.assure_values(vals, None)
        return vals

    def load_min_vals(self, backend, vmodel, vals, ext_id_name, ext_id):
        actual_model = self.get_actual_model(vmodel, only_name=True)
        Cache = self.env["ir.model.synchro.cache"]
        min_vals = (
            {ext_id_name: ext_id} if vals.get(ext_id_name) else {}
        )
        for loc_name in Cache.get_struct_attr(actual_model).keys():
            if loc_name in Cache.get_model_attr(backend.id, vmodel, "LOC_FIELDS"):
                required = Cache.get_struct_model_field_attr(
                    actual_model, loc_name, "required"
                ) or Cache.get_model_field_attr(
                    backend.id, vmodel, loc_name, "REQUIRED"
                )
                if required or loc_name in self.DEF_INCL_FLDS and loc_name in vals:
                    min_vals[loc_name] = vals[loc_name]
        return min_vals

    def bind_record(self, struct, backend, vmodel, vals, constraints, ctx=None):
        def add_constraints(domain, constraints):
            for constr in constraints:
                add_domain = False
                if constr[0] in vals:
                    constr[0] = vals[constr[0]]
                    add_domain = True
                if constr[-1] in vals:
                    constr[-1] = vals[constr[-1]]
                    add_domain = True
                if add_domain:
                    domain.append(constr)
            return domain

        Cache = self.env["ir.model.synchro.cache"]
        ctx = ctx or {}
        actual_model = self.get_actual_model(vmodel, only_name=True)
        spec = self.get_spec_from_vmodel(vmodel)
        spec = spec if spec != "supplier" else ""
        if actual_model == "res.partner" and spec in ("delivery", "invoice"):
            ctx["type"] = spec
        self.logmsg(
            "debug",
            "%(model)s.bind_record(%(x)s)",
            model=vmodel,
            ctx={"x": Cache.get_struct_model_attr(actual_model, "SKEYS") or []},
        )
        loc_ext_id_name = self.get_loc_ext_id_name(backend, vmodel)
        if loc_ext_id_name:
            use_sync = Cache.get_struct_model_attr(actual_model, loc_ext_id_name)
        else:
            use_sync = False
        rec = False
        candidate = False
        if loc_ext_id_name in vals:
            domain = [
                (
                    loc_ext_id_name,
                    "=",
                    self.get_loc_ext_id_value(
                        backend, vmodel, vals[loc_ext_id_name]
                    ),
                )
            ]
            rec, maybe_dif = self.do_search(
                actual_model, domain,
                only_id=True, ext_id_name=loc_ext_id_name)
            if len(rec) > 1:
                self.logmsg(
                    "warning",
                    "### WRONG INDEX %(model)s[%(id)s]",
                    model=actual_model,
                    ctx={"id": loc_ext_id_name},
                )
        if not rec and vmodel in ("res.partner.shipping",
                                  "res.partner.invoice"):
            return -9, None
        if not rec:
            parent_id_name = Cache.get_struct_model_attr(actual_model, "PARENT_ID")
            found_valid_key = True if parent_id_name else False
            for keys in Cache.get_struct_model_attr(actual_model, "SKEYS") or []:
                domain = []
                valid_domain = False
                if isinstance(keys, basestring):
                    keys = [keys]
                for key in keys:
                    if key not in vals:
                        if key == "dim_name" and vals.get("name"):
                            if vmodel in ("res.partner.shipping",
                                          "res.partner.invoice"):
                                domain.append(
                                    ("commercial_company_name", "ilike", vals["name"])
                                )
                            else:
                                domain.append(
                                    ("dim_name", "=", self.dim_text(vals["name"]))
                                )
                        elif key in ctx:
                            domain.append((key, "=", ctx[key]))
                        else:
                            domain = []
                            break
                    elif (
                            isinstance(vals[key], basestring)
                            and vals[key] == ""
                    ):
                        domain.append("|")
                        domain.append((key, "=", False))
                        domain.append((key, "=", ""))
                    elif (
                            key == "amount"
                            and isinstance(vals[key], basestring)
                            and not eval(vals[key])
                    ):
                        domain = []
                        break
                    elif key == "amount" and not vals[key]:
                        domain = []
                        break
                    else:
                        domain.append((key, "=", _b(vals[key])))
                        if key not in ("type", "is_company"):
                            valid_domain = True
                if domain and valid_domain:
                    found_valid_key = True
                    domain = add_constraints(domain, constraints)
                    if loc_ext_id_name and loc_ext_id_name in vals and use_sync:
                        domain.append("|")
                        domain.append((loc_ext_id_name, "=", False))
                        domain.append((loc_ext_id_name, "=", 0))
                    rec, maybe_dif = self.do_search(actual_model, domain, spec=spec)
                    if rec:
                        break
                    if maybe_dif and not candidate:
                        candidate = rec
        if not rec and candidate:
            rec = candidate
        if rec:
            if len(rec) > 1:
                self.logmsg(
                    "warning",
                    "### synchro error: multiple %(model)s[%(id)s]",
                    model=actual_model,
                    rec=rec[0],
                )
                return rec[0].id, rec[0]
            else:
                self.logmsg(
                    "warning",
                    "%(model)s[%(id)s].bind_record()",
                    model=actual_model,
                    rec=rec,
                )
            return rec.id, rec
        return -9 if found_valid_key else -7, None

    def get_xmlrpc_response(
        self, backend_id, vmodel, ext_id=False, select=None, mode=None
    ):
        def default_params():
            return "xmlrpc", 8069, "demo", "admin", "admin"

        def parse_endpoint(endpoint, login=None, port=None):
            protocol, def_port, db, user, passwd = default_params()
            login = login or user
            port = port or def_port
            if endpoint:
                if len(endpoint.split("@")) == 2:
                    login = endpoint.split("@")[0]
                    endpoint = endpoint.split("@")[1]
                if len(endpoint.split(":")) == 2:
                    port = int(endpoint.split(":")[1])
                    endpoint = endpoint.split(":")[0]
            return protocol, endpoint, port, login

        def xml_connect(endpoint, protocol=None, port=None):
            cnx = Cache.get_attr(backend_id, "CNX")
            if not cnx:
                prot, endpoint, def_port, login = parse_endpoint(endpoint)
                protocol = protocol or prot
                port = port or def_port
                try:
                    cnx = oerplib.OERP(server=endpoint, protocol=protocol, port=port)
                    Cache.set_attr(backend_id, "CNX", cnx)
                except BaseException:  # pragma: no cover
                    self.env.cr.rollback()  # pylint: disable=invalid-commit
                    cnx = False
            return cnx

        def xml_login(cnx, endpoint, db=None, login=None, passwd=None):
            session = Cache.get_attr(backend_id, "SESSION")
            if not session:
                login = login or self.env.user.login
                prot, endpoint, port, user = parse_endpoint(endpoint)
                db = db or "demo"
                passwd = passwd or "admin"
                login = login or user
                try:
                    session = cnx.login(database=db, user=login, passwd=passwd)
                    Cache.set_attr(backend_id, "SESSION", session)
                except BaseException:  # pragma: no cover
                    self.env.cr.rollback()  # pylint: disable=invalid-commit
                    session = False
            return cnx, session

        def connect_params():
            protocol, port, db, login, passwd = default_params()
            endpoint = Cache.get_attr(backend_id, "COUNTERPART_URL")
            db = Cache.get_attr(backend_id, "CLIENT_KEY")
            passwd = Cache.get_attr(backend_id, "PASSWORD")
            protocol, endpoint, port, login = parse_endpoint(endpoint)
            return protocol, endpoint, port, db, login, passwd

        def rpc_session():
            cnx = Cache.get_attr(backend_id, "CNX")
            session = Cache.get_attr(backend_id, "SESSION")
            tnldict = self.get_tnldict(backend_id)
            if cnx and session:
                return cnx, session, tnldict
            prot, endpoint, port, db, login, passwd = connect_params()
            if not endpoint:
                self.logmsg(
                    "error",
                    "Channel %(chid)s without connection parameters!",
                    ctx={"chid": backend_id},
                )
                return False, False, tnldict
            cnx, session = xml_login(
                xml_connect(endpoint, protocol=prot, port=port),
                endpoint,
                db=db,
                login=login,
                passwd=passwd,
            )
            if not cnx:
                self.logmsg("warning", "Not response from %(ep)s", ctx={"ep": endpoint})
            elif not session:
                self.logmsg(
                    "info",
                    "Login response error (%(db)s,%(login)s,%(pwd)s)",
                    ctx={"db": db, "login": login, "pwd": passwd},
                )
            return cnx, session, tnldict

        def expand_many(rec, ext_field, vals):
            try:
                vals[ext_field] = [x.id for x in rec[ext_field]]
            except BaseException:
                if ext_field in vals:
                    del vals[ext_field]
            return vals

        def browse_rec(cache, actual_model, ext_id, tnldict):
            try:
                rec = cnx.browse(actual_model, ext_id)
            except BaseException:
                rec = False
            prefix = cache.get_attr(backend_id, "PREFIX")
            ext_odoo_ver = self.get_ext_odoo_ver(prefix)
            vals = {}
            if rec:
                for field in cache.get_struct_attr(actual_model):
                    if ext_odoo_ver:
                        ext_field = self.translate_from_to(
                            tnldict, actual_model, field, ext_odoo_ver)
                    else:
                        ext_field = field
                    if field in ("id", "state") or (
                        hasattr(rec, ext_field)
                        and cache.is_struct(field)
                        and not cache.get_struct_model_field_attr(
                            actual_model, field, "readonly"
                        )
                    ):
                        if isinstance(rec[ext_field], (bool, int, long)):
                            vals[ext_field] = rec[ext_field]
                        elif (
                            cache.get_struct_model_field_attr(
                                actual_model, field, "ttype"
                            )
                            == "many2one"
                        ):
                            try:
                                vals[ext_field] = rec[ext_field].id
                            except BaseException:
                                vals[ext_field] = rec[ext_field]
                        elif cache.get_struct_model_field_attr(
                            actual_model, field, "ttype"
                        ) in ("one2many", "many2many"):
                            vals = expand_many(rec, ext_field, vals)
                        elif isinstance(rec[ext_field], basestring):
                            vals[ext_field] = (
                                rec[ext_field].encode("utf-8").decode("utf-8")
                            )
                        else:
                            vals[ext_field] = rec[ext_field]
                if vals:
                    vals["id"] = ext_id
            return vals

        self.logmsg(
            "debug",
            "%(model)s.get_xmlrpc_response(ch=%(chid)s,%(xid)s,%(sel)s):",
            model=vmodel,
            ctx={"chid": backend_id, "xid": ext_id, "sel": select},
        )
        Cache = self.env["ir.model.synchro.cache"]
        cnx, session, tnldict = rpc_session()
        actual_model = self.get_actual_model(vmodel, only_name=True)
        if ext_id:
            if mode:
                return cnx.search(actual_model, [(mode, "=", ext_id)])
            return browse_rec(Cache, actual_model, ext_id, tnldict)
        else:
            try:
                ids = cnx.search(actual_model, [])
            except BaseException:
                ids = []
            return ids
        return {}

    def get_json_response(self, backend_id, vmodel, ext_id=False, mode=None):
        def sort_data(datas):
            # Single record
            if "id" in datas:
                return datas
            ixs = {}
            for item in datas:
                if isinstance(item, dict):
                    id = item.get("id")
                    if not id:
                        return datas
                    ixs[int(id)] = item
            datas = []
            for id in sorted(ixs.keys()):
                datas.append(ixs[id])
            return datas

        self.logmsg(
            "debug",
            "%(model)s.get_json_response(%(chid)s,%(xid)s):",
            model=vmodel,
            ctx={"chid": backend_id, "xid": ext_id},
        )
        Cache = self.env["ir.model.synchro.cache"]
        endpoint = Cache.get_attr(backend_id, "COUNTERPART_URL")
        if not endpoint:
            self.logmsg(
                "error",
                "Channel %(chid)s without connection parameters!",
                ctx={"chid": backend_id},
            )
            return False
        ext_model = Cache.get_model_attr(backend_id, vmodel, "BIND")
        if not ext_model:
            _logger.error("Model %s not managed by external partner!" % vmodel)
            return False
        if not ext_id:
            url = os.path.join(endpoint, ext_model)
        else:
            url = os.path.join(endpoint, ext_model, str(ext_id))
        headers = {
            "Authorization": "access_token %s"
            % Cache.get_attr(backend_id, "CLIENT_KEY")
        }
        self.logmsg(
            "warning",
            "%(model)s.vg7_requests(%(url)s,%(hdr)s):",
            model=vmodel,
            ctx={"url": url, "hdr": headers},
        )
        try:
            response = requests.get(url, headers=headers, verify=False)
        except BaseException:
            response = False
        if response:
            datas = sort_data(response.json())
            return datas
        self.logmsg(
            "warning",
            "Response error %(sts)s (%(chid)s,%(url)s,%(key)s,%(pfx)s)",
            model=vmodel,
            ctx={
                "sts": getattr(response, "status_code", "N/A"),
                "chid": backend_id,
                "url": url,
                "key": Cache.get_attr(backend_id, "CLIENT_KEY"),
                "pfx": Cache.get_attr(backend_id, "PREFIX"),
            },
        )
        # Cache.clean_cache(backend_id=backend_id, model=vmodel)
        return {}

    def get_csv_response(self, backend_id, vmodel, ext_id=False, mode=None):
        self.logmsg(
            "debug",
            "%(model)s.get_csv_response(%(chid)s,%(xid)s):",
            model=vmodel,
            ctx={"chid": backend_id, "xid": ext_id},
        )
        Cache = self.env["ir.model.synchro.cache"]
        endpoint = Cache.get_attr(backend_id, "EXCHANGE_PATH")
        if not endpoint:
            self.logmsg(
                "error",
                "Channel %(chid)s without connection parameters!",
                ctx={"chid": backend_id},
            )
            return False
        ext_model = Cache.get_model_attr(backend_id, vmodel, "BIND")
        counterpart_pk = Cache.get_model_attr(
            backend_id, vmodel, "KEY_ID", default="id")
        if not ext_model:
            _logger.error("Model %s not managed by external partner!" % vmodel)
            return False
        file_csv = os.path.expanduser(os.path.join(endpoint, ext_model + ".csv"))
        self.logmsg(
            "warning",
            "%(model)s.csv_requests(%(csv)s)",
            model=vmodel,
            ctx={"csv": file_csv},
        )
        res = []
        if not os.path.isfile(file_csv):
            return res
        with open(file_csv, "rb") as fd:
            hdr = False
            reader = csv.DictReader(fd, fieldnames=[], restkey="undef_name")
            for line in reader:
                row = line["undef_name"]
                if not hdr:
                    row_id = 0
                    hdr = row
                    continue
                row_id += 1
                row_res = {counterpart_pk: row_id}
                # row_billing = {}
                # row_shipping = {}
                # row_contact = {}
                for ix, value in enumerate(row):
                    if (
                        isinstance(value, basestring)
                        and value.startswith("[")
                        and value.endswith("]")
                    ):
                        value = eval(value)
                    if hdr[ix] == counterpart_pk:
                        if not value:
                            continue
                        row_id = value
                    # if hdr[ix].startswith("billing_"):
                    #     row_billing[hdr[ix]] = value
                    # elif hdr[ix].startswith("shipping_"):
                    #     row_shipping[hdr[ix]] = value
                    # elif hdr[ix].startswith("contact_"):
                    #     row_contact[hdr[ix]] = value
                    # else:
                    #     row_res[hdr[ix]] = value
                # if row_billing:
                #     if vmodel == "res.partner.invoice":
                #         row_res = row_billing
                #     else:
                #         row_res["billing"] = row_billing
                # if row_shipping:
                #     if vmodel == "res.partner.shipping":
                #         for nm in ("customer_shipping_id", "customer_id"):
                #             row_shipping[nm] = row_res[nm]
                #         row_res = row_shipping
                #     else:
                #         row_res["shipping"] = row_shipping
                # if row_contact:
                #     row_res["contact"] = row_contact
                if ext_id and row_res[counterpart_pk] != ext_id:
                    continue
                if ext_id:
                    res = row_res
                    break
                res.append(row_res)
        return res

    def get_counterpart_response(self, backend, vmodel, ext_id=False, mode=None):
        """Get data from counterpart"""
        Cache = self.env["ir.model.synchro.cache"]
        if not Cache.is_manageable(vmodel):
            return False
        # TODO: channel_id
        Cache.open(backend=backend, model=vmodel)
        method = Cache.get_attr(backend.id, "METHOD")
        if method == "XML":
            return self.get_xmlrpc_response(backend.id, vmodel, ext_id, mode=mode)
        elif method == "JSON":
            return self.get_json_response(backend.id, vmodel, ext_id, mode=mode)
        elif method == "CSV":
            return self.get_csv_response(backend.id, vmodel, ext_id, mode=mode)

    def create_ext_id(self, backend, actual_model, loc_id, ext_id):
        ext_id_name = self.get_loc_ext_id_name(backend, actual_model, force=True)
        self.env["ir.model.synchro.data"].create(
            {
                "model": actual_model,
                "ext_id_name": ext_id_name,
                "ext_id": ext_id,
                "res_id": loc_id,
            }
        )

    @api.model
    def assign_backend_loglevel(self, backend):
        # Cache = self.env["ir.model.synchro.cache"]
        # Cache.set_attr(backend.id, "LOGLEVEL", backend.tracelevel) or "2"
        # self.LOGLEVEL = Cache.get_attr(backend.id, "LOGLEVEL")
        self.LOGLEVEL = str(4 - int(backend.tracelevel or "2"))

    @api.model
    def synchro_childs(
        self, backend, vmodel, actual_model, parent_id, ext_id, only_minimal=None,
    ):
        backend_id = backend.id
        self.logmsg(
            "debug",
            "%(model)s.synchro_childs(%(chid)s,%(cmodel)s,%(id)s,%(xid)s) ##",
            model=vmodel,
            ctx={
                "chid": backend_id,
                "cmodel": actual_model,
                "id": parent_id,
                "xid": ext_id,
            },
        )

        Cache = self.env["ir.model.synchro.cache"]
        channel = self.env["synchro.channel"].browse(backend_id)
        child_ids = Cache.get_struct_model_attr(
            actual_model, "CHILD_IDS", default=False
        )
        model_child = Cache.get_struct_model_attr(actual_model, "MODEL_CHILD")
        if not child_ids and not model_child:
            _logger.error("!-5! Invalid structure of %s!" % vmodel)
            return -5
        if not self.env["synchro.channel.model"].search(
            [("synchro_channel_id", "=", backend_id), ("name", "=", model_child)]
        ):
            if Cache.get_attr(backend_id, "IDENTITY") == "odoo":
                self.env["synchro.channel.model"].build_odoo_synchro_model(
                    backend_id, model_child
                )
            else:
                _logger.error("!-11! Unmanaged model %s!" % model_child)
                return -11
        Cache.open(model=model_child, backend=channel)
        # Retrieve header id field
        parent_id_name = Cache.get_struct_model_attr(model_child, "PARENT_ID")
        if not parent_id_name:
            _logger.error("!-5! Invalid structure of %s!" % vmodel)
            return -5
        cls = self.get_actual_model(model_child)
        rec_ids = Cache.get_model_attr(backend_id, vmodel, "__%s_ids" % actual_model)
        Cache.del_model_attr(backend_id, vmodel, "__%s_ids" % actual_model)
        if not rec_ids:
            return -7

        if "to_delete" in cls._fields:
            cls.search([(parent_id_name, "=", parent_id),
                        ("to_delete", "=", False)]).write({"to_delete": True})
        for vals in rec_ids:
            vals[":%s" % parent_id_name] = parent_id
            if "to_delete" in cls._fields:
                vals[":to_delete"] = False
            try:
                id = self.generic_synchro(
                    cls,
                    vals,
                    channel_id=backend_id,
                    jacket=True,
                    only_minimal=only_minimal,
                    no_del_child=True,
                )
                if id < 0:
                    self.logmsg(
                        "warning",
                        "Error %(id)s processing %(model)s",
                        model=model_child,
                        ctx={"id": id},
                    )
                    return id
                # commit every table to avoid too big transaction
                # self.env.cr.commit()  # pylint: disable=invalid-commit
            except BaseException as e:  # pragma: no cover
                self.env.cr.rollback()  # pylint: disable=invalid-commit
                self.logmsg(
                    "error",
                    "Error %(e)s processing %(model)s(%(vals)s)",
                    model=model_child,
                    ctx={"e": e, "vals": vals},
                )
                return -12

        if "to_delete" in cls._fields:
            self.logmsg(
                "warning",
                "Removing deleted lines [%s]" % [x.id for x in cls.search(
                    [(parent_id_name, "=", parent_id), ("to_delete", "=", True)])]
            )
            cls.search(
                [(parent_id_name, "=", parent_id), ("to_delete", "=", True)]).unlink()

        self.commit(self.env[actual_model], parent_id)
        return ext_id

    @api.model
    def synchro(
        self, cls, vals, chk_in_queue=None, no_deep_fields=[], only_minimal=True,
        no_del_child=False
    ):
        """Generic synchronizer entry
        The external counterpart can call this method to synchronize a record;
        datas are prefixed by identification code which is store in channel.
        Prefix ia associated to conversion/mapping rule.
        """
        def protect_against_vg7(vmodel, actual_model, vals):
            # Protect against VG7 mistakes
            if "vg7_id" in vals and "vg7:id" not in vals:
                vals["vg7:id"] = vals["vg7_id"]
                del vals["vg7_id"]
                _logger.warning(
                    "Deprecated field name %s: please use %s!" % ("vg7_id", "vg7:id")
                )
            if "id" in vals:
                del vals["id"]
                _logger.warning("Ignored field name %s!" % "id")
            if vmodel == "sale.order":
                for nm in ("partner_id", "partner_shipping_id"):
                    if nm in vals:
                        del vals[nm]
                        _logger.warning("Ignored field name %s!" % nm)
            if vmodel == "res.partner" and vals.get("type"):
                vmodel = self.get_vmodel(actual_model, vals["type"])
                Cache.open(model=vmodel)
            return vmodel, vals

        def browse_from_id(actual_cls, vals):
            id = 0
            rec = None
            if "id" in vals:
                id = vals.pop("id")
            elif hasattr(actual_cls, "get_id_from_ref"):
                id, xref = actual_cls.get_id_from_ref(vals)
            if id:
                try:
                    rec = actual_cls.with_context({"lang": self.env.user.lang}).browse(
                        id
                    )
                except BaseException:
                    pass
                if not rec or rec.id != id:
                    _logger.error("!-3! ID %s does not exist in %s" % (id, vmodel))
                    # pop_ref(backend.id, vmodel, actual_model, id, ext_id)
                    return -3, None
                id = rec.id
                self.logmsg(
                    "debug",
                    "### synchro: found id=%(model)s.%(id)s",
                    model=actual_model,
                    rec=rec,
                )
            return id, rec

        vals = unicodes(vals)
        jvals = vals.copy()
        vmodel = cls._name
        actual_model = self.get_actual_model(vmodel, only_name=True)
        struct = self.env[actual_model].fields_get()
        actual_cls = self.get_actual_model(vmodel)
        Cache = self.env["ir.model.synchro.cache"]
        backend = self.env["synchro.channel"].assign_backend(vals)
        self.assign_backend_loglevel(backend)
        self.logrec = self.logmsg(
            "info",
            "synchro(%(vals)s,%(x)s,%(y)s)",
            model=vmodel,
            ctx={
                "vals": self.env["ir.model.synchro.log"].pretty_print(vals),
                "x": "in que" if chk_in_queue else "",
                "y": "internal" if no_del_child else ""
            },
        )
        # identity = Cache.get_attr(backend.id, "IDENTITY")
        Cache.open(
            model=vmodel,
            cls=cls,
            backend=backend,
        )
        no_deep_fields = no_deep_fields or []
        if "*" in no_deep_fields:
            no_deep_fields = list(set(no_deep_fields) - set(self.DEF_EXCL_FLDS))
            no_deep_fields = list(set(no_deep_fields) | set(self.DEF_INCL_FLDS))
        else:
            no_deep_fields = list(set(no_deep_fields) | set(self.DEF_EXCL_FLDS))
            no_deep_fields = list(set(no_deep_fields) - set(self.DEF_INCL_FLDS))
        if not backend:
            # cache.clean_cache()
            _logger.error("!-6! No channel found!")
            return -6

        if hasattr(actual_cls, "CONTRAINTS"):
            constraints = actual_cls.CONTRAINTS
        else:
            constraints = []
        has_state = "state" in struct
        has_2delete = "to_delete" in struct
        has_active = "active" in struct
        has_sequence = "sequence" in struct
        child_ids = Cache.get_struct_model_attr(
            actual_model, "CHILD_IDS", default=False
        )
        model_child = Cache.get_struct_model_attr(actual_model, "MODEL_CHILD")
        if no_del_child:
            sequence = 0
        else:
            last_model = Cache.get_attr(backend.id, "LAST_MODEL")
            sequence = Cache.get_attr(
                backend.id, "CTR", default=0) + 1 if last_model == actual_model else 1
            if (
                (has_sequence and "sequence" not in vals and backend.renum_lines)
                or actual_model.startswith("account.payment.term")
            ):
                vals["sequence"] = sequence

        do_auto_process = True
        if has_2delete or (
            Cache.get_model_attr(backend.id, vmodel, "BIND")
            and Cache.get_attr(backend.id, "IDENTITY") == "vg7"
        ):
            do_auto_process = False
        if Cache.get_attr(backend.id, "IDENTITY") == "vg7":
            vmodel, vals = protect_against_vg7(vmodel, actual_model, vals)
        # TODO: channel_id
        Cache.open(backend=backend, ext_model=vmodel)
        spec = ""
        if vmodel == actual_model:
            if hasattr(cls, "preprocess"):
                vals, spec = cls.preprocess(backend, vals)
            elif do_auto_process:
                vals, spec = self.preprocess(backend, vmodel, vals)
            if spec:
                vmodel = self.get_vmodel(actual_model, spec)
                actual_model = self.get_actual_model(vmodel)
                Cache.open(model=vmodel)
            self.logmsg(
                "debug",
                "preprocess(%(model)s,%(vals)s)",
                model=vmodel,
                ctx={"vals": self.env["ir.model.synchro.log"].pretty_print(vals)},
            )
        else:
            spec = self.get_spec_from_vmodel(vmodel)
        # Warning! After this function, return MUST pop ref_id
        vals, parent_child_mode = self.map_to_internal(
            struct, backend, vmodel, vals, no_deep_fields=no_deep_fields
        )
        if has_sequence and "sequence" in vals:
            sequence = vals["sequence"]
        ext_id_name = self.get_loc_ext_id_name(backend, vmodel)
        ext_id = vals.get(ext_id_name)

        loc_id, rec = browse_from_id(actual_cls, vals)
        if loc_id < 0:
            return loc_id
        elif loc_id == 0:
            loc_id, rec = self.bind_record(
                struct, backend, vmodel, vals, constraints)
        if loc_id > 0 and "sequence" in rec:
            sequence = rec["sequence"]
        if not no_del_child:
            Cache.set_attr(backend.id, "LAST_MODEL", actual_model)
            Cache.set_attr(backend.id, "CTR", sequence)
        if loc_id == -7 and not has_state:
            self.logmsg("info",
                        "### No values passed(%s.%s)" % (vmodel, actual_model),
                        logrec=self.logrec, id=loc_id)
            return loc_id
        if (
            vmodel in ("res.partner.shipping", "res.partner.invoice")
            and not self.diff_parent(vals, spec)
        ):
            vals["active"] = False
        if has_state:
            vals, erc = self.set_state_to_draft(struct, vmodel, rec, vals)
            if erc < 0:
                _logger.error("!%s! Returned error code!" % erc)
                return erc
        if has_2delete:
            vals["to_delete"] = False
        self.drop_invalid_fields(vmodel, vals)
        do_write = True
        if loc_id < 1:
            if has_state or has_2delete or not ext_id:
                min_vals = vals
                do_write = False
                vals = self.set_default_values(cls, backend, vmodel, vals)
            else:
                vals = self.set_default_values(cls, backend, vmodel, vals)
                min_vals = self.load_min_vals(
                    backend, vmodel, vals, ext_id_name, ext_id)
                if not min_vals or min_vals == vals:
                    do_write = False
                    min_vals = vals
                else:
                    do_write = True
            if vals:
                if hasattr(actual_cls, "assure_values"):
                    vals = actual_cls.assure_values(vals, rec)
                if actual_model == "account.payment.term":
                    vals[child_ids] = {"sequence": 1, "value": "balance"}
                rec = self.create_n_commit(actual_model, min_vals, logrec=self.logrec)
                if not rec and min_vals != vals:
                    rec = self.create_n_commit(actual_model, vals, logrec=self.logrec)
                if not rec:
                    return loc_id
                if backend.ignore_child_lines and parent_child_mode == "B":
                    parent_child_mode = "A"
                loc_id = rec.id
                if not ext_id_name:
                    self.create_ext_id(backend, actual_model, loc_id, ext_id)
                if only_minimal:
                    do_write = False
        if loc_id > 0 and do_write:
            try:
                rec = actual_cls.with_context({"lang": self.env.user.lang}).browse(
                    loc_id
                )
            except BaseException as e:  # pragma: no cover
                self.env.cr.rollback()  # pylint: disable=invalid-commit
                self.logmsg(
                    "error",
                    "!-3! %(e)s\nvalues=%(val)s",
                    model=vmodel,
                    logrec=self.logrec,
                    rec=rec,
                    ctx={"e": e, "val": jvals},
                )
                rec = None
            if rec:
                if hasattr(cls, "assure_values"):
                    vals = actual_cls.assure_values(vals, rec)
                if vals:
                    if has_active and not rec.active:
                        vals["active"] = True
                    vals = self.drop_protected_fields(
                        backend, vmodel, vals, rec, no_del_child=no_del_child)
                if vals:
                    try:
                        if actual_model.startswith("account.move"):
                            rec.with_context(check_move_validity=False).write(vals)
                        else:
                            rec.write(vals)
                        self.logmsg(
                            "warning",
                            "synchro: %s[%s].write(%s)"
                            % (actual_model, rec.id, vals),
                            logrec=self.logrec,
                            rec=rec,
                        )
                    except BaseException as e:  # pragma: no cover
                        self.env.cr.rollback()  # pylint: disable=invalid-commit
                        self.logmsg(
                            "error",
                            "!-2! %(e)s\nvalues=%(val)s",
                            model=vmodel,
                            logrec=self.logrec,
                            rec=rec,
                            ctx={"e": e, "val": jvals},
                        )
                        return -2
                elif do_write:
                    self.logmsg(
                        "debug", "### Nothing to update(%s.%s)"
                                 % (actual_model, loc_id),
                        logrec=self.logrec,
                        rec=rec
                    )
                if (
                    do_write and rec and child_ids and hasattr(rec, child_ids)
                    and Cache.get_struct_model_attr(model_child, "sequence")
                    and backend.renum_lines
                ):
                    for num, line in enumerate(rec[child_ids]):
                        sequence = num + 1
                        child_vals = {"sequence": sequence}
                        try:
                            line.write(child_vals)
                            self.logmsg(
                                "debug",
                                "line[%(id)s].write(%(vals)s)",
                                rec=rec,
                                ctx={
                                    "vals": self.env[
                                        "ir.model.synchro.log"].pretty_print(child_vals)
                                },
                            )
                        except BaseException as e:  # pragma: no cover
                            self.env.cr.rollback()  # pylint: disable=invalid-commit
                            self.logmsg(
                                "error",
                                "!-2! %(e)s\nvalues=%(val)s",
                                model=vmodel,
                                ctx={"e": e, "val": child_vals},
                            )

        if (
            rec and vmodel in ("res.partner.shipping", "res.partner.invoice")
            and "active" in vals and vals["active"] != rec.active
        ):
            rec.write({"active": vals["active"]})
        # commit to avoid lost data in recursive write
        # self.env.cr.commit()  # pylint: disable=invalid-commit

        if loc_id > 0 and not chk_in_queue and vmodel == "res.partner":
            child_vals = Cache.get_model_attr(
                backend.id, vmodel, "__partner.invoice")
            if child_vals:
                Cache.del_model_attr(backend.id, vmodel,  "__partner.invoice")
            child_vals = Cache.get_model_attr(
                backend.id, vmodel, "__partner.shipping")
            if child_vals:
                child_vals[":parent_id"] = loc_id
                Cache.del_model_attr(backend.id, vmodel, "__partner.shipping")
                cls = self.env["res.partner.shipping"]
                self.generic_synchro(
                    cls, child_vals, channel_id=backend.id,
                    jacket=True, only_minimal=True)

        # if loc_id > 0 and not chk_in_queue and vmodel == actual_model:
        #     if actual_model == "res.lang":
        #         self.manage_language(vals)
        #     elif actual_model == "ir.module.module":
        #         loc_id = self.set_actual_state(struct, actual_model, rec)
        #         if loc_id < 0:
        #             return loc_id

        parent_id_name = Cache.get_struct_model_attr(actual_model, "PARENT_ID")
        if model_child and rec and hasattr(rec, "fiscal_position_id"):
            Cache.set_model_attr(
                backend.id, model_child, "__%s_FP" % model_child,
                rec.fiscal_position_id
            )
        if parent_child_mode == "B":
            sts = self.synchro_childs(
                backend,
                vmodel,
                actual_model,
                loc_id,
                ext_id,
                only_minimal=only_minimal,
            )
            if sts < 1:
                return sts - 100
        elif model_child:
            self.logmsg(
                "debug",
                "### Child mode %s: counterpart must send child records"
                % parent_child_mode,
            )
        elif rec and loc_id > 0 and "to_delete" in rec and not no_del_child:
            actual_cls.search([(parent_id_name, "=", rec[parent_id_name].id),
                               ("to_delete", "=", True)]).unlink()
        if model_child and rec and hasattr(rec, "fiscal_position_id"):
            Cache.del_model_attr(backend.id, model_child, "__%s_FP" % model_child)
        if (
            loc_id > 0
            and not chk_in_queue
            and vmodel == actual_model
            and not no_del_child
        ):
            self.synchro_queue(backend)
        _logger.info("!%s! Returned ID of %s" % (loc_id, vmodel))
        return loc_id

    @api.model
    def commit(self, cls, loc_id, ext_id=None, backend=None):
        vmodel = cls._name
        actual_model = self.get_actual_model(vmodel, only_name=True)
        self.logmsg(
            "warning",
            "%(model)s[%(id)s].commit(%(x)s)",
            model=vmodel,
            ctx={"id": loc_id, "x": ext_id},
        )
        struct = self.env[actual_model].fields_get()
        Cache = self.env["ir.model.synchro.cache"]
        Cache.open(model=vmodel, cls=cls)
        has_state = "state" in struct
        child_ids = Cache.get_struct_model_attr(
            actual_model, "CHILD_IDS", default=False
        )
        model_child = Cache.get_struct_model_attr(actual_model, "MODEL_CHILD")
        if not has_state and not child_ids and not model_child:
            _logger.error("!-5! Invalid structure of %s!" % vmodel)
            return -5
        Cache.open(model=model_child)
        # Retrieve header id field
        parent_id_name = Cache.get_struct_model_attr(model_child, "PARENT_ID")
        if not parent_id_name:
            _logger.error("!-5! Invalid structure of %s!" % vmodel)
            return -5
        if (not loc_id or loc_id < 1) and ext_id:
            backend = backend or fields.first(self.env["synchro.channel"].search([]))
            loc_id = self.bind_record(
                struct, backend, vmodel, {"id": ext_id}, [], False)

        try:
            rec_2_commit = self.get_actual_model(vmodel).browse(loc_id)
        except BaseException:
            _logger.error("!-3! Errore retriving %s.%s!" % (vmodel, loc_id))
            return -3
        loc_id = 0
        if has_state:
            loc_id = self.set_actual_state(struct, vmodel, rec_2_commit)
            if loc_id < 0:
                _logger.error("!%s! Committed ID" % loc_id)
            else:
                _logger.info("!%s! Committed ID" % loc_id)
        return loc_id

    @api.model
    def generic_synchro(
        self,
        cls,
        vals,
        jacket=None,
        chk_in_queue=None,
        channel_id=None,
        only_minimal=True,
        no_deep_fields=None,
        no_del_child=False,
    ):
        self.logmsg(
            "debug",
            "%(model)s.generic_synchro(jacket=%(j)s,que=%(d)s)",
            model=cls._name,
            ctx={"j": jacket, "d": chk_in_queue},
        )
        Cache = self.env["ir.model.synchro.cache"]
        if hasattr(cls, "synchro"):
            if jacket:
                return cls.synchro(
                    self.jacket_vals(Cache.get_attr(channel_id, "PREFIX"), vals),
                    chk_in_queue=chk_in_queue,
                    only_minimal=only_minimal,
                    no_deep_fields=no_deep_fields,
                    no_del_child=no_del_child,
                )
            else:
                return cls.synchro(
                    vals,
                    chk_in_queue=chk_in_queue,
                    only_minimal=only_minimal,
                    no_deep_fields=no_deep_fields,
                    no_del_child=no_del_child,
                )
        else:
            if jacket:
                return self.synchro(
                    cls,
                    self.jacket_vals(Cache.get_attr(channel_id, "PREFIX"), vals),
                    chk_in_queue=chk_in_queue,
                    only_minimal=only_minimal,
                    no_deep_fields=no_deep_fields,
                )
            else:
                return self.synchro(
                    cls,
                    vals,
                    chk_in_queue=chk_in_queue,
                    only_minimal=only_minimal,
                    no_deep_fields=no_deep_fields,
                )

    @api.model
    def jacket_vals(self, prefix, vals):
        self.logmsg(
            "debug",
            "jacket_vals(%(pfx)s,%(vals)s)",
            ctx={
                "pfx": prefix,
                "vals": self.env["ir.model.synchro.log"].pretty_print(vals)
            },
        )
        jvals = {}
        for name in vals:
            if name.startswith(prefix):
                jvals[name] = vals[name]
            elif name.startswith(":"):
                jvals[name[1:]] = vals[name]
            else:
                jvals["%s:%s" % (prefix, name)] = vals[name]
        return jvals

    @api.model
    def preprocess(self, backend, vmodel, vals):
        return vals, ""

    @api.model
    def synchro_queue(self, backend):
        self.logmsg("warning", "synchro_queue()")
        cache = self.env["ir.model.synchro.cache"]
        max_ctr = 16
        queue = cache.get_attr(backend.id, "IN_QUEUE")
        while queue:
            if max_ctr == 0:
                break
            max_ctr -= 1
            item = queue.pop(0)
            vmodel = item[0]
            loc_id = item[1]
            if not loc_id or loc_id < 1:
                self.logmsg(
                    "warning", "### invalid %s.synchro_queue[%s]" % (vmodel, loc_id)
                )
                return
            self.logmsg("debug", "queued_pull(%s,%s)?" % (vmodel, loc_id))
            # rec = self.get_actual_model(vmodel).browse(loc_id)
            rec = (
                self.get_actual_model(vmodel)
                .with_context({"lang": self.env.user.lang})
                .browse(loc_id)
            )
            loc_ext_id_name = self.get_loc_ext_id_name(backend, vmodel)
            if loc_ext_id_name and hasattr(rec, loc_ext_id_name):
                self.pull_1_record(backend.id, vmodel, getattr(rec, loc_ext_id_name))

    @api.model
    def vals_or_id(self, item, ext_key_id):
        if isinstance(item, (int, long)):
            vals = {}
            ext_id = item
        else:
            vals = item
            if isinstance(vals, (list, tuple)):
                vals = vals[0]
            if ext_key_id in vals:
                if isinstance(vals[ext_key_id], (int, long)):
                    ext_id = vals[ext_key_id]
                else:
                    ext_id = int(vals[ext_key_id])
            else:
                ext_id = False
        return ext_id, vals

    @api.multi
    def pull_recs_2_complete(self, only_model=None):
        """Delete records does not exist on counterpart"""

        def get_ext_id(ext_ix, datas):
            if ext_ix < -1:
                return -1, -2
            ext_ix += 1
            if ext_ix < len(datas):
                if isinstance(datas[ext_ix], (int, long)):
                    ext_id = int(datas[ext_ix])
                else:
                    ext_id = int(datas[ext_ix]["id"])
            else:
                ext_id = -1
                ext_ix = -2
            return ext_id, ext_ix

        def get_loc_id(loc_ix, recs, loc_ext_id, backend_id):
            # vmodel?
            if loc_ix < -1:
                return -1, -2
            loc_ix += 1
            if loc_ext_id and loc_ix < len(recs):
                if isinstance(recs[loc_ix], (int, long)):
                    loc_id = recs[loc_ix]
                else:
                    loc_id = recs[loc_ix][loc_ext_id]
                loc_id = self.get_actual_ext_id_value(backend_id, vmodel, loc_id)
            else:
                loc_id = -1
                loc_ix = -2
            return loc_id, loc_ix

        self.logmsg("warning", "pull_recs_2_complete(%(x)s)", ctx={"x": only_model})
        cache = self.env["ir.model.synchro.cache"]
        cache.open()
        cache.setup_channels(all=True)
        for backend in cache.get_channel_list().copy():
            if not cache.get_attr(backend.id, "COUNTERPART_URL") and not cache.get_attr(
                backend.id, "EXCHANGE_PATH"
            ):
                continue
            identity = cache.get_attr(backend.id, "IDENTITY")
            if identity == "odoo":
                model_list = self.env["ir.model.synchro.cache"].TABLE_DEF.keys()
            else:
                domain = [("synchro_channel_id", "=", backend.id)]
                model_list = [
                    x.name
                    for x in self.env["synchro.channel.model"].search(
                        domain, order="sequence"
                    )
                ]
            ctr = 0
            for vmodel in model_list:
                if not cache.is_struct(vmodel):
                    continue
                cache.open(model=vmodel)
                if identity != "odoo" and not cache.get_model_attr(
                    backend.id, vmodel, "BIND"
                ):
                    continue
                loc_ext_id_name = self.get_loc_ext_id_name(backend, vmodel)
                actual_model = self.get_actual_model(vmodel, only_name=True)
                self.logmsg("info", "### Checking %s for unlink" % vmodel)
                cls = self.env[vmodel]
                datas = self.get_model_of_channel(
                    backend.id, vmodel
                ).get_counterpart_response()
                if not datas:
                    continue
                if not isinstance(datas, (list, tuple)):
                    datas = [datas]
                if len(datas) and isinstance(datas[0], (int, long)):
                    datas.sort()
                if loc_ext_id_name:
                    recs = cls.search(
                        [(loc_ext_id_name, "!=", False)], order=loc_ext_id_name
                    )
                else:
                    recs = []
                ext_ix = -1
                loc_ix = -1
                ext_id, ext_ix = get_ext_id(ext_ix, datas)
                loc_id, loc_ix = get_loc_id(loc_ix, recs, loc_ext_id_name, backend.id)
                while ext_id > 0 and loc_id > 0:
                    if (
                        (loc_id > 0 and 0 < ext_id < loc_id)
                        or (loc_id < 0 and ext_id > 0)
                        or (
                            cache.get_struct_model_attr(actual_model, "MODEL_WITH_NAME")
                            and recs[loc_ix].name.startswith("Unknown")
                        )
                    ):
                        if identity == "odoo" or cache.get_model_attr(
                            backend.id, vmodel, "2PULL", default=True
                        ):
                            if isinstance(datas[ext_ix], (int, long)):
                                vals = self.get_model_of_channel(
                                    backend.id, vmodel
                                ).get_counterpart_response(id=ext_id)
                            else:
                                vals = datas[ext_ix]
                            if not vals:
                                continue
                            self.generic_synchro(
                                cls, vals, jacket=True, channel_id=backend.id
                            )
                            # self.env.cr.commit()  # pylint: disable=invalid-commit
                        ext_id, ext_ix = get_ext_id(ext_ix, datas)
                    elif (
                        (ext_id > 0 and 0 < loc_id < ext_id)
                        or loc_id > 0
                        and ext_id < 0
                    ):
                        if isinstance(recs[ext_ix], (int, long)):
                            rec = cls.browse(loc_id)
                        else:
                            rec = recs[loc_ix]
                        if loc_ext_id_name:
                            rec.write({loc_ext_id_name: False})
                        try:
                            id = rec.id
                            rec.unlink()
                            ctr += 1
                            # self.env.cr.commit()  # pylint: disable=invalid-commit
                            self.logmsg(
                                "warning",
                                "### Deleted record %s[%d] ext=%d"
                                % (vmodel, id, loc_id),
                            )
                        except BaseException as e:  # pragma: no cover
                            self.env.cr.rollback()  # pylint: disable=invalid-commit
                            self.logmsg(
                                "error", "!-3! %(e)s", model=vmodel, ctx={"e": e}
                            )

                        loc_id, loc_ix = get_loc_id(
                            loc_ix, recs, loc_ext_id_name, backend.id
                        )
                    else:
                        ext_id, ext_ix = get_ext_id(ext_ix, datas)
                        loc_id, loc_ix = get_loc_id(
                            loc_ix, recs, loc_ext_id_name, backend.id
                        )
            _logger.info(
                "%s record successfully unlinked from channel %s" % (ctr, backend.id)
            )

    @api.multi
    def pull_full_records(
        self,
        force=None,
        only_model=None,
        only_complete=None,
        select=None,
        only_minimal=None,
        no_deep_fields=None,
        remote_ids=None,
        sel_backend=None,
    ):
        """Called by import wizard
        @only_complete: import only records which name starting with 'Unknown'
        """

        def evaluate_remote_ids(rec_ids):
            remote_ids = rec_ids
            if isinstance(rec_ids, basestring):
                remote_ids = []
                for item in (
                    rec_ids.replace("[", "")
                    .replace("]", "")
                    .replace(",", " ")
                    .replace("  ", " ")
                    .split(" ")
                ):
                    if item.isdigit():
                        remote_ids.append(eval(item))
                    else:
                        if item.find("-") < 0:
                            continue
                        items = item.split("-")
                        if not items[0].isdigit():
                            if not items[1].isdigit():
                                items[0] = 1
                            else:
                                items[0] = int(items[1]) - 100
                                if items[0] < 1:
                                    item[0] = 1
                        if not items[1].isdigit():
                            items[1] = int(items[0]) + 100
                        item = "range(%d,%d)" % (int(items[0]), int(items[1]) + 1)
                        remote_ids += eval(item)
            return remote_ids

        def update_rec_counter(
            cur_backend, ext_id, rec_counter, use_workflow, model=None
        ):
            if ext_id > rec_counter:
                rec_counter = ext_id
                if use_workflow:
                    vals = {"rec_counter": rec_counter}
                    if model:
                        vals["workflow_model"] = model
                    cur_backend.write(vals)
                elif model:
                    vals = {"rec_counter": rec_counter}
                    rec = self.env["synchro.channel.model"].search(
                        [("name", "=", model),
                         ("model_spec", "=", False),
                         ("synchro_channel_id", "=", cur_backend.id)])
                    if rec:
                        rec.write(vals)
            return rec_counter

        def do_workflow(backend, only_complete, use_workflow, datetime_stop,
                        local_ids):
            cur_backend = backend
            workflow = cur_backend.import_workflow
            rec_counter = cur_backend.rec_counter
            self.logmsg(
                "debug",
                ">>> WORKFLOW(%(w)s,%(c)s)",
                ctx={
                    "w": cur_backend.import_workflow,
                    "c": cur_backend.rec_counter,
                },
            )
            while workflow in WORKFLOW:
                if datetime.now() > datetime_stop:
                    break
                model_list = [WORKFLOW[workflow]["model"]]
                select = WORKFLOW[workflow].get("select", "all")
                only_minimal = WORKFLOW[workflow].get("only_minimal", False)
                no_deep_fields = WORKFLOW[workflow].get("no_deep_fields", [])
                remote_ids = WORKFLOW[workflow].get("remote_ids")
                if not remote_ids:
                    remote_ids = "%s-" % (rec_counter + 1)
                self.logmsg(
                    "debug",
                    ">>> use_workflow(wkf=%(w)s,only_min=%(o)s,nodeep=%(n)s,rmt=%(r)s)",
                    ctx={
                        "w": workflow,
                        "o": only_minimal,
                        "n": no_deep_fields,
                        "r": remote_ids,
                    },
                )
                rec_counter, loc_ids = pull_model(
                    backend, select, only_complete, use_workflow, only_minimal,
                    datetime_stop, no_deep_fields, model_list, remote_ids,
                    rec_counter
                )
                if loc_ids:
                    local_ids = local_ids + loc_ids
                    cur_backend.rec_counter = rec_counter
                else:
                    workflow += 1
                    cur_backend.import_workflow = workflow
                    cur_backend.rec_counter = 0
                    cur_backend.workflow_model = ""
                self.logmsg(
                    "debug",
                    ">>> WORKFLOW(%(w)s,%(c)s)",
                    ctx={
                        "w": cur_backend.import_workflow,
                        "c": cur_backend.rec_counter,
                    },
                )

        def pull_model(backend, select, only_complete, use_workflow, only_minimal,
                       datetime_stop, no_deep_fields, model_list,
                       remote_ids, rec_counter):
            cache = self.env["ir.model.synchro.cache"]
            identity = cache.get_attr(backend.id, "IDENTITY")
            cur_backend = backend
            ctr = 0
            local_ids = []
            for vmodel in model_list:
                if datetime.now() > datetime_stop:
                    break
                if not self.env["synchro.channel.model"].search(
                    [("synchro_channel_id", "=", backend.id), ("name", "=", vmodel)]
                ):
                    if identity == "odoo":
                        if not self.env[
                            "synchro.channel.model"].build_odoo_synchro_model(
                            backend.id, None, model=vmodel
                        ):
                            continue
                    else:
                        continue
                cache.open(model=vmodel)
                actual_model = self.get_actual_model(vmodel, only_name=True)
                if only_complete and not cache.get_struct_model_attr(
                    actual_model, "MODEL_WITH_NAME"
                ):
                    continue
                if (
                    identity != "odoo"
                    and not only_complete
                    and not cache.get_model_attr(
                        backend.id, vmodel, "2PULL", default=True
                    )
                ):
                    self.logmsg("info", "### Model %s not pullable" % vmodel)
                    continue
                cls = self.env[vmodel]
                if remote_ids:
                    datas = evaluate_remote_ids(remote_ids)
                else:
                    datas = self.get_model_of_channel(
                        backend.id, vmodel
                    ).get_counterpart_response()
                if not datas:
                    continue
                if not isinstance(datas, (list, tuple)):
                    datas = [datas]
                if len(datas) and isinstance(datas[0], (int, long)):
                    datas.sort()
                ext_id_name = self.get_loc_ext_id_name(backend, vmodel)
                for item in datas:
                    if datetime.now() > datetime_stop:
                        break
                    if not item:
                        continue
                    ext_id, vals = self.vals_or_id(item, ext_id_name)
                    if ext_id:
                        if (
                            select == "new"
                            and ext_id_name
                            and cls.search([(ext_id_name, "=", ext_id)])
                        ) or (
                            select == "upd"
                            and ext_id_name
                            and not cls.search([(ext_id_name, "=", ext_id)])
                        ):
                            rec_counter = update_rec_counter(
                                cur_backend.id,
                                ext_id,
                                rec_counter,
                                use_workflow,
                                model=vmodel,
                            )
                            continue
                        if use_workflow and ext_id <= rec_counter:
                            continue
                        rec_counter = update_rec_counter(
                            cur_backend.id, ext_id, rec_counter, use_workflow,
                            model=vmodel
                        )
                    loc_id = self.pull_1_record(
                        backend.id,
                        vmodel,
                        vals or ext_id,
                        only_minimal=only_minimal,
                        no_deep_fields=no_deep_fields,
                    )
                    self.logmsg(
                        "debug",
                        "WORKFLOW>>> self.pull_1_record("
                        "ch=%s,%s,%s,min=%s,nodeep=%s)"
                        % (
                            backend.id,
                            vmodel,
                            vals or ext_id,
                            only_minimal,
                            no_deep_fields,
                        ),
                    )
                    if loc_id == -8:
                        break
                    if loc_id < 0:
                        continue
                    rec_counter = update_rec_counter(
                        cur_backend.id, ext_id, rec_counter, use_workflow
                    )
                    ctr += 1
                    if loc_id not in local_ids:
                        local_ids.append(loc_id)
            _logger.info(
                "%s record successfully pulled from channel %s" % (ctr, backend.id))
            return rec_counter, local_ids

        self.logmsg(
            "debug",
            ">>> pull_full_records(force=%(f)s,only_model=%(x)s,select=%(sel)s)",
            ctx={"f": force, "x": only_model, "sel": select},
        )
        use_workflow = False
        if not select:
            if force:
                select = "all"
                use_workflow = True
            elif only_complete:
                select = "upd"
            else:
                select = "new"
        datetime_stop = datetime.now() + timedelta(seconds=210 if use_workflow else 500)
        cache = self.env["ir.model.synchro.cache"]
        cache.open(backend=sel_backend, model=only_model)
        if not sel_backend:
            cache.setup_channels(all=True)
        local_ids = []
        for backend in cache.get_channel_list():
            if sel_backend and backend != sel_backend:
                continue
            if datetime.now() > datetime_stop:
                break
            if not cache.get_attr(backend.id, "COUNTERPART_URL") and not cache.get_attr(
                backend.id, "EXCHANGE_PATH"
            ):
                continue
            identity = cache.get_attr(backend.id, "IDENTITY")
            rec_counter = 0
            if use_workflow:
                do_workflow(
                    backend, only_complete, use_workflow, datetime_stop, local_ids)
            elif identity == "odoo":
                if only_model:
                    model_list = [only_model]
                else:
                    model_list = self.env["ir.model.synchro.cache"].TABLE_DEF.keys()
                rec_counter, local_ids = pull_model(
                    backend, select, only_complete, use_workflow, only_minimal,
                    datetime_stop, no_deep_fields, model_list,
                    remote_ids, rec_counter)
            else:
                domain = [("synchro_channel_id", "=", backend.id)]
                if only_model:
                    domain.append(("name", "=", only_model))
                model_list = [
                    x.name
                    for x in self.env["synchro.channel.model"].search(
                        domain, order="sequence"
                    )
                ]
                rec_counter, local_ids = pull_model(
                    backend, select, only_complete, use_workflow, only_minimal,
                    datetime_stop, no_deep_fields, model_list,
                    remote_ids, rec_counter)
        return local_ids

    @api.model
    def pull_1_record(
        self,
        backend_id,
        vmodel,
        item,
        chk_in_queue=None,
        only_minimal=None,
        no_deep_fields=None,
    ):
        self.logmsg(
            "debug", "%(model)s.pull_1_record(%(x)s)", model=vmodel, ctx={"x": item}
        )
        cache = self.env["ir.model.synchro.cache"]
        counterpart_pk = cache.get_model_attr(
            backend_id, vmodel, "KEY_ID", default="id")
        ext_id, vals = self.vals_or_id(item, counterpart_pk)
        if not vals and ext_id:
            Backend = self.get_model_of_channel(backend_id, vmodel)
            if not Backend:
                self.env["ir.model.synchro"].logmsg(
                    "error", "Model %(model)s not managed by external partner!",
                    model=vmodel
                )
                return -8
            vals = Backend.get_counterpart_response(ext_id)
        if not vals:
            return -7
        ext_id, vals = self.vals_or_id(vals, counterpart_pk)
        if not counterpart_pk:
            self.logmsg("warning", "Data received of model %s w/o id" % vmodel)
            return -1
        cls = self.env[vmodel]
        id = self.generic_synchro(
            cls,
            vals,
            chk_in_queue=chk_in_queue,
            jacket=True,
            channel_id=backend_id,
            only_minimal=only_minimal,
            no_deep_fields=no_deep_fields,
        )
        if id < 0:
            self.logmsg(
                "warning", "External id %s error pulling from %s" % (ext_id, vmodel)
            )
            return id
        # commit every table to avoid too big transaction
        # self.env.cr.commit()  # pylint: disable=invalid-commit
        return id

    @api.multi
    def pull_record(self, cls, backend_id=None):
        """Button synchronize at record UI page"""
        self.logmsg("debug", "pull_record()")
        cache = self.env["ir.model.synchro.cache"]
        for rec in cls:
            model = cls.__class__.__name__
            self.logmsg("info", "%s.pull_record()" % model)
            if not cache.is_struct(model):
                continue
            cache.setup_channels(all=True)
            for backend in cache.get_channel_list():
                cache.open(model=model, cls=cls, backend=backend)
                identity = cache.get_attr(backend.id, "IDENTITY")
                loc_ext_id_name = self.get_loc_ext_id_name(backend, model)
                if loc_ext_id_name and hasattr(rec, loc_ext_id_name):
                    vmodel = model
                    ext_id = getattr(rec, loc_ext_id_name)
                    if identity == "vg7":
                        if model == "res.partner":
                            if ext_id > 200000000:
                                vmodel = "%s.invoice" % model
                            elif ext_id > 100000000:
                                vmodel = "%s.shipping" % model
                                cache.open(model=vmodel, backend=backend)
                            ext_id = self.get_actual_ext_id_value(
                                backend.id, vmodel, ext_id
                            )
                    if ext_id and (
                        identity != "vg7" or vmodel != "res.partner.invoice"
                    ):
                        self.pull_1_record(backend.id, vmodel, ext_id)
                    if identity == "vg7" and model == "res.partner":
                        vmodel = "res.partner.supplier"
                        loc_ext_id_name = self.get_loc_ext_id_name(backend, vmodel)
                        if loc_ext_id_name and cache.get_struct_model_attr(
                            model, loc_ext_id_name
                        ):
                            ext_id = getattr(rec, loc_ext_id_name)
                            ext_id = self.get_actual_ext_id_value(
                                backend.id, vmodel, ext_id
                            )
                            if ext_id:
                                cache.open(model=vmodel)
                                self.pull_1_record(backend.id, vmodel, ext_id)

    @api.model
    def trigger_one_record(self, ext_model, prefix, ext_id):
        if not prefix:
            return -7
        Cache = self.env["ir.model.synchro.cache"]
        backend = self.env["synchro.channel"].assign_backend({"%s:" % prefix: ""})
        self.assign_backend_loglevel(backend)
        self.logmsg(
            "info",
            "trigger_one_record(%(xm)s,%(xid)s,%(pfx)s)",
            ctx={"xm": ext_model, "xid": ext_id, "pfx": prefix},
        )
        backend_id = backend.id
        if not backend_id:
            # Cache.clean_cache()
            _logger.error("!-6! No channel found!")
            return -6
        self.logmsg(
            "debug", "### assigned channel is %(chid)s", ctx={"chid": backend_id}
        )
        Cache.open(backend=backend, ext_model=ext_model)
        for model in Cache.get_channel_models(backend_id):
            if not Cache.is_struct(model):
                continue
            if ext_model != Cache.get_model_attr(backend_id, model, "BIND"):
                continue
            return self.pull_1_record(backend_id, model, ext_id)
        return -8

    # def manage_module(self, vals):
    #     if "name" not in vals:
    #         self.logmsg("error", "Invalid module name")
    #         return -7
    #     module_model = self.env["ir.module.module"]
    #     modules = module_model.search([("name", "=", vals["name"])])
    #     if not modules:
    #         self.logmsg("error", "Module %s does not exist" % vals["name"])
    #         return -3
    #     module = modules[0]
    #     if module.state == "uninstalled":
    #         try:
    #             modules.button_immediate_install()
    #         except BaseException as e:  # pragma: no cover
    #             self.env.cr.rollback()  # pylint: disable=invalid-commit
    #             self.logmsg("error",
    #                         "Module %s not installable\n%s" % (vals["name"], e))
    #             return -4
    #         max_ctr = len(module.dependencies_id) + 3
    #         query = ("SELECT id FROM ir_module_module WHERE"
    #                  " name='%s' AND state='installed'" % module.name)
    #         # Check for state by sql to avoid cache trouble
    #         while max_ctr > 0:
    #             self.env.cr.execute(query)
    #             res = self.env.cr.fetchall()
    #             if res:
    #                 module.state = "installed"
    #                 break
    #             max_ctr -= 1
    #             time.sleep(0.5)
    #         time.sleep(1)
    #     if module.state != "installed":
    #         self.logmsg("error", "Module %s not installed" % vals["name"])
    #         return -4
    #     self.logmsg("info",
    #                 "%s.install(%s)" % ("ir.module.module", module.name))
    #     return module.id
    #
    # def manage_language(self, vals):
    #     if "code" not in vals:
    #         self.logmsg("error", "Invalid language code")
    #         return -7
    #     languages = self.env["res.lang"].search([("code", "=", vals["code"])])
    #     if not languages:
    #         lang_model = self.env["base.language.install"]
    #         lang_model.create({"code": vals["code"], "overwrite": True}).lang_install()
    #         languages = self.env["res.lang"].search([("code", "=", vals["code"])])
    #     return languages[0].id


class IrModelField(models.Model):
    _inherit = "ir.model.fields"

    protect_update = fields.Selection(
        [
            ("0", "Always Update"),
            ("1", "But new value not empty"),
            ("2", "But current value is empty"),
            ("3", "Protected field"),
        ],
        string="Protect field against update",
        default="0",
    )

    @api.model_cr_context
    def _auto_init(self):
        res = super(IrModelField, self)._auto_init()

        self._cr.execute(
            """UPDATE ir_model_fields set protect_update='3'
        where name not like '____id' and model_id in
        (select id from ir_model where model='res.country');
        """
        )

        self._cr.execute(
            """UPDATE ir_model_fields set protect_update='3'
        where name not like '____id' and model_id in
        (select id from ir_model where model='res.country.state');
        """
        )

        self._cr.execute(
            """UPDATE ir_model_fields set protect_update='0'
        where name not in ('type', 'categ_id', 'uom_id', 'uom_po_id',
        'purchase_method', 'invoice_policy', 'property_account_income_id',
        'taxes_id', 'property_account_expense_id', 'supplier_taxes_id')
        and model_id in
        (select id from ir_model where model='product_product');
        """
        )

        self._cr.execute(
            """UPDATE ir_model_fields set protect_update='3'
        where name in ('type', 'categ_id', 'uom_id', 'uom_po_id',
        'purchase_method', 'invoice_policy', 'property_account_income_id',
        'taxes_id', 'property_account_expense_id', 'supplier_taxes_id')
        and model_id in
        (select id from ir_model where model='product_product');
        """
        )

        self._cr.execute(
            """UPDATE ir_model_fields set protect_update='0'
        where name like '____id' ;
        """
        )
        return res


class IrModelSynchroLog(models.Model):
    _name = "ir.model.synchro.log"
    _order = "timestamp desc, id desc"

    timestamp = fields.Datetime("Timestamp", copy=False)
    model = fields.Char("Model")
    res_id = fields.Integer("Model ID")
    errmsg = fields.Char("Error message", copy=False)

    @api.model
    def pretty_print(self, values):  # pragma: no cover
        def to_str(obj):
            x = str(obj)
            return obj.id if hasattr(obj, "id") else str(x) if (
                (hasattr(obj, "__len__") or isinstance(obj, (date, datetime)))
                and len(x) < 512) else "[...]"

        if isinstance(values, dict):
            return (
                json.dumps(
                    {
                        k + "_id" if hasattr(v, "id") else k: (
                            "[...]" if k and k.startswith("image")
                            else v[0:60] + "[...]" if isinstance(v, str) and len(v) > 64
                            else v
                        )
                        for k, v in values.items()
                    },
                    default=to_str,
                    indent=2,
                )
                .replace(": false", ": False")
                .replace(": true", ": True")
            )
        elif isinstance(values, (date, datetime)):
            return "\"" + str(values) + "\""
        return json.dumps(values, indent=2)

    def logger(self, vmodel, rec, errmsg, logrec=None, id=None):
        now = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        res_id = rec and rec.id or id or False
        if not isinstance(res_id, (int, long)):
            res_id = False
        if logrec:
            vals = {
                "timestamp": now,
                "errmsg": (logrec.errmsg or "") + "\n\n" + (errmsg or ""),
            }
            if res_id:
                vals["res_id"] = res_id
            logrec.write(vals)
        else:
            errmsg = errmsg or _("No Error")
            logrec = self.create(
                {
                    "timestamp": now,
                    "model": vmodel or "",
                    "res_id": res_id,
                    "errmsg": errmsg,
                }
            )
        if rec and hasattr(rec, "timestamp") and hasattr(rec, "errmsg"):
            rec.write({"timestamp": now, "errmsg": errmsg})
        # self.env.cr.commit()  # pylint: disable=invalid-commit
        return logrec

    def purge_log(self):
        for day in (15, 8, 7, 5, 3, 2, 1):
            last = (datetime.today() - timedelta(day)).strftime("%Y-%m-%d %H:%M:%S")
            domain = [("timestamp", ">=", last)]
            nrecs = self.search_count(domain)
            domain = [("timestamp", "<", last)]
            if nrecs < 10000:
                break
        max_recs_per_session = 1000
        for rec in self.search(domain, order="timestamp desc"):
            rec.unlink()
            max_recs_per_session -= 1
            if not max_recs_per_session:
                break
