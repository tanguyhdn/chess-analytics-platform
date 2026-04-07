-- mart_elo_progression.sql
-- Évolution du rating ELO par joueur dans le temps
-- Granularité : par jour et par format de jeu

with games as (

    select * from {{ ref('stg_games') }}

),

daily_rating as (

    select
        username,
        time_class,
        date(ended_at)                                     as game_date,

        -- Rating du joueur à cette date
        -- On prend le dernier rating de la journée
        last_value(player_rating) over (
            partition by username, time_class, date(ended_at)
            order by ended_at
            rows between unbounded preceding and unbounded following
        )                                                  as closing_rating,

        -- Rating max et min de la journée
        max(player_rating) over (
            partition by username, time_class, date(ended_at)
        )                                                  as daily_max_rating,

        min(player_rating) over (
            partition by username, time_class, date(ended_at)
        )                                                  as daily_min_rating,

        -- Nombre de parties ce jour-là
        count(*) over (
            partition by username, time_class, date(ended_at)
        )                                                  as daily_games,

        -- Victoires ce jour-là
        countif(player_result = 'win') over (
            partition by username, time_class, date(ended_at)
        )                                                  as daily_wins

    from games

),

-- Déduplication pour garder une ligne par joueur/format/jour
deduplicated as (

    select distinct
        username,
        time_class,
        game_date,
        closing_rating,
        daily_max_rating,
        daily_min_rating,
        daily_games,
        daily_wins,

        -- Variation de rating vs jour précédent
        closing_rating - lag(closing_rating) over (
            partition by username, time_class
            order by game_date
        )                                                  as rating_change

    from daily_rating

)

select * from deduplicated
order by username, time_class, game_date