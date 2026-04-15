"""
fetch_games.py
Ingestion batch — Chess.com PubAPI → BigQuery (chess_raw)
Récupère les parties mensuelles des top joueurs et les charge en raw zone.
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
from google.cloud import bigquery

# ─── Config ───────────────────────────────────────────
load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET    = os.getenv("BQ_DATASET_RAW")
USER_AGENT = os.getenv("CHESSCOM_USER_AGENT")

PLAYERS = [
    "magnuscarlsen",
    "hikaru",
    "fabianocaruana",
    "firouzja2003",
    "rpragchess",
]

MONTHS = [
    ("2025", "01"),
    ("2025", "02"),
    ("2025", "03"),
]

TABLE_ID = f"{PROJECT_ID}.{DATASET}.raw_games"

client = bigquery.Client(project=PROJECT_ID)


# ─── Fonctions ────────────────────────────────────────
def get_games(username: str, year: str, month: str) -> list:
    """Récupère les parties d'un joueur pour un mois donné."""
    url = f"https://api.chess.com/pub/player/{username}/games/{year}/{month}"
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        games = response.json().get("games", [])
        print(f"  {username} {year}/{month} — {len(games)} parties trouvées")
        return games
    elif response.status_code == 404:
        print(f"  {username} {year}/{month} — aucune partie")
        return []
    else:
        print(f"  ERREUR {response.status_code} pour {username} {year}/{month}")
        return []


def transform_game(game: dict, username: str) -> dict:
    """Transforme un game brut en ligne BigQuery-ready."""
    return {
        "game_url":       game.get("url"),
        "username":       username,
        "time_class":     game.get("time_class"),
        "time_control":   game.get("time_control"),
        "rated":          game.get("rated"),
        "pgn":            game.get("pgn"),
        "white_username": game.get("white", {}).get("username"),
        "white_rating":   game.get("white", {}).get("rating"),
        "white_result":   game.get("white", {}).get("result"),
        "black_username": game.get("black", {}).get("username"),
        "black_rating":   game.get("black", {}).get("rating"),
        "black_result":   game.get("black", {}).get("result"),
        "end_time":       game.get("end_time"),
        "ingested_at":    datetime.utcnow().isoformat(),
    }


def create_table_if_not_exists():
    """Crée la table raw_games si elle n'existe pas."""
    schema = [
        bigquery.SchemaField("game_url",      "STRING"),
        bigquery.SchemaField("username",       "STRING"),
        bigquery.SchemaField("time_class",     "STRING"),
        bigquery.SchemaField("time_control",   "STRING"),
        bigquery.SchemaField("rated",          "BOOL"),
        bigquery.SchemaField("pgn",            "STRING"),
        bigquery.SchemaField("white_username", "STRING"),
        bigquery.SchemaField("white_rating",   "INTEGER"),
        bigquery.SchemaField("white_result",   "STRING"),
        bigquery.SchemaField("black_username", "STRING"),
        bigquery.SchemaField("black_rating",   "INTEGER"),
        bigquery.SchemaField("black_result",   "STRING"),
        bigquery.SchemaField("end_time",       "INTEGER"),
        bigquery.SchemaField("ingested_at",    "STRING"),
    ]
    table = bigquery.Table(TABLE_ID, schema=schema)
    table.clustering_fields = ["username", "time_class"]
    client.create_table(table, exists_ok=True)
    print(f"Table {TABLE_ID} prête.")


def load_all_to_bigquery(all_rows: list):
    """Charge toutes les lignes en un seul load job avec WRITE_TRUNCATE."""
    if not all_rows:
        print("Aucune ligne à charger.")
        return

    tmp_file = "tmp_all_games.json"
    with open(tmp_file, "w") as f:
        for row in all_rows:
            f.write(json.dumps(row) + "\n")

    print(f"\nChargement de {len(all_rows)} lignes en un seul job...")

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        schema=[
            bigquery.SchemaField("game_url",      "STRING"),
            bigquery.SchemaField("username",       "STRING"),
            bigquery.SchemaField("time_class",     "STRING"),
            bigquery.SchemaField("time_control",   "STRING"),
            bigquery.SchemaField("rated",          "BOOL"),
            bigquery.SchemaField("pgn",            "STRING"),
            bigquery.SchemaField("white_username", "STRING"),
            bigquery.SchemaField("white_rating",   "INTEGER"),
            bigquery.SchemaField("white_result",   "STRING"),
            bigquery.SchemaField("black_username", "STRING"),
            bigquery.SchemaField("black_rating",   "INTEGER"),
            bigquery.SchemaField("black_result",   "STRING"),
            bigquery.SchemaField("end_time",       "INTEGER"),
            bigquery.SchemaField("ingested_at",    "STRING"),
        ],
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    with open(tmp_file, "rb") as f:
        job = client.load_table_from_file(f, TABLE_ID, job_config=job_config)
        try:
            job.result()
            if job.errors:
                print(f"  ERREURS JOB : {job.errors}")
            else:
                print(f"  ✓ Job terminé — état : {job.state}")
        except Exception as e:
            print(f"  EXCEPTION JOB : {e}")

    os.remove(tmp_file)


# ─── Main ─────────────────────────────────────────────
def main():
    print("=== Chess Analytics — Ingestion Batch ===\n")

    create_table_if_not_exists()

    all_rows = []

    for username in PLAYERS:
        print(f"\nJoueur : {username}")
        for year, month in MONTHS:
            games = get_games(username, year, month)
            rows  = [transform_game(g, username) for g in games]
            all_rows.extend(rows)

    load_all_to_bigquery(all_rows)
    print(f"\n=== Terminé — {len(all_rows)} parties ingérées au total ===")


if __name__ == "__main__":
    main()