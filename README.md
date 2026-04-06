# ♟ Chess Analytics Platform

> End-to-end Modern Data Stack pipeline built on real Chess.com data.

[![dbt](https://img.shields.io/badge/dbt-Core-FF6849?logo=dbt)](https://www.getdbt.com/)
[![BigQuery](https://img.shields.io/badge/BigQuery-Google_Cloud-4285F4?logo=google-cloud)](https://cloud.google.com/bigquery)
[![Kafka](https://img.shields.io/badge/Kafka-Streaming-231F20?logo=apache-kafka)](https://kafka.apache.org/)
[![Airflow](https://img.shields.io/badge/Airflow-Orchestration-017CEE?logo=apache-airflow)](https://airflow.apache.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit)](https://streamlit.io/)

## Overview

This project builds a complete analytics engineering pipeline ingesting data from the
Chess.com Public API — no API key required. It covers the full Modern Data Stack:
batch ingestion, real-time streaming simulation, data modeling with dbt, orchestration
with Airflow, data quality monitoring, and a deployed Streamlit dashboard.

**Data source** : [Chess.com PubAPI](https://www.chess.com/news/view/published-data-api)
— public, free, no authentication required.

## Stack

| Layer | Tool |
|---|---|
| Ingestion batch | Python · Chess.com PubAPI |
| Streaming | Apache Kafka · Kafka Connect |
| Storage | Google BigQuery |
| Transformation | dbt Core |
| Orchestration | Apache Airflow |
| Data quality | Elementary Data · dbt tests |
| Serving | Streamlit |

## Project Structure

    chess-analytics-platform/
    ├── ingestion/          # Batch ingestion scripts
    │   ├── batch/          # Python scripts Chess.com API → BigQuery
    │   └── schemas/        # JSON schemas for raw tables
    ├── streaming/          # Kafka producers & consumers
    │   ├── producers/      # PGN move replay producer
    │   └── consumers/      # BigQuery sink consumer
    ├── dbt/                # Data transformation
    │   ├── models/
    │   │   ├── sources/    # Source declarations
    │   │   ├── staging/    # Cleaned, typed models
    │   │   ├── intermediate/ # Business logic joins
    │   │   └── marts/      # Analytics-ready tables
    │   ├── tests/          # Custom data tests
    │   ├── macros/         # Reusable Jinja macros
    │   └── snapshots/      # SCD Type 2 snapshots
    ├── orchestration/      # Airflow DAGs
    │   └── dags/
    ├── serving/            # Streamlit dashboard
    │   └── app/
    └── docs/               # Architecture diagrams

## Getting Started

### Prerequisites

- Docker Desktop
- Python 3.10+
- Google Cloud account (free tier)
- Git

### Setup

    # Clone the repo
    git clone https://github.com/tanguyhdn/chess-analytics-platform.git
    cd chess-analytics-platform

    # Copy environment variables
    cp .env.example .env
    # Edit .env with your GCP project details

    # Add your GCP service account key
    # Place service_account.json in credentials/

## Data Models

| Model | Layer | Description |
|---|---|---|
| `stg_games` | Staging | Cleaned game records |
| `stg_players` | Staging | Player profiles & ratings |
| `int_player_performance` | Intermediate | Per-player aggregated stats |
| `mart_player_stats` | Mart | Final player analytics table |
| `mart_opening_analysis` | Mart | Opening repertoire analysis |
| `mart_elo_progression` | Mart | ELO rating over time |

## Dashboard

> Live app : coming soon

Built with Streamlit, connected to BigQuery marts.
Covers player ELO progression, opening win rates, game length distribution,
and head-to-head comparisons between top players.

---

*Built by [Tanguy](https://github.com/tanguyhdn) —
Analytics Engineer · Paris*