# Olist E-commerce Data Warehouse — dbt + Dimensional Modelling

A production-shaped analytics warehouse built on the **Olist Brazilian
E-commerce** dataset. Raw CSVs are transformed through a **raw → staging →
marts** dbt pipeline into a **star schema**, validated with dbt tests,
documented with dbt docs, orchestrated by Airflow, and visualised in Streamlit.

**100% free & local — no Kaggle, Snowflake, or any account required.**
The stack is dbt Core + DuckDB (in-process) + Streamlit, with an optional
Airflow layer via Docker.

---

## Architecture

```
                 ┌────────────────────────────────────────────┐
 generate_       │                  dbt Core                  │
 olist_data.py   │                                            │
      │          │   RAW            STAGING          MARTS     │
      ▼          │  (CSV in     →  (views: cast,  →  (tables:  │
 data/raw/*.csv  │   DuckDB)       rename, clean)    star      │
                 │   sources       stg_*            schema)    │
                 └────────────────────────────────────────────┘
                                                      │
                          ┌───────────────────────────┴───────────┐
                          ▼                                        ▼
                  ⭐ Star schema                          📊 Streamlit dashboard
              fact_orders (order grain)                   (reads marts read-only)
              fact_order_items (line grain)
              dim_customer / dim_product /
              dim_seller / dim_date  (conformed)
```

The whole flow is scheduled by an **Airflow DAG**
(`airflow/dags/olist_dbt_dag.py`): `generate → dbt run → dbt test → dbt docs`.

### Star schema

| Table              | Grain                       | Type      | Keys |
|--------------------|-----------------------------|-----------|------|
| `fact_orders`      | one row per **order**       | fact      | `customer_sk`, `order_date_sk` |
| `fact_order_items` | one row per **order line**  | fact      | `customer_sk`, `product_sk`, `seller_sk`, `order_date_sk` |
| `dim_customer`     | one row per customer        | dimension | `customer_sk` |
| `dim_product`      | one row per product         | dimension | `product_sk` |
| `dim_seller`       | one row per seller          | dimension | `seller_sk` |
| `dim_date`         | one row per calendar day    | dimension | `date_sk` |

Two facts share **conformed dimensions** — the textbook pattern that lets you
slice both order-level and line-level measures by the same customer / date.

---

## Quick start (Windows, no accounts)

> Requires **Python 3.11 or 3.12** (dbt does not yet support 3.14). If you only
> have 3.14, install 3.12 with [`uv`](https://github.com/astral-sh/uv):
> `pip install uv && uv python install 3.12`.

```powershell
# 1. create the environment
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. build everything in one shot (generate data → run → test → docs)
powershell -ExecutionPolicy Bypass -File build_all.ps1

# 3. open the dashboard
streamlit run dashboard\streamlit_app.py
```

### Manual steps (any OS)

```bash
python scripts/generate_olist_data.py          # create data/raw/*.csv

cd olist_dbt
export DBT_PROFILES_DIR=$(pwd)                  # profiles.yml lives in-project
dbt run        # build staging views + mart tables
dbt test       # 64 data-quality tests
dbt docs generate && dbt docs serve            # browsable lineage + catalog
```

The warehouse is written to `data/olist.duckdb`. Query it with any DuckDB client:

```sql
select order_status, count(*), sum(total_order_value)
from main_marts.fact_orders group by 1;
```

---

## Layered transformation pattern

| Layer       | Folder              | Materialisation | Responsibility |
|-------------|---------------------|-----------------|----------------|
| **Raw**     | `_sources.yml`      | CSV via DuckDB  | Land source data untouched (the "landing zone"). |
| **Staging** | `models/staging`    | **views**       | 1:1 with sources — rename, cast types, light cleaning. One `stg_` model per source. |
| **Marts**   | `models/marts`      | **tables**      | Business-facing star schema (facts + conformed dims) + `int_` helpers. |

This is the standard architecture every dbt shop uses, and it's the answer to
the senior-DE interview question *"walk me through your transformation layers."*

## Data quality tests (64 total)

- **Generic tests** in YAML: `not_null`, `unique`, `accepted_values`,
  `relationships` (referential integrity between every fact FK and its dim).
- **Singular test**: `tests/assert_fact_orders_value_non_negative.sql`.

```bash
dbt test            # all pass
```

## A note on Slowly Changing Dimensions (SCD)

The dimensions here are **Type 1** (overwrite). dbt's native mechanism for
**Type 2** history is **snapshots** — drop a snapshot in `snapshots/` keyed on
e.g. `customer_id` with `strategy: check`, and dbt maintains `dbt_valid_from` /
`dbt_valid_to` automatically. This repo keeps Type 1 for clarity but the
modelling is snapshot-ready (every dim has a stable natural key + surrogate key).

---

## Orchestration with Airflow

`airflow/dags/olist_dbt_dag.py` runs the pipeline daily at 06:00 as
`BashOperator` tasks. Airflow has **no native Windows support**, so run it under
Docker:

```bash
docker compose up        # Airflow UI at http://localhost:8080 (admin/admin)
```

The dbt models themselves run fine on Windows directly — Airflow is only the
scheduler.

---

## Swapping DuckDB for Snowflake later

Because all logic is in portable dbt SQL, moving to Snowflake (or BigQuery /
Postgres) is just a new `profiles.yml` target + `pip install dbt-snowflake`.
Not a single model needs to change.

## Repo layout

```
scripts/generate_olist_data.py   # synthetic Olist generator (stdlib only)
data/raw/                         # generated source CSVs (git-ignored)
olist_dbt/
  models/staging/                 # stg_* views + sources + tests
  models/marts/                   # facts, dims, int_ models + tests
  macros/                         # local surrogate-key macro (offline)
  tests/                          # singular data test
  profiles.yml                    # DuckDB connection
airflow/dags/olist_dbt_dag.py     # orchestration DAG
dashboard/streamlit_app.py        # BI dashboard on the marts
docker-compose.yaml               # optional Airflow stack
build_all.ps1                     # one-command Windows build
```
