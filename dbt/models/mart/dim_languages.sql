
-- Modèle mart : table de dimension des langues.
-- Liste toutes les langues originales présentes dans le catalogue
-- avec le nombre de contenus par langue. Utile pour les filtres BI.


with movies_languages as (

    select
        original_language,                                         
        'movie'               as content_type,                  
        count(*)              as nb_contenus                      -- Nombre de films dans cette langue

    from {{ ref('stg_movies') }}                                  
    group by original_language                                    

),

series_languages as (

    select
        original_language,                          
        'series' as content_type,                   
        count(*) as nb_contenus                     

    from {{ ref('stg_series') }}                                
    group by original_language                                    

),

all_languages as (

    select * from movies_languages                              
    union all
    select * from series_languages                             

),

final as (

    select
        original_language,                                         -- Code langue (fr, en, ja, ko)
        content_type,                                              -- Type de contenu (film ou série)
        nb_contenus,                                           
        round(                                                     -- Calcule le pourcentage de contenus par langue

            nb_contenus * 100.0 / sum(nb_contenus) over (partition by content_type), 2

        ) as pct_du_catalogue                                       -- Pourcentage arrondi à 2 décimales

    from all_languages

)

select * from final                                               
order by content_type, nb_contenus desc                     
