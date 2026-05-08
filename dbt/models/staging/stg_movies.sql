
-- Modèle staging pour les films.
-- Lit les données brutes de la table staging.stg_movies chargée par Glue
-- et applique des transformations légères pour normaliser les données.

with source as (

    select * from {{ source('staging', 'stg_movies') }}      -- Lit la table stg_movies depuis le schéma staging de Redshift

), 

renamed as (

    select
        id  as movie_id,          
        title,                 
        original_title,           
        overview,                 -- Synopsis du film
        release_date,             
        vote_average,           
        vote_count,                
        popularity,               -- Score de popularité TMDB
        original_language,        
        content_type,             -- Type de contenu : "movie"
        ingested_at               -- Date d'ingestion par la Lambda

    from source
    where id is not null          
      and title is not null     
      and vote_count >= 10        -- Garde uniquement les films avec au moins 10 votes

) 

select * from renamed           
