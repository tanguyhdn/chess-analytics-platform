"""
chess_dbt_dag.py
DAG Airflow — dbt run + test + Elementary
Schedule : quotidien à 7h UTC (après ingestion)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# ─── Default args ─────────────────────────────────────
default_args = {
    "owner":            "chess-analytics",
    "depends_on_past":  False,
    "email_on_failure": False,
    "email_on_retry":   False,
    "retries":          1,
    "retry_delay":      timedelta(minutes=5),
}

DBT_CMD = "cd /opt/airflow/dbt/chess_analytics && dbt"
PROFILES_DIR = "--profiles-dir /opt/airflow/dbt"

# ─── DAG ──────────────────────────────────────────────
with DAG(
    dag_id="chess_dbt_pipeline",
    default_args=default_args,
    description="dbt run + test + docs + Elementary monitoring",
    schedule="0 7 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["chess", "dbt", "transformation"],
) as dag:

    # ─── Task 1 : dbt deps ────────────────────────────
    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"{DBT_CMD} deps {PROFILES_DIR}",
    )

    # ─── Task 2 : dbt run ─────────────────────────────
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"{DBT_CMD} run {PROFILES_DIR}",
    )

    # ─── Task 3 : dbt test ────────────────────────────
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"{DBT_CMD} test {PROFILES_DIR}",
    )

    # ─── Task 4 : dbt source freshness ───────────────
    dbt_freshness = BashOperator(
        task_id="dbt_source_freshness",
        bash_command=f"{DBT_CMD} source freshness {PROFILES_DIR}",
    )

    # ─── Task 5 : dbt docs generate ──────────────────
    dbt_docs = BashOperator(
        task_id="dbt_docs_generate",
        bash_command=f"{DBT_CMD} docs generate {PROFILES_DIR}",
    )

    # ─── Dépendances ──────────────────────────────────
    dbt_deps >> dbt_run >> dbt_test >> dbt_freshness >> dbt_docs