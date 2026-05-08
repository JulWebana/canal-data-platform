
-- Script SQL exécuté une seule fois dans Redshift pour créer 
-- le schéma staging et les tables qui recevront les données du job Glue.


-- SCHÉMA STAGING

CREATE SCHEMA IF NOT EXISTS staging;                                        


-- TABLE STG_MOVIES

DROP TABLE IF EXISTS staging.stg_movies;                                       

CREATE TABLE staging.stg_movies (

    id                  INTEGER,                                                -- Identifiant unique TMDB du film
    title               VARCHAR(500),                                           
    original_title      VARCHAR(500),                                           
    overview            VARCHAR(5000),                                          -- Synopsis du film (long texte)
    release_date        DATE,                                                   
    vote_average        FLOAT,                                           
    vote_count          INTEGER,                                      
    popularity          FLOAT,                                                  -- Score de popularité TMDB
    adult               BOOLEAN,                                                -- Indique si le contenu est réservé aux adultes
    original_language   VARCHAR(10),                                            -- Code langue originale (fr, en, ja)
    content_type        VARCHAR(10),                                    
    ingested_at         DATE                                                    -- Date d'ingestion pour la traçabilité
)

DISTSTYLE AUTO                                                                  -- Redshift choisit automatiquement la meilleure distribution
SORTKEY(release_date, vote_average);                                            -- Tri par date et note pour optimiser les requêtes analytiques


-- TABLE STG_SERIES

DROP TABLE IF EXISTS staging.stg_series;                                   

CREATE TABLE staging.stg_series (

    id                  INTEGER,                                                
    title               VARCHAR(500),                                           -- Nom de la série (renommé depuis name dans le job Glue)
    original_title      VARCHAR(500),                                 
    overview            VARCHAR(5000),                                        
    release_date        DATE,                                                 
    vote_average        FLOAT,                                               
    vote_count          INTEGER,                                              
    popularity          FLOAT,                                            
    original_language   VARCHAR(10),                                     
    content_type        VARCHAR(10),                                            
    ingested_at         DATE                                                  
)

DISTSTYLE AUTO
SORTKEY(release_date, vote_average);                                      


-- VÉRIFICATION

SELECT 'stg_movies' as table_name, COUNT(*) as nb_lignes FROM staging.stg_movies   -- Vérifie le nombre de lignes dans stg_movies
UNION ALL
SELECT 'stg_series', COUNT(*) FROM staging.stg_series;                             -- Vérifie le nombre de lignes dans stg_series
