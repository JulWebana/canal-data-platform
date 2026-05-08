
-- Modèle staging pour les séries.
-- Lit les données brutes de la table staging.stg_series chargée par Glue
-- et applique des transformations légères pour normaliser les données.

with source as (

    select * from {{ source('staging', 'stg_series') }}      -- Lit la table stg_series depuis le schéma staging de Redshift

),

renamed as (

    select
        id as series_id,         
        title,                                                                   
        original_title,                                                       
        overview,                                                             
        release_date,                                                            
        vote_average,                                                        
        vote_count,                                                   
        popularity,                                                             
        original_language,                                                 
        content_type,                                                        
        ingested_at                                                      

    from source
    where id is not null                                                      
      and title is not null                                                   
      and vote_count >= 10                                                        

)

select * from renamed                                                          
