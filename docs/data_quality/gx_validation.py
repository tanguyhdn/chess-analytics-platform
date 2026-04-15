"""
gx_validation.py
Great Expectations — Validation des marts BigQuery
Valide la qualité des données dans chess_marts
"""

import os
import great_expectations as gx
from google.cloud import bigquery
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./credentials/service_account.json"

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
client = bigquery.Client(project=PROJECT_ID)


# ─── Chargement des données ───────────────────────────
def load_mart(table: str) -> pd.DataFrame:
    query = f"SELECT * FROM `{PROJECT_ID}.chess_staging.{table}`"
    return client.query(query).to_dataframe()


# ─── Contexte GX ──────────────────────────────────────
context = gx.get_context(mode="ephemeral")


# ─── Validation mart_player_stats ─────────────────────
def validate_player_stats():
    print("\n=== Validation : mart_player_stats ===")

    df = load_mart("mart_player_stats")
    ds = context.data_sources.add_pandas("player_stats_source")
    da = ds.add_dataframe_asset("player_stats_asset")
    batch = da.add_batch_definition_whole_dataframe("batch").get_batch(
        batch_parameters={"dataframe": df}
    )

    suite = context.suites.add(
        gx.ExpectationSuite(name="player_stats_suite")
    )

    # Username non null et unique
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="username")
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeUnique(column="username")
    )

    # Peak rating dans une plage réaliste
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="peak_rating",
            min_value=1000,
            max_value=4000
        )
    )

    # Total games positif
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="total_games_all",
            min_value=0,
            max_value=100000
        )
    )

    # 5 joueurs attendus
    suite.add_expectation(
        gx.expectations.ExpectTableRowCountToBeBetween(
            min_value=4,
            max_value=6
        )
    )

    result = batch.validate(suite)
    _print_results(result, "mart_player_stats")
    return result.success


# ─── Validation stg_games ─────────────────────────────
def validate_stg_games():
    print("\n=== Validation : stg_games ===")

    df = load_mart("stg_games")
    ds = context.data_sources.add_pandas("games_source")
    da = ds.add_dataframe_asset("games_asset")
    batch = da.add_batch_definition_whole_dataframe("batch").get_batch(
        batch_parameters={"dataframe": df}
    )

    suite = context.suites.add(
        gx.ExpectationSuite(name="games_suite")
    )

    # game_url non null
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="game_url")
    )

    # time_class dans les valeurs attendues
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="time_class",
            value_set=["rapid", "blitz", "bullet", "daily"]
        )
    )

    # player_color dans les valeurs attendues
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="player_color",
            value_set=["white", "black"]
        )
    )

    # Ratings dans une plage réaliste
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="player_rating",
            min_value=500,
            max_value=4000
        )
    )

    # Volume minimum de parties
    suite.add_expectation(
        gx.expectations.ExpectTableRowCountToBeBetween(
            min_value=1000,
            max_value=500000
        )
    )

    result = batch.validate(suite)
    _print_results(result, "stg_games")
    return result.success


# ─── Affichage des résultats ──────────────────────────
def _print_results(result, table_name: str):
    results = result.results
    passed = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)

    print(f"  Résultats pour {table_name}:")
    print(f"  ✓ {passed} expectations passées")
    print(f"  ✗ {failed} expectations échouées")

    for r in results:
        status = "✓" if r.success else "✗"
        exp_type = r.expectation_config.type
        print(f"    {status} {exp_type}")


# ─── Main ─────────────────────────────────────────────
def main():
    print("=== Chess Analytics — Great Expectations Validation ===")

    results = []
    results.append(validate_player_stats())
    results.append(validate_stg_games())

    total = len(results)
    passed = sum(results)

    print(f"\n=== Résumé : {passed}/{total} suites validées ===")

    if all(results):
        print("✓ Toutes les validations sont passées !")
    else:
        print("✗ Certaines validations ont échoué.")


if __name__ == "__main__":
    main()