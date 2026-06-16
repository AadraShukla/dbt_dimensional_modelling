"""
Streamlit dashboard built directly on the dbt mart layer.

It connects read-only to the same DuckDB file dbt writes to and queries the
star-schema marts (fact_orders, fact_order_items, dim_*). Run *after* `dbt run`:

    streamlit run dashboard/streamlit_app.py
"""
from __future__ import annotations

import os

import duckdb
import pandas as pd
import streamlit as st

DB_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "data", "olist.duckdb")
)

st.set_page_config(page_title="Olist Warehouse", page_icon="📦", layout="wide")


@st.cache_resource
def get_con():
    # read_only so the dashboard never locks the file against dbt.
    return duckdb.connect(DB_PATH, read_only=True)


def q(sql: str) -> pd.DataFrame:
    return get_con().execute(sql).fetchdf()


st.title("📦 Olist E-commerce Warehouse")
st.caption("Star schema built with dbt + DuckDB · dashboard reads the marts layer")

if not os.path.exists(DB_PATH):
    st.error("DuckDB file not found. Run `dbt run` first (see README).")
    st.stop()

# ---- KPI row ----------------------------------------------------------------
kpis = q("""
    select
        count(*)                              as orders,
        sum(total_order_value)                as revenue,
        avg(avg_review_score)                 as avg_review,
        avg(delivery_days)                    as avg_delivery_days
    from main_marts.fact_orders
    where order_status = 'delivered'
""").iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Delivered orders", f"{int(kpis.orders):,}")
c2.metric("Revenue (BRL)", f"R$ {kpis.revenue:,.0f}")
c3.metric("Avg review score", f"{kpis.avg_review:.2f} ★")
c4.metric("Avg delivery days", f"{kpis.avg_delivery_days:.1f}")

st.divider()

# ---- revenue over time ------------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("Monthly revenue")
    monthly = q("""
        select
            date_trunc('month', order_purchase_timestamp) as month,
            sum(total_order_value)                        as revenue
        from main_marts.fact_orders
        group by 1 order by 1
    """)
    st.bar_chart(monthly, x="month", y="revenue")

with right:
    st.subheader("Top product categories by revenue")
    cats = q("""
        select
            p.product_category_name_english as category,
            sum(f.item_total)               as revenue
        from main_marts.fact_order_items f
        join main_marts.dim_product p on f.product_sk = p.product_sk
        group by 1 order by 2 desc limit 10
    """)
    st.bar_chart(cats, x="category", y="revenue", horizontal=True)

st.divider()

# ---- geography + sellers ----------------------------------------------------
left2, right2 = st.columns(2)

with left2:
    st.subheader("Revenue by customer state")
    states = q("""
        select
            c.customer_state as state,
            sum(f.total_order_value) as revenue
        from main_marts.fact_orders f
        join main_marts.dim_customer c on f.customer_sk = c.customer_sk
        group by 1 order by 2 desc
    """)
    st.bar_chart(states, x="state", y="revenue")

with right2:
    st.subheader("Payment installments distribution")
    inst = q("""
        select max_installments as installments, count(*) as orders
        from main_marts.fact_orders
        where max_installments > 0
        group by 1 order by 1
    """)
    st.bar_chart(inst, x="installments", y="orders")

st.divider()
st.subheader("Top 10 sellers by revenue")
sellers = q("""
    select
        s.seller_id,
        s.seller_state,
        count(distinct f.order_id) as orders,
        sum(f.item_total)          as revenue
    from main_marts.fact_order_items f
    join main_marts.dim_seller s on f.seller_sk = s.seller_sk
    group by 1, 2 order by revenue desc limit 10
""")
st.dataframe(sellers, use_container_width=True, hide_index=True)
