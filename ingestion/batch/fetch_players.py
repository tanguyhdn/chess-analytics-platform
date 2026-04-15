"""
fetch_players.py
Ingestion batch — Profils joueurs Chess.com → BigQuery (chess_raw)
"""

import os
import json
import requests
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

TABLE_ID = f"{PROJECT_ID}.{DATASET}.raw_players"

client = bigquery.Client(project=PROJECT_ID)


# ─── Fonctions ────────────────────────────────────────
def get_player_profile(username: str) -> dict:
    """Récupère le profil d'un joueur."""
    url = f"https://api.chess.com/pub/player/{username}"
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print(f"  {username} — profil récupéré")
        return response.json()
    else:
        print(f"  ERREUR {response.status_code} pour {username}")
        return {}


def get_player_stats(username: str) -> dict:
    """Récupère les stats et ratings d'un joueur."""
    url = f"https://api.chess.com/pub/player/{username}/stats"
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return {}


def transform_player(profile: dict, stats: dict, username: str) -> dict:
    """Transforme profil + stats en ligne BigQuery-ready."""
    chess_rapid  = stats.get("chess_rapid",  {}).get("last", {})
    chess_blitz  = stats.get("chess_blitz",  {}).get("last", {})
    chess_bullet = stats.get("chess_bullet", {}).get("last", {})

    return {
        "username":      username,
        "player_id":     profile.get("player_id"),
        "title":         profile.get("title"),
        "name":          profile.get("name"),
        "country":       profile.get("country", "").split("/")[-1],
        "location":      profile.get("location"),
        "followers":     profile.get("followers"),
        "is_streamer":   profile.get("is_streamer", False),
        "rapid_rating":  chess_rapid.get("rating"),
        "blitz_rating":  chess_blitz.get("rating"),
        "bullet_rating": chess_bullet.get("rating"),
        "rapid_games":   chess_rapid.get("rd"),
        "blitz_games":   chess_blitz.get("rd"),
        "bullet_games":  chess_bullet.get("rd"),
        "ingested_at":   datetime.utcnow().isoformat(),
    }


def create_table_if_not_exists():
    """Crée la table raw_players si elle n'existe pas."""
    schema = [
        bigquery.SchemaField("username",      "STRING"),
        bigquery.SchemaField("player_id",     "INTEGER"),
        bigquery.SchemaField("title",         "STRING"),
        bigquery.SchemaField("name",          "STRING"),
        bigquery.SchemaField("country",       "STRING"),
        bigquery.SchemaField("location",      "STRING"),
        bigquery.SchemaField("followers",     "INTEGER"),
        bigquery.SchemaField("is_streamer",   "BOOL"),
        bigquery.SchemaField("rapid_rating",  "INTEGER"),
        bigquery.SchemaField("blitz_rating",  "INTEGER"),
        bigquery.SchemaField("bullet_rating", "INTEGER"),
        bigquery.SchemaField("rapid_games",   "INTEGER"),
        bigquery.SchemaField("blitz_games",   "INTEGER"),
        bigquery.SchemaField("bullet_games",  "INTEGER"),
        bigquery.SchemaField("ingested_at",   "STRING"),
    ]
    table = bigquery.Table(TABLE_ID, schema=schema)
    client.create_table(table, exists_ok=True)
    print(f"Table {TABLE_ID} prête.")


def load_to_bigquery(rows: list):
    """Charge les lignes dans BigQuery via load job."""
    if not rows:
        return

    tmp_file = "tmp_players.json"
    with open(tmp_file, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        schema=[
            bigquery.SchemaField("username",      "STRING"),
            bigquery.SchemaField("player_id",     "INTEGER"),
            bigquery.SchemaField("title",         "STRING"),
            bigquery.SchemaField("name",          "STRING"),
            bigquery.SchemaField("country",       "STRING"),
            bigquery.SchemaField("location",      "STRING"),
            bigquery.SchemaField("followers",     "INTEGER"),
            bigquery.SchemaField("is_streamer",   "BOOL"),
            bigquery.SchemaField("rapid_rating",  "INTEGER"),
            bigquery.SchemaField("blitz_rating",  "INTEGER"),
            bigquery.SchemaField("bullet_rating", "INTEGER"),
            bigquery.SchemaField("rapid_games",   "INTEGER"),
            bigquery.SchemaField("blitz_games",   "INTEGER"),
            bigquery.SchemaField("bullet_games",  "INTEGER"),
            bigquery.SchemaField("ingested_at",   "STRING"),
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
    print(f"  {len(rows)} joueurs chargés dans BigQuery.")


# ─── Main ─────────────────────────────────────────────
def main():
    print("=== Chess Analytics — Ingestion Joueurs ===\n")

    create_table_if_not_exists()

    rows = []
    for username in PLAYERS:
        print(f"\nJoueur : {username}")
        profile = get_player_profile(username)
        stats   = get_player_stats(username)
        if profile:
            row = transform_player(profile, stats, username)
            rows.append(row)

    load_to_bigquery(rows)
    print(f"\n=== Terminé — {len(rows)} joueurs ingérés ===")


if __name__ == "__main__":
    main()