"""
transform_job.py = script Python qui tourne à l'intérieur du job Glue sur AWS.

Ce Glue Job représente l'étape intermédiaire : il lit les fichiers JSON bruts (Bronze) stockés dans S3
par la Lambda TMDB, les nettoie et les normalise (suppression des doublons, conversion des dates, filtrage
des contenus sans votes), puis charge les données structurées (Silver) dans Redshift Serverless
dans le schéma staging; prêtes à être exploitées par DBT et les outils BI.

Entrée  : s3://canal-data-platform-raw/raw/movies/ et raw/series/
Sortie  : Redshift; schéma staging, tables stg_movies et stg_series

"""

# Commençons par importer les modules nécessaires pour notre job Glue.

import sys                                                                      # Accès aux arguments système passés au job Glue
from datetime import datetime, timezone                                         # Pour horodater les enregistrements transformés

# AWS Glue
from awsglue.utils import getResolvedOptions                                    # Récupère les arguments passés au job Glue
from awsglue.context import GlueContext                                         # Contexte Glue — point d'entrée principal
from awsglue.job import Job                                                     # Gestion du cycle de vie du job (init, commit)

# Spark
from pyspark.context import SparkContext                                        # Contexte Spark sous-jacent à Glue
from pyspark.sql import functions as F                                          # Fonctions SQL Spark (col, lit, to_date...)
from pyspark.sql.types import StructType, StructField, StringType, FloatType, IntegerType, BooleanType  # Types de colonnes Spark


# Initialisation glue et spark

args = getResolvedOptions(sys.argv, [                                           # Récupère les arguments passés au job depuis la console Glue ou Airflow
    "JOB_NAME",                                                                 
    "S3_BUCKET",                                                                # Nom du bucket S3 source
    "REDSHIFT_URL",                                                             # URL de connexion Redshift
    "REDSHIFT_USER",                                                            
    "REDSHIFT_PASSWORD",                                                        
    "REDSHIFT_TMP_DIR",                                                         # Dossier S3 temporaire pour le chargement Redshift
])

sc = SparkContext()                                                             # Démarre le moteur Spark
glueContext = GlueContext(sc)                                                   # Glue s'appuie sur Spark
spark = glueContext.spark_session                                               # Session Spark pour lire/écrire des DataFrames
job = Job(glueContext)                                                          # Initialise le job Glue
job.init(args["JOB_NAME"], args)                                                # Enregistre le job avec son nom et ses arguments


# CONFIGURATION

S3_BUCKET = args["S3_BUCKET"]                                                   # Bucket S3 contenant les données brutes
REDSHIFT_URL = args["REDSHIFT_URL"]                                             # URL de connexion JDBC à Redshift (protocole standard pour se connecter à une base de données)
REDSHIFT_USER = args["REDSHIFT_USER"]                                         
REDSHIFT_PASSWORD = args["REDSHIFT_PASSWORD"]                                   
REDSHIFT_TMP_DIR = args["REDSHIFT_TMP_DIR"]                                     # Dossier S3 temporaire utilisé par Glue pour charger dans Redshift
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")                         # Date du jour en UTC pour lire la bonne partition S3


# SCHÉMAS DES DONNÉES TMDB

MOVIE_SCHEMA = StructType([                                                     # Schéma explicite des films
    StructField("id", IntegerType(), True),                                     # Identifiant unique TMDB du film
    StructField("title", StringType(), True),                                   
    StructField("original_title", StringType(), True),                         
    StructField("overview", StringType(), True),                                # Synopsis
    StructField("release_date", StringType(), True),                            # Date de sortie (string, converti plus bas)
    StructField("vote_average", FloatType(), True),                         
    StructField("vote_count", IntegerType(), True),                           
    StructField("popularity", FloatType(), True),                               # Score de popularité TMDB
    StructField("adult", BooleanType(), True),                                  # Contenu adulte ou non
    StructField("original_language", StringType(), True),                   
])

SERIES_SCHEMA = StructType([                                                    # Schéma explicite des séries
    StructField("id", IntegerType(), True),                                     # Identifiant unique TMDB de la série
    StructField("name", StringType(), True),                                    
    StructField("original_name", StringType(), True),                          
    StructField("overview", StringType(), True),                              
    StructField("first_air_date", StringType(), True),                          # Date de première diffusion
    StructField("vote_average", FloatType(), True),                          
    StructField("vote_count", IntegerType(), True),                          
    StructField("popularity", FloatType(), True),                       
    StructField("original_language", StringType(), True),                    
])


# FONCTIONS DE TRANSFORMATION

def read_raw_json(s3_prefix: str, schema: StructType):
    """Lit les fichiers JSON bruts depuis S3 pour une date donnée et retourne un DataFrame Spark."""

    s3_path = f"s3://{S3_BUCKET}/{s3_prefix}/{TODAY}/"                         # Chemin S3 partitionné par date

    df_raw = spark.read.option("multiline", "true").json(s3_path)              # Lit les JSON multiligne depuis S3

    df_results = df_raw.select(F.explode(F.col("results")).alias("item"))      # Extrait chaque film/série du tableau "results"

    return df_results.select([F.col(f"item.{field.name}").cast(field.dataType).alias(field.name)  # Sélectionne et caste chaque champ selon le schéma
                               for field in schema.fields])


def transform_movies(df):
    """Nettoie et enrichit le DataFrame des films."""
    return (df
        .filter(F.col("id").isNotNull())                                                # Supprime les lignes sans identifiant
        .filter(F.col("title").isNotNull())                                             # Supprime les films sans titre
        .filter(F.col("vote_count") >= 10)                                              # Garde uniquement les films avec au moins 10 votes
        .withColumn("release_date", F.to_date(F.col("release_date"), "yyyy-MM-dd"))     # Convertit la date string en type Date
        .withColumn("ingested_at", F.lit(TODAY))                                        # Ajoute la date d'ingestion pour traçabilité
        .withColumn("content_type", F.lit("movie"))                                     # Ajoute le type de contenu
        .dropDuplicates(["id"])                                                         # Supprime les doublons sur l'identifiant TMDB
    )


def transform_series(df):
    """Nettoie et enrichit le DataFrame des séries."""
    return (df
        .filter(F.col("id").isNotNull())                                                # Supprime les lignes sans identifiant
        .filter(F.col("name").isNotNull())                                              # Supprime les séries sans nom
        .filter(F.col("vote_count") >= 10)                                              # Garde uniquement les séries avec au moins 10 votes
        .withColumnRenamed("name", "title")                                             # Renomme "name" en "title" pour uniformiser avec les films
        .withColumnRenamed("original_name", "original_title")                           # Renomme pour uniformiser
        .withColumnRenamed("first_air_date", "release_date")                   
        .withColumn("release_date", F.to_date(F.col("release_date"), "yyyy-MM-dd"))     # Convertit la date string en type Date
        .withColumn("ingested_at", F.lit(TODAY))                                        # Ajoute la date d'ingestion
        .withColumn("content_type", F.lit("series"))                                    # Ajoute le type de contenu
        .dropDuplicates(["id"])                                                         # Supprime les doublons
    )

# Connexion à Redshift via JDBC et chargement du DataFrame; écrase la table à chaque exécution

def write_to_redshift(df, table_name: str):
    """Écrit un DataFrame Spark dans une table Redshift via JDBC."""
    df.write \
        .format("jdbc") \
        .option("url", REDSHIFT_URL) \
        .option("dbtable", f"staging.{table_name}") \
        .option("user", REDSHIFT_USER) \
        .option("password", REDSHIFT_PASSWORD) \
        .option("driver", "com.amazon.redshift.jdbc42.Driver") \
        .option("tempdir", REDSHIFT_TMP_DIR) \
        .mode("overwrite") \
        .save()
    
    print(f"[Redshift] Table staging.{table_name} chargée avec {df.count()} lignes")        # Log du nombre de lignes chargées


# PIPELINE PRINCIPAL

print("[START] Début du job Glue. Transformation TMDB")

df_movies_raw = read_raw_json("raw/movies/popular", MOVIE_SCHEMA)              # Lecture des films populaires bruts depuis S3
df_movies_top = read_raw_json("raw/movies/top_rated", MOVIE_SCHEMA)            # Lecture des films top rated bruts depuis S3
df_movies = df_movies_raw.union(df_movies_top).dropDuplicates(["id"])          # Fusion des deux sources et suppression des doublons

df_series_raw = read_raw_json("raw/series/popular", SERIES_SCHEMA)             
df_series_top = read_raw_json("raw/series/top_rated", SERIES_SCHEMA)        
df_series = df_series_raw.union(df_series_top).dropDuplicates(["id"])          

df_movies_clean = transform_movies(df_movies)                                  # Transformation et nettoyage des films
df_series_clean = transform_series(df_series)                                  # Transformation et nettoyage des séries

write_to_redshift(df_movies_clean, "stg_movies")                               # Chargement des films dans Redshift
write_to_redshift(df_series_clean, "stg_series")                               # Chargement des séries dans Redshift

print("[END] Job Glue terminé avec succès")

job.commit()                                                                   # Valide le job Glue; obligatoire pour marquer le job comme réussi
