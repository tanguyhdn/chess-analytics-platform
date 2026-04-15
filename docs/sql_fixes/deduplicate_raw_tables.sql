-- deduplicate_raw_tables.sql
-- Script de correction one-time pour dédupliquer les tables raw
-- À exécuter dans BigQuery Console si des doublons sont détectés
-- Cause : WRITE_APPEND sans contrôle d'idempotence lors de rejeux d'ingestion

-- ─── Déduplication raw_games ──────────────────────────
CREATE OR REPLACE TABLE `chess-analytics-platform.chess_raw.raw_games` AS
SELECT DISTINCT *
FROM `chess-analytics-platform.chess_raw.raw_games`
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY game_url
    ORDER BY ingested_at DESC
) = 1;

-- ─── Déduplication raw_players ────────────────────────
CREATE OR REPLACE TABLE `chess-analytics-platform.chess_raw.raw_players` AS
SELECT DISTINCT *
FROM `chess-analytics-platform.chess_raw.raw_players`
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY username
    ORDER BY ingested_at DESC
) = 1;