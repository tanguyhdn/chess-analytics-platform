import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./credentials/service_account.json"

client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"))

query = """
SELECT
    COUNT(*) as total_games,
    COUNT(DISTINCT username) as unique_players,
    MIN(ended_at) as earliest_game,
    MAX(ended_at) as latest_game
FROM `chess-analytics-platform.chess_staging.stg_games`
"""

for row in client.query(query):
    print(f"Total games : {row.total_games}")
    print(f"Unique players : {row.unique_players}")
    print(f"Earliest game : {row.earliest_game}")
    print(f"Latest game : {row.latest_game}")