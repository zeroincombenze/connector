#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import os
import csv

from odoo import models
from python_plus import _u


class SynchroApi(models.Model):
    """API for Odoo Backends"""

    _inherit = "synchro.api"

    def simple_cast(self, value):
        """Execute the simple field casting. From remote counterparty all field may
        be all strings; here may be converted to integer or list or dictionary"""
        if isinstance(value, (list, tuple)):
            new_vals = []
            for i, x in enumerate(value):
                new_vals.append(self.adapt_values(x))
            value = new_vals
        elif isinstance(value, str):
            try:
                if value.isdigit() and not value.startswith("0") and len(value) < 10:
                    value = int(value)
                elif value.startswith("[") and value.endswith("]"):
                    value = self.adapt_values(eval(value))
                elif value.startswith("{") and value.endswith("}"):
                    value = self.adapt_values(eval(value))
            except BaseException:  # pragma: no cover
                pass
        return _u(value)

    def csv_connect(self, exchange_path):
        session = self.init_session()
        session["cnx_lgi"] = True
        session["exchange_path"] = (
            exchange_path if os.path.isdir(exchange_path) else False
        )
        return session

    def csv_authorize(self, cnx, backend):
        cnx["session"] = True
        return cnx

    def csv_session(self, backend):
        return self.csv_authorize(
            self.csv_connect(backend.exchange_path),
            backend,
        )

    def get_response_csv(
        self, session, dir_mapper, ext_id=False, endpoint=None, fields=None
    ):
        backend = dir_mapper.backend_id
        exchange_path = backend.exchange_path
        ext_key_id = dir_mapper.counterpart_pk
        file_csv = os.path.join(exchange_path, dir_mapper.counterpart_name + ".csv")
        res = []
        if not os.path.isfile(file_csv):
            return res
        with open(file_csv, "r") as fd:
            hdr = False
            reader = csv.DictReader(fd, fieldnames=[], restkey="undef_name")
            for line in reader:
                row = line["undef_name"]
                if not hdr:
                    row_id = 0
                    hdr = row
                    continue
                row_id += 1
                row_res = dict(zip(hdr, [self.simple_cast(x) for x in row]))
                if ext_key_id not in row_res:
                    row_res[ext_key_id] = row_id
                else:
                    row_id = row_res[ext_key_id]
                if ext_id and row_res[ext_key_id] != ext_id:
                    continue
                if ext_id:
                    res = [row_res]
                    break
                res.append(row_res)
        return res

    def get_record_list_csv(self, session, dir_mapper):
        backend = dir_mapper.backend_id
        exchange_path = backend.exchange_path
        ext_key_id = dir_mapper.counterpart_pk
        file_csv = os.path.join(exchange_path, dir_mapper.counterpart_name + ".csv")
        res = []
        if not os.path.isfile(file_csv):
            return res
        with open(file_csv, "r") as fd:
            hdr = False
            reader = csv.DictReader(fd, fieldnames=[], restkey="undef_name")
            for line in reader:
                row = line["undef_name"]
                if not hdr:
                    row_id = 0
                    hdr = row
                    continue
                row_id += 1
                row_res = dict(zip(hdr, [self.simple_cast(x) for x in row]))
                if ext_key_id not in row_res:
                    row_res[ext_key_id] = row_id
                else:
                    row_id = row_res[ext_key_id]
                res.append(row_id)
        return res

    def get_ext_id_of_ext_ref_odoo_csv(self, session, dir_mapper, ext_id):
        backend = dir_mapper.backend_id
        exchange_path = backend.exchange_path
        ext_key_id = "id"
        file_csv = os.path.join(exchange_path, "ir.model.data.csv")
        res = []
        if not os.path.isfile(file_csv):
            return res
        ext_model = dir_mapper.counterpart_name
        with open(file_csv, "r") as fd:
            hdr = False
            reader = csv.DictReader(fd, fieldnames=[], restkey="undef_name")
            for line in reader:
                row = line["undef_name"]
                if not hdr:
                    row_id = 0
                    hdr = row
                    continue
                row_id += 1
                row_res = dict(zip(hdr, [self.simple_cast(x) for x in row]))
                if ext_key_id not in row_res:
                    row_res[ext_key_id] = row_id
                else:
                    row_id = row_res[ext_key_id]
                if row_res["model"] == ext_model and ext_id == row_res["res_id"]:
                    res.append(row_id)
                    break
        return res
