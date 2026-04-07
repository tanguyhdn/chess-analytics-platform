-- mart_player_stats.sql
-- Table finale des statistiques par joueur
-- Consommée par le dashboard Streamlit

with player_performance as (

    select * from {{ ref('int_player_performance') }}

),

players as (

    select * from {{ ref('stg_players') }}

),

-- Pivot des performances par format de jeu
rapid as (
    select * from player_performance
    where time_class = 'rapid'
),

blitz as (
    select * from player_performance
    where time_class = 'blitz'
),

bullet as (
    select * from player_performance
    where time_class = 'bullet'
),

final as (

    select
        -- Identité joueur
        p.username,
        p.full_name,
        p.title,
        p.country_code,
        p.followers,
        p.is_streamer,

        -- Ratings actuels
        p.rapid_rating,
        p.blitz_rating,
        p.bullet_rating,
        p.peak_rating,

        -- Stats Rapid
        r.total_games                                      as rapid_total_games,
        r.total_wins                                       as rapid_wins,
        r.win_rate_pct                                     as rapid_win_rate_pct,
        r.avg_rating                                       as rapid_avg_rating,

        -- Stats Blitz
        b.total_games                                      as blitz_total_games,
        b.total_wins                                       as blitz_wins,
        b.win_rate_pct                                     as blitz_win_rate_pct,
        b.avg_rating                                       as blitz_avg_rating,

        -- Stats Bullet
        bu.total_games                                     as bullet_total_games,
        bu.total_wins                                      as bullet_wins,
        bu.win_rate_pct                                    as bullet_win_rate_pct,
        bu.avg_rating                                      as bullet_avg_rating,

        -- Total toutes catégories
        coalesce(r.total_games, 0)
        + coalesce(b.total_games, 0)
        + coalesce(bu.total_games, 0)                      as total_games_all,

        coalesce(r.total_wins, 0)
        + coalesce(b.total_wins, 0)
        + coalesce(bu.total_wins, 0)                       as total_wins_all

    from players p
    left join rapid  r  on p.username = r.username
    left join blitz  b  on p.username = b.username
    left join bullet bu on p.username = bu.username

)

select * from final