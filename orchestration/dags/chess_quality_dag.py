"""
chess_quality_dag.py
DAG Airflow — Great Expectations validation
Schedule : quotidien à 8h UTC (après dbt)
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

# ─── DAG ──────────────────────────────────────────────
with DAG(
    dag_id="chess_data_quality",
    default_args=default_args,
    description="Great Expectations validation sur les marts BigQuery",
    schedule="0 8 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["chess", "quality", "great-expectations"],
) as dag:

    # ─── Task 1 : Validation GX ───────────────────────
    gx_validation = BashOperator(
        task_id="gx_validation",
        bash_command="cd /opt/airflow && python docs/data_quality/gx_validation.py",
    )

    # ─── Task 2 : Rapport Elementary ──────────────────
    elementary_report = BashOperator(
        task_id="elementary_report",
        bash_command="""
        cd /opt/airflow/dbt/chess_analytics && \
        edr report \
            --profiles-dir /opt/airflow/dbt \
            --profile-target dev \
            --file-path /opt/airflow/docs/elementary_report.html
        """,
    )

    # ─── Dépendances ──────────────────────────────────
    gx_validation >> elementary_report