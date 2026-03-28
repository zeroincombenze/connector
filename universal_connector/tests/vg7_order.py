#! /usr/bin/python3
"""
Simulate VG7: send order
"""
import os.path
import sys
import csv
try:
    from clodoo import clodoo
except ImportError:
    import clodoo

SALE_ORDER_LINE_1_1 = {
    "id": 3451,
    "iva": 22,
    "weight": 13,
    "product_name": "grafica . smart (ps.g)",
    "product_id": 300000184,
    "unitary_price": 0.42508196721311,
    "job_name": """Codice: cpb
grafica . smart (ps.g)
concorso spese: impaginata su tracciato pf (file fornito dal cliente in vettoriale)
Quantit\\xe0: 1""",
    "quantity": 100
}
SALE_ORDER_LINE_1_2 = {
    "id": 3452,
    "iva": 22,
    "weight": 0,
    "product_name": "clich\\xe9 serigrafia 1col (smart)",
    "product_id": 300000181,
    "unitary_price": 0,
    "job_name": """Codice: cs1s
clich\\xe9 serigrafia 1col (smart)
concorso spese: impaginata su tracciato pf (file fornito dal cliente in vettoriale)
quantit\\xe0: 1
tipologia: nuovo
nota: .
(necessario per la creazione del pf: visibile su ddt, no consegna)""",
    "quantity": 1
}
SALE_ORDER_LINE_1_3 = {
    "id": 3453,
    "iva": 22,
    "weight": 0,
    "product_name": "serigrafia combi cliche e ink (smart)",
    "product_id": 300000153,
    "unitary_price": 10.0,
    "job_name": """Codice: sccis
serigrafia combi cliche' e ink
Quantit\\xe0: 1
sconto: 1 cliche' per 2 referenze bag""",
    "quantity": 1
}
SALE_ORDER_LINE_1_4 = {
    "id": 3454,
    "iva": 22,
    "weight": 0,
    "product_name": "mix natural strong (e.n1) . cordino paper bag (e)",
    "product_id": 300000121,
    "unitary_price": -10.0,
    "job_name": """Codice: cpb
mix natural strong (e.n1) . cordino paper bag (e)
Prodotto: mix natural strong (e.n1) . cordino paper bag (e)
bianco spl (wl) 540x140x500 (120pf) (epbc.mns.n1): 100
unit\\xe0 di misura: pezzi""",
    "quantity": 1
}
SALE_ORDER_LINE_1_5 = {
    "id": 3455,
    "iva": 22,
    "weight": 0,
    "product_name": "Spedizione",
    "product_id": 100000011,
    "unitary_price": 0,
    "job_name": "Spedizione",
    "quantity": 1
}

SALE_ORDER_1 = {
    "shipping": {
        "shipping_name": "",
        "shipping_postal_code": "82024",
        "shipping_city": "Colle Sannita",
        "shipping_street": "viale meomartini",
        "shipping_region": "BENEVENTO",
        "shipping_country": "Italia",
        "shipping_telephone": "",
        "shipping_street_number": "48",
        "shipping_email": "",
        "shipping_company": "mary & frank",
        "shipping_surename": ""
    },
    "total_taxed": 51.86,
    "order_number": "26-O261361",
    "iva": 22,
    "billing": {
        "billing_region": "BENEVENTO",
        "billing_company": "mary & frank",
        "billing_piva": "01178050629",
        "billing_cf": "01178050629",
        "billing_email": "",
        "billing_street": "viale meomartini",
        "billing_telephone": "",
        "billing_street_number": "48",
        "billing_surename": "",
        "billing_name": "",
        "billing_postal_code": "82024",
        "billing_country": "Italia",
        "billing_city": "Colle Sannita"
    },
    "total_taxable": 42.51,
    "name": "test peso odoo su oc",
    "order_state": 2,
    "order_rows": [
        SALE_ORDER_LINE_1_1,
        SALE_ORDER_LINE_1_2,
        SALE_ORDER_LINE_1_3,
        SALE_ORDER_LINE_1_4,
        SALE_ORDER_LINE_1_5
    ],
    "customer_id": 425,
    "order_id": 1361,
    "id": 1361,
    "date": "2026-03-26",
    "agent_id": 90
}


class ExtTestEnv(object):
    def __init__(self, config=None, database=None, reset_prod=False):
        if os.path.isfile(config):
            self.config = config
        else:
            print("File %s not found!" % config)
        self.database = database
        self.ctx = {}
        self.user = False
        self.reset_prod = reset_prod

    def connect_user(self):
        uid, ctx = clodoo.oerp_set_env(
            confn=self.config,
            db=self.database,
            ctx=self.ctx,
        )
        if not uid:
            raise IOError("DB %s not connected via json/xmlrpc!" % self.database)
        self.user = self.ctx["user"]

    def trigger_order(self):
        order = SALE_ORDER_1
        ext_id = order["id"]
        fqn = "/home/odoo/10.0/connector/universal_connector/tests/data/orders.csv"
        with open(fqn, "wb") as fd:
            writer = csv.writer(fd)
            keys = list(order.keys())
            writer.writerow(keys)
            writer.writerow(order.values())
        fqn = "/home/odoo/10.0/connector/universal_connector/tests/data/orders.line.csv"
        with open(fqn, "wb") as fd:
            writer = csv.writer(fd)
            keys = list(SALE_ORDER_LINE_1_1.keys())
            writer.writerow(keys)
            for line in (
                    SALE_ORDER_LINE_1_1,
                    SALE_ORDER_LINE_1_2,
                    SALE_ORDER_LINE_1_3,
                    SALE_ORDER_LINE_1_4,
                    SALE_ORDER_LINE_1_5,
            ):
                writer.writerow(line.values())
                if self.reset_prod:
                    product_id = clodoo.searchL8(
                        self.ctx,
                        "product.product",
                        [("vg7_id", "=", line["product_id"])])
                    if product_id:
                        try:
                            clodoo.unlinkL8(
                                self.ctx, "product.product", product_id)
                        except BaseException:
                            pass

        id = clodoo.executeL8(
            self.ctx,
            "ir.model.synchro", "trigger_one_record", "orders", "vg7", ext_id)
        # for line in (
        #         SALE_ORDER_LINE_1_1,
        #         SALE_ORDER_LINE_1_2,
        #         SALE_ORDER_LINE_1_3,
        #         SALE_ORDER_LINE_1_4,
        #         SALE_ORDER_LINE_1_5,
        # ):
        #     ext_id = line["id"]
        #     clodoo.executeL8(
        #         self.ctx,
        #         "ir.model.synchro",
        #         "trigger_one_record",
        #         "orders.line",
        #         "vg7", ext_id)
        return id

    def send_order(self):
        self.connect_user()
        id = self.trigger_order()
        return 0 if id > 0 else 1


def main(cli_args=[]):
    param = ""
    help = False
    config = "/home/odoo/clodoo/confs/odoo10.conf"
    database = "paperservice"
    reset_prod = False
    for arg in cli_args:
        if arg.endswith("--reset"):
            reset_prod = True
        elif arg.startswith("-"):
            if "h" in arg:
                help = True
            if arg.endswith("c"):
                param = "config"
            if arg.endswith("d"):
                param = "database"
        elif param == "config":
            config = arg
        elif param == "database":
            database = arg
        else:
            pass
    if help:
        print("usage: vg7_order -c CONFIG -d DATABASE --reset")
        exit(0)
    Conn = ExtTestEnv(config=config, database=database, reset_prod=reset_prod)
    return Conn.send_order()


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
