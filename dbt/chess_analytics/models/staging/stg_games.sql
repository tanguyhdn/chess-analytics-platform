-- stg_games.sql
-- Staging des parties Chess.com
-- Nettoyage, typage, renommage depuis raw_games

with source as (

    select * from {{ source('chess_raw', 'raw_games') }}

),

-- Déduplication sur game_url — garde la ligne la plus récente
deduplicated as (

    select *
    from source
    qualify row_number() over (
        partition by game_url
        order by ingested_at desc
    ) = 1

),

renamed as (

    select
        -- Clé naturelle
        game_url,

        -- Joueur suivi
        lower(username)                                    as username,

        -- Format de jeu
        lower(time_class)                                  as time_class,
        time_control,

        -- Partie classée
        rated,

        -- Joueur blanc
        lower(white_username)                              as white_username,
        white_rating,
        lower(white_result)                                as white_result,

        -- Joueur noir
        lower(black_username)                              as black_username,
        black_rating,
        lower(black_result)                                as black_result,

        -- Temps
        timestamp_seconds(end_time)                        as ended_at,

        -- Dérivés utiles
        case
            when lower(white_username) = lower(username)
            then 'white'
            else 'black'
        end                                                as player_color,

        case
            when lower(white_username) = lower(username)
            then lower(white_result)
            else lower(black_result)
        end                                                as player_result,

        case
            when lower(white_username) = lower(username)
            then white_rating
            else black_rating
        end                                                as player_rating,

        case
            when lower(white_username) = lower(username)
            then black_rating
            else white_rating
        end                                                as opponent_rating,

        case
            when lower(white_username) = lower(username)
            then lower(black_username)
            else lower(white_username)
        end                                                as opponent_username,

        -- Metadata pipeline
        ingested_at

    from deduplicated

)

select * from renamed