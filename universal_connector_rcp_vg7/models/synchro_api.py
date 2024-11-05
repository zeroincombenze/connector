#
# Copyright 2019-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
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

    def adapt_response_vg7(self, values, vmodel):
        row_billing = {}
        row_shipping = {}
        row_contact = {}
        for key, value in values.items():
            if key.startswith("billing_"):
                row_billing[key] = value
            elif key.startswith("shipping_"):
                row_shipping[key] = value
            elif key.startswith("contact_"):
                row_contact[key] = value
        if row_billing:
            if vmodel == "res.partner.invoice":
                values = row_billing
            else:
                values["billing"] = row_billing
        if row_shipping:
            if vmodel == "res.partner.shipping":
                for nm in ("customer_shipping_id", "customer_id"):
                    row_shipping[nm] = values[nm]
                values = row_shipping
            else:
                values["shipping"] = row_shipping
        if row_contact:
            values["contact"] = row_contact
        return values

    def adapt_responses_vg7(self, res, backend, ext_model):
        SynchroModel = self.env["synchro.channel.model"]
        model_rec = SynchroModel.get_model_from_ext(backend, ext_model)
        new_res = []
        for item in res:
            new_res.append(self.adapt_response_vg7(item, model_rec.name))
        return new_res

    def get_response_vg7_https(
        self, session, backend, ext_model, ext_id=False, endpoint=None
    ):
        endpoint = session["data_endpoint"]
        if ext_id:
            endpoint = os.path.join(endpoint, ext_model, str(ext_id))
        else:
            endpoint = os.path.join(endpoint, ext_model)
        res = self.get_response_https(
            session, backend, ext_model, ext_id=ext_id, endpoint=endpoint
        )
        if res:
            model_rec = self.env["synchro.channel.model"].get_model_from_ext(
                backend, ext_model
            )
            res[model_rec.counterpart_pk] = ext_id
            return [res]
        return res

    def get_response_vg7_http(
        self, session, backend, ext_model, ext_id=False, endpoint=None
    ):
        return self.get_response_vg7_https(
            session, backend, ext_model, ext_id=ext_id, endpoint=endpoint
        )

    def get_response_vg7_csv(
        self, session, backend, ext_model, ext_id=False, endpoint=None
    ):
        res = self.get_response_csv(
            session, backend, ext_model, ext_id=ext_id, endpoint=endpoint
        )
        return res
