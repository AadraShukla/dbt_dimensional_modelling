"""
Generate a synthetic Olist Brazilian E-commerce dataset.

The real Olist dataset lives on Kaggle and requires an account to download.
To keep this project 100% free and reproducible with zero external accounts,
this script generates a statistically similar dataset with the SAME schema
(same 9 tables, same column names) so every dbt model works unchanged.

Stdlib only -- no pandas/numpy required.

Usage:
    python scripts/generate_olist_data.py
Outputs CSVs into data/raw/.
"""
from __future__ import annotations

import csv
import os
import random
import string
from datetime import datetime, timedelta

random.seed(42)

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.normpath(os.path.join(HERE, "..", "data", "raw"))
os.makedirs(RAW, exist_ok=True)

# ---- scale knobs (kept modest so dbt runs in seconds) -------------------------
N_CUSTOMERS = 4000
N_SELLERS = 300
N_PRODUCTS = 800
N_ORDERS = 9000

BR_STATES = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "DF", "GO", "ES", "PE", "CE"]
CITIES = {
    "SP": ["sao paulo", "campinas", "santos", "guarulhos"],
    "RJ": ["rio de janeiro", "niteroi", "duque de caxias"],
    "MG": ["belo horizonte", "uberlandia", "contagem"],
    "RS": ["porto alegre", "caxias do sul"],
    "PR": ["curitiba", "londrina"],
    "SC": ["florianopolis", "joinville"],
    "BA": ["salvador", "feira de santana"],
    "DF": ["brasilia"],
    "GO": ["goiania"],
    "ES": ["vitoria", "vila velha"],
    "PE": ["recife"],
    "CE": ["fortaleza"],
}
CATEGORIES = [
    ("cama_mesa_banho", "bed_bath_table"),
    ("beleza_saude", "health_beauty"),
    ("esporte_lazer", "sports_leisure"),
    ("informatica_acessorios", "computers_accessories"),
    ("moveis_decoracao", "furniture_decor"),
    ("utilidades_domesticas", "housewares"),
    ("relogios_presentes", "watches_gifts"),
    ("telefonia", "telephony"),
    ("automotivo", "auto"),
    ("brinquedos", "toys"),
    ("cool_stuff", "cool_stuff"),
    ("perfumaria", "perfumery"),
]
PAYMENT_TYPES = ["credit_card", "boleto", "voucher", "debit_card"]
ORDER_STATUS = (
    ["delivered"] * 88
    + ["shipped"] * 4
    + ["canceled"] * 3
    + ["processing"] * 2
    + ["invoiced"] * 2
    + ["unavailable"] * 1
)

START = datetime(2017, 1, 1)
END = datetime(2018, 8, 31)


def hexid(n: int = 32) -> str:
    return "".join(random.choices(string.hexdigits.lower()[:16], k=n))


def zip_prefix() -> int:
    return random.randint(1000, 99999)


def rand_dt(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def fmt(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""


def write(name: str, header: list[str], rows: list[list]) -> None:
    path = os.path.join(RAW, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  wrote {name:45s} {len(rows):>7,} rows")


def main() -> None:
    print(f"Generating synthetic Olist data into {RAW}")

    # ---- geolocation + customers + sellers ----------------------------------
    geo_rows, zips = [], set()
    for state in BR_STATES:
        for city in CITIES[state]:
            for _ in range(8):
                z = zip_prefix()
                zips.add(z)
                geo_rows.append([
                    z,
                    round(random.uniform(-33, 5), 6),
                    round(random.uniform(-73, -34), 6),
                    city,
                    state,
                ])
    write(
        "olist_geolocation_dataset.csv",
        ["geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng",
         "geolocation_city", "geolocation_state"],
        geo_rows,
    )
    zip_list = list(zips)

    customers = []
    cust_rows = []
    for _ in range(N_CUSTOMERS):
        state = random.choices(BR_STATES, weights=[40, 14, 12, 6, 6, 5, 4, 3, 3, 2, 3, 2])[0]
        city = random.choice(CITIES[state])
        cid = hexid()
        uid = hexid()
        z = random.choice(zip_list)
        customers.append(cid)
        cust_rows.append([cid, uid, z, city, state])
    write(
        "olist_customers_dataset.csv",
        ["customer_id", "customer_unique_id", "customer_zip_code_prefix",
         "customer_city", "customer_state"],
        cust_rows,
    )

    sellers = []
    seller_rows = []
    for _ in range(N_SELLERS):
        state = random.choice(BR_STATES)
        sid = hexid()
        sellers.append(sid)
        seller_rows.append([sid, random.choice(zip_list), random.choice(CITIES[state]), state])
    write(
        "olist_sellers_dataset.csv",
        ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"],
        seller_rows,
    )

    # ---- products + category translation ------------------------------------
    products = []
    prod_rows = []
    prod_cat = {}
    for _ in range(N_PRODUCTS):
        pid = hexid()
        cat_pt, _cat_en = random.choice(CATEGORIES)
        prod_cat[pid] = cat_pt
        products.append(pid)
        prod_rows.append([
            pid, cat_pt,
            random.randint(20, 60), random.randint(100, 1000), random.randint(1, 6),
            random.randint(100, 30000), random.randint(5, 100),
            random.randint(5, 100), random.randint(5, 100),
        ])
    write(
        "olist_products_dataset.csv",
        ["product_id", "product_category_name", "product_name_lenght",
         "product_description_lenght", "product_photos_qty", "product_weight_g",
         "product_length_cm", "product_height_cm", "product_width_cm"],
        prod_rows,
    )
    write(
        "product_category_name_translation.csv",
        ["product_category_name", "product_category_name_english"],
        [[pt, en] for pt, en in CATEGORIES],
    )

    # ---- orders + items + payments + reviews --------------------------------
    order_rows, item_rows, pay_rows, review_rows = [], [], [], []
    for _ in range(N_ORDERS):
        oid = hexid()
        cust = random.choice(customers)
        status = random.choice(ORDER_STATUS)
        purchase = rand_dt(START, END)
        approved = purchase + timedelta(hours=random.randint(1, 48))
        if status == "delivered":
            carrier = approved + timedelta(days=random.randint(1, 5))
            delivered = carrier + timedelta(days=random.randint(1, 20))
        else:
            carrier = approved + timedelta(days=random.randint(1, 5)) if status in ("shipped",) else None
            delivered = None
        estimated = purchase + timedelta(days=random.randint(10, 40))
        order_rows.append([
            oid, cust, status, fmt(purchase), fmt(approved),
            fmt(carrier), fmt(delivered), fmt(estimated),
        ])

        # items (1-3 per order)
        n_items = random.choices([1, 2, 3], weights=[70, 22, 8])[0]
        order_total = 0.0
        for i in range(1, n_items + 1):
            pid = random.choice(products)
            sid = random.choice(sellers)
            price = round(random.uniform(10, 800), 2)
            freight = round(random.uniform(5, 60), 2)
            order_total += price + freight
            item_rows.append([
                oid, i, pid, sid, fmt(approved + timedelta(days=2)), price, freight,
            ])

        # payments (usually one)
        n_pay = random.choices([1, 2], weights=[90, 10])[0]
        remaining = order_total
        for seq in range(1, n_pay + 1):
            ptype = random.choices(PAYMENT_TYPES, weights=[74, 19, 5, 2])[0]
            installments = random.randint(1, 10) if ptype == "credit_card" else 1
            val = round(remaining if seq == n_pay else remaining / 2, 2)
            remaining -= val
            pay_rows.append([oid, seq, ptype, installments, val])

        # reviews (~80% of delivered orders)
        if status == "delivered" and random.random() < 0.8:
            score = random.choices([1, 2, 3, 4, 5], weights=[8, 5, 9, 25, 53])[0]
            created = (delivered or approved) + timedelta(days=random.randint(0, 3))
            review_rows.append([
                hexid(), oid, score, "", "",
                created.strftime("%Y-%m-%d %H:%M:%S"),
                (created + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
            ])

    write(
        "olist_orders_dataset.csv",
        ["order_id", "customer_id", "order_status", "order_purchase_timestamp",
         "order_approved_at", "order_delivered_carrier_date",
         "order_delivered_customer_date", "order_estimated_delivery_date"],
        order_rows,
    )
    write(
        "olist_order_items_dataset.csv",
        ["order_id", "order_item_id", "product_id", "seller_id",
         "shipping_limit_date", "price", "freight_value"],
        item_rows,
    )
    write(
        "olist_order_payments_dataset.csv",
        ["order_id", "payment_sequential", "payment_type",
         "payment_installments", "payment_value"],
        pay_rows,
    )
    write(
        "olist_order_reviews_dataset.csv",
        ["review_id", "order_id", "review_score", "review_comment_title",
         "review_comment_message", "review_creation_date", "review_answer_timestamp"],
        review_rows,
    )

    print("Done.")


if __name__ == "__main__":
    main()
