#
# Copyright 2018-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import os
import csv
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class SynchroApi(models.Model):
    """API for Odoo Backends"""

    _inherit = "synchro.api"

    def csv_default(self, backend):
        return ["csv", 0, "demo", "admin", "admin", "", ""]

    def get_pypi_name_csv(self):
        return "csv"

    def csv_connect(self, exchange_path):
        session = self.init_sesssion()
        session["cnx_lgi"] = True
        session["exchange_path"] = (
            exchange_path if os.path.isdir(exchange_path) else False
        )
        return session

    def csv_login(self, cnx, backend):
        cnx["session"] = True
        return cnx

    def csv_session(self, backend):
        return self.csv_login(
            self.csv_connect(backend.exchange_path),
            backend,
        )

    def get_response_csv(
        self, session, synchro_model, ext_id=False, endpoint=None, fields=None
    ):
        backend = synchro_model.synchro_channel_id
        exchange_path = backend.exchange_path
        ext_key_id = synchro_model.counterpart_pk
        file_csv = os.path.join(exchange_path, synchro_model.counterpart_name + ".csv")
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

    def get_record_list_csv(self, session, synchro_model):
        backend = synchro_model.synchro_channel_id
        exchange_path = backend.exchange_path
        ext_key_id = synchro_model.counterpart_pk
        file_csv = os.path.join(exchange_path, synchro_model.counterpart_name + ".csv")
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
