"""
Airflow DAG that orchestrates the Olist warehouse end to end on a schedule:

    generate raw data  ->  dbt deps  ->  dbt run  ->  dbt test  ->  dbt docs

Each dbt step is a BashOperator -- the standard, adapter-agnostic way to run
dbt Core from Airflow. Set PROJECT_DIR below (or the OLIST_PROJECT_DIR env var)
to the absolute path of this repo on the machine running the scheduler.

NOTE: Apache Airflow does not run natively on Windows. Run this DAG under
WSL2, Linux, or the official Airflow Docker image (see docker-compose.yaml).
The dbt models themselves run fine on Windows via `dbt run` directly.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = os.environ.get("OLIST_PROJECT_DIR", "/opt/airflow/olist")
DBT_DIR = f"{PROJECT_DIR}/olist_dbt"

# dbt reads profiles.yml from the project dir; venv holds the dbt executable.
DBT_ENV = (
    f"cd {DBT_DIR} && export DBT_PROFILES_DIR={DBT_DIR} && "
    f"export PATH={PROJECT_DIR}/.venv/bin:$PATH &&"
)

default_args = {
    "owner": "data-engineering",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="olist_dbt_warehouse",
    description="Build the Olist star schema with dbt on DuckDB",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule="0 6 * * *",  # daily at 06:00
    catchup=False,
    tags=["dbt", "duckdb", "dimensional-modelling"],
) as dag:

    generate_data = BashOperator(
        task_id="generate_raw_data",
        bash_command=f"cd {PROJECT_DIR} && python scripts/generate_olist_data.py",
    )

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"{DBT_ENV} dbt deps",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"{DBT_ENV} dbt run",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"{DBT_ENV} dbt test",
    )

    dbt_docs = BashOperator(
        task_id="dbt_docs_generate",
        bash_command=f"{DBT_ENV} dbt docs generate",
    )

    generate_data >> dbt_deps >> dbt_run >> dbt_test >> dbt_docs
