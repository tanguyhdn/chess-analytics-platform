-- stg_players.sql
-- Staging des profils joueurs Chess.com
-- Nettoyage, typage, renommage depuis raw_players

with source as (

    select * from {{ source('chess_raw', 'raw_players') }}

),

deduplicated as (

    select *
    from source
    qualify row_number() over (
        partition by username
        order by ingested_at desc
    ) = 1

),

renamed as (

    select
        -- Clé naturelle
        lower(username)                                    as username,

        -- Identifiants
        player_id,
        upper(title)                                       as title,
        name                                               as full_name,

        -- Localisation
        upper(country)                                     as country_code,
        location,

        -- Communauté
        followers,
        is_streamer,

        -- Ratings par format
        rapid_rating,
        blitz_rating,
        bullet_rating,

        -- Rating max toutes catégories
        greatest(
            coalesce(rapid_rating, 0),
            coalesce(blitz_rating, 0),
            coalesce(bullet_rating, 0)
        )                                                  as peak_rating,

        -- Metadata pipeline
        ingested_at

    from deduplicated

)

select * from renamed