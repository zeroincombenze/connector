#
# Copyright 2018-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import os
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class SynchroApi(models.Model):
    """API for Odoo Backends"""

    _inherit = "synchro.api"

    def manage_alias(self, vals):
        for old, new in (
            ("country", "country_id"),
            ("region", "region_id"),
            ("vg7_um", "um_id"),
            ("tax_id", "tax_code_id"),
            ("payment", "payment_id"),
        ):
            if old in vals and new not in vals:
                vals[new] = vals[old]
        return vals

    def adapt_response_vg7(self, values, dir_mapper, ext_id):
        Cache = self.env["ir.model.synchro.cache"]
        vmodel = dir_mapper.name
        ext_model = dir_mapper.counterpart_name
        backend = dir_mapper.synchro_channel_id
        ext_key_id = dir_mapper.counterpart_pk
        row_billing = {}
        row_shipping = {}
        row_contact = {}
        for key, value in values.copy().items():
            if isinstance(value, dict):
                if key == "billing":
                    row_billing.update(value)
                    del values[key]
                    continue
                elif key == "shipping":
                    row_shipping.update(value)
                    del values[key]
                    continue
                elif key == "contact":
                    row_contact.update(value)
                    del values[key]
                    continue
            if key.startswith("billing_"):
                row_billing[key] = value
            elif key.startswith("shipping_"):
                row_shipping[key] = value
            elif key.startswith("contact_"):
                row_contact[key] = value
        values = self.manage_alias(values)
        if vmodel == "res.partner":
            if row_billing:
                invoice_vals = {}
                for key, value in row_billing.items():
                    if key.startswith("billing_"):
                        key = key[8:]
                    invoice_vals[key] = value
                    if key not in values:
                        values[key] = value
                if invoice_vals:
                    invoice_vals = self.manage_alias(invoice_vals)
                    if ext_key_id not in invoice_vals:
                        invoice_vals[ext_key_id] = values[ext_key_id]
                    invoice_vals[":type"] = "invoice"
                    Cache.que_push(
                        backend, "push", ext_model, invoice_vals, 2, {}, prio=3
                    )
            if row_shipping:
                shipping_vals = {}
                for key, value in row_shipping.items():
                    if key == "customer_shipping_id":
                        pass
                    elif key.startswith("shipping_"):
                        key = key[9:]
                    shipping_vals[key] = value
                if shipping_vals:
                    shipping_vals = self.manage_alias(shipping_vals)
                    shipping_vals[":type"] = "delivery"
                    Cache.que_push(
                        backend,
                        "push",
                        "customers_shipping_addresses",
                        shipping_vals,
                        2,
                        {},
                        prio=3,
                    )
            # if row_contact:
            #     values["contact"] = row_contact
        return values

    def adapt_responses_vg7(self, res, dir_mapper, ext_id):
        new_res = []
        for item in res:
            new_res.append(self.adapt_response_vg7(item, dir_mapper, ext_id))
        return new_res

    def get_response_vg7_https(
        self, session, dir_mapper, ext_id=False, endpoint=None, fields=None
    ):
        ext_model = dir_mapper.counterpart_name
        endpoint = session["data_endpoint"]
        if ext_id:
            endpoint = os.path.join(endpoint, ext_model, str(ext_id))
        else:
            endpoint = os.path.join(endpoint, ext_model)
        res = self.get_response_https(
            session, dir_mapper, ext_id=ext_id, endpoint=endpoint
        )
        if res:
            res[dir_mapper.counterpart_pk] = ext_id
            return [self.adapt_response_vg7(res, dir_mapper, ext_id)]
        return res

    def get_response_vg7_http(
        self, session, dir_mapper, ext_id=False, endpoint=None, fields=None
    ):
        return self.get_response_vg7_https(
            session, dir_mapper, ext_id=ext_id, endpoint=endpoint, fields=fields
        )

    def get_response_vg7_csv(
        self, session, dir_mapper, ext_id=False, endpoint=None, fields=None
    ):
        res = self.get_response_csv(
            session, dir_mapper, ext_id=ext_id, endpoint=endpoint, fields=fields
        )
        return self.adapt_response_vg7(res, dir_mapper, ext_id)
