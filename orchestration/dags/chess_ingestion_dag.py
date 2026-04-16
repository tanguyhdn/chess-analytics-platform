"""
chess_ingestion_dag.py
DAG Airflow — Ingestion batch Chess.com → BigQuery
Schedule : quotidien à 6h UTC
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# ─── Default args ─────────────────────────────────────
default_args = {
    "owner":            "chess-analytics",
    "depends_on_past":  False,
    "email_on_failure": False,
    "email_on_retry":   False,
    "retries":          2,
    "retry_delay":      timedelta(minutes=5),
}

# ─── DAG ──────────────────────────────────────────────
with DAG(
    dag_id="chess_daily_ingestion",
    default_args=default_args,
    description="Ingestion batch Chess.com API → BigQuery raw zone",
    schedule="0 6 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["chess", "ingestion", "batch"],
) as dag:

    # ─── Task 1 : Ingestion des joueurs ───────────────
    ingest_players = BashOperator(
        task_id="ingest_players",
        bash_command="cd /opt/airflow && python ingestion/batch/fetch_players.py",
    )

    # ─── Task 2 : Ingestion des parties ───────────────
    ingest_games = BashOperator(
        task_id="ingest_games",
        bash_command="cd /opt/airflow && python ingestion/batch/fetch_games.py",
    )

    # ─── Task 3 : Vérification du volume ──────────────
    check_volume = BashOperator(
        task_id="check_raw_volume",
        bash_command="""
        python -c "
from google.cloud import bigquery
client = bigquery.Client(project='chess-analytics-platform')
result = list(client.query('SELECT COUNT(*) as total FROM \`chess-analytics-platform.chess_raw.raw_games\`'))
total = result[0].total
print(f'raw_games count: {total}')
assert total > 1000, f'Volume trop faible: {total} lignes'
print('Volume check passed')
"
        """,
    )

    # ─── Dépendances ──────────────────────────────────
    ingest_players >> ingest_games >> check_volume