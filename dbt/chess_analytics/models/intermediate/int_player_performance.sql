-- int_player_performance.sql
-- Agrégation des performances par joueur et format de jeu
-- Source : stg_games

with games as (

    select * from {{ ref('stg_games') }}

),

performance as (

    select
        -- Dimensions
        username,
        time_class,

        -- Volume
        count(*)                                           as total_games,

        -- Résultats
        countif(player_result = 'win')                     as total_wins,
        countif(player_result = 'loss')                    as total_losses,
        countif(player_result = 'draw')                    as total_draws,

        -- Win rate
        round(
            countif(player_result = 'win') / count(*) * 100,
            2
        )                                                  as win_rate_pct,

        -- Performance par couleur
        countif(player_color = 'white')                    as games_as_white,
        countif(player_color = 'black')                    as games_as_black,
        countif(player_color = 'white' and player_result = 'win')
                                                           as wins_as_white,
        countif(player_color = 'black' and player_result = 'win')
                                                           as wins_as_black,

        -- Ratings
        round(avg(player_rating), 0)                       as avg_rating,
        max(player_rating)                                 as max_rating,
        min(player_rating)                                 as min_rating,
        round(avg(opponent_rating), 0)                     as avg_opponent_rating,

        -- Activité
        min(ended_at)                                      as first_game_at,
        max(ended_at)                                      as last_game_at

    from games
    group by username, time_class

)

select * from performance