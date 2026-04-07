-- mart_opening_analysis.sql
-- Analyse des ouvertures par joueur
-- Extrait l'ouverture depuis le PGN

with games as (

    select * from {{ ref('stg_games') }}

),

-- Extraction de l'ouverture depuis le PGN
-- Le PGN contient une ligne [ECOUrl "..."] avec le nom de l'ouverture
with_opening as (

    select
        *,
        -- Extrait le nom de l'ouverture depuis le tag ECOUrl du PGN
        regexp_extract(pgn, r'\[ECOUrl "https://www\.chess\.com/openings/([^"]+)"\]')
                                                           as opening_slug,

        -- Extrait le code ECO (ex: E60, D35...)
        regexp_extract(pgn, r'\[ECO "([^"]+)"\]')         as eco_code

    from games

),

opening_stats as (

    select
        username,
        time_class,
        player_color,
        coalesce(opening_slug, 'unknown')                  as opening_slug,
        coalesce(eco_code, 'unknown')                      as eco_code,

        -- Volume
        count(*)                                           as total_games,

        -- Résultats
        countif(player_result = 'win')                     as wins,
        countif(player_result = 'loss')                    as losses,
        countif(player_result = 'draw')                    as draws,

        -- Win rate
        round(
            countif(player_result = 'win') / count(*) * 100,
            2
        )                                                  as win_rate_pct,

        -- Rating moyen dans cette ouverture
        round(avg(player_rating), 0)                       as avg_rating

    from with_opening
    group by
        username,
        time_class,
        player_color,
        opening_slug,
        eco_code

),

-- Filtre les ouvertures avec au moins 3 parties pour la pertinence statistique
final as (

    select *
    from opening_stats
    where total_games >= 3

)

select * from final