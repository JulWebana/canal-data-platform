
-- Modèle mart : top contenus toutes catégories confondues (films + séries).
-- Combine les films et séries, les classe par note et popularité.


with movies as (

    select
        movie_id as content_id,      
        title,                                                    
        'movie' as content_type,   
        vote_average,   
        vote_count,                                            
        popularity,                                              
        release_date,                                            
        original_language,                                     
        ingested_at                                             

    from {{ ref('stg_movies') }}     -- Référence au modèle staging stg_movies

),

series as (

    select
        series_id as content_id,    
        title,                    
        'series' as content_type,   
        vote_average,            
        vote_count,                                        
        popularity,                                            
        release_date,                                              
        original_language,                                    
        ingested_at                                                

    from {{ ref('stg_series') }}                                  

),

all_content as (

    select * from movies                                           
    union all
    select * from series                                   

),

final as (

    select
        content_id,
        title,
        content_type,
        vote_average,
        vote_count,
        popularity,
        release_date,
        original_language,
        ingested_at,

        row_number() over (                                        -- Calcule le rang de chaque contenu

            partition by content_type                              -- Séparément pour les films et les séries
            order by vote_average desc, popularity desc            -- Classé par note puis par popularité

        )   as rank_by_type                                        

    from all_content
    where vote_average >= 7.0                                      -- Garde uniquement les contenus bien notés

)

select * from final                                                
order by vote_average desc, popularity desc                       
