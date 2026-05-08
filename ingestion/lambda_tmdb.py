"""
Lambda = ingestion brute  

Fonction AWS Lambda d’ingestion : récupère les données de films et séries depuis l’API TMDB et les stocke en JSON brut dans un bucket S3.

Déclenchement : manuel ou via EventBridge (scheduler)
Destination   : S3 bucket, dossiers raw/movies/ et raw/series/

"""

# Import des modules nécessaires :

import json                               # sérialise les données en JSON
import os                                 # lit les variables d'environnement
import boto3                              # SDK AWS pour interagir avec S3
import urllib.request                     # fait des requêtes HTTP sans dépendance externe
from datetime import datetime, timezone   # horodate les fichiers déposés dans S3


# CONFIGURATION                                                        

TMDB_API_KEY = os.environ["TMDB_API_KEY"]                       # Clé API TMDB. injectée via variable d'environnement Lambda

S3_BUCKET = os.environ["S3_BUCKET"]                             #  # Nom du bucket S3 où seront déposées les données brutes 

TMDB_BASE_URL = "https://api.themoviedb.org/3"

LANGUAGE = "fr-FR"

MAX_PAGES = 3                                                   # Nombre de pages à récupérer par catégorie. 1 page = 20 résultats



# CLIENT S3                                                            


s3_client = boto3.client("s3")                                  # Initialisation du client S3 utilisé pour uploader les données brutes (JSON) dans le bucket S3.


# FONCTIONS UTILITAIRES                                                


# 1. Fonction qui appelle un endpoint de l'API TMDB et retourne la réponse JSON.  endpoint = chemin de l'API et page = numéro de page pour la pagination

def fetch_tmdb(endpoint: str, page: int = 1) -> dict:         

    url = (                                                     # Construction de l'URL complète avec clé API, langue et page
        f"{TMDB_BASE_URL}{endpoint}"
        f"?api_key={TMDB_API_KEY}"
        f"&language={LANGUAGE}"
        f"&page={page}"
    )

    with urllib.request.urlopen(url) as response:                  # Ouverture de la requête HTTP GET

        raw = response.read().decode("utf-8")                      # Lecture et décodage de la réponse en UTF-8

    return json.loads(raw)                                         # Conversion de la chaîne JSON en dictionnaire Python



# 2. Fonction qui sérialise un dictionnaire Python en JSON et le dépose dans S3. data   = dictionnaire Python à sauvegarder.  s3_key = chemin complet dans le bucket S3

def save_to_s3(data: dict, s3_key: str) -> None:

    json_body = json.dumps(data, ensure_ascii=False, indent=2)          # Conversion du dictionnaire en chaîne JSON bien formatée

    s3_client.put_object(                                               # Envoi vers S3 via put_object
        Bucket=S3_BUCKET,                                       
        Key=s3_key,                                                     # Chemin du fichier dans le bucket
        Body=json_body.encode("utf-8"),                                 
        ContentType="application/json",                                 # Métadonnée MIME type
    )


    # Log pour le suivi dans CloudWatch

    print(f"[S3] Fichier déposé : s3://{S3_BUCKET}/{s3_key}")



# 3. Function qui récupère plusieurs pages d'un endpoint TMDB et les stocke dans S3. 

def ingest_category(endpoint: str, s3_prefix: str, label: str) -> int:             # label = nom lisible pour les logs

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")                        # Date du jour en UTC pour partitionner les fichiers dans S3

    total_results = 0                                                              # Compteur de résultats ingérés

    for page in range(1, MAX_PAGES + 1):                                           # Boucle sur les pages (de 1 à MAX_PAGES inclus)

        print(f"[TMDB] Récupération : {label} — page {page}/{MAX_PAGES}")

  
        data = fetch_tmdb(endpoint, page=page)                                     # Appel à l'API TMDB pour cette page

        s3_key = f"{s3_prefix}/{today}/page_{page}.json"                           # Construction du chemin S3 avec partitionnement par date. Structure : raw/movies/popular/2026-05-06/page_1.json

        save_to_s3(data, s3_key)                                                   # Sauvegarde dans S3 du JSON brut de cette page      

     
        page_count = len(data.get("results", []))
        total_results += page_count

        print(f"[TMDB] {page_count} résultats récupérés pour la page {page}")

    return total_results



# HANDLER PRINCIPAL (point d'entrée Lambda)                           

def lambda_handler(event: dict, context) -> dict:                                   #  Point d'entrée de la fonction Lambda. AWS appelle automatiquement cette fonction lors du déclenchement.
                                                                                    #  event = données de l'événement déclencheur. context : contexte d'exécution Lambda 
                                                                                    #  dict = avec statusCode HTTP et un message de résumé

    print("[START] Début de l'ingestion TMDB")

  
    stats = {}                                                                      # Dictionnaire pour accumuler les stats d'ingestion

    # ---- FILMS ---------------------------------------------------- #

    # Films populaires du moment
    stats["movies_popular"] = ingest_category(
        endpoint="/movie/popular",
        s3_prefix="raw/movies/popular",
        label="Films populaires",
    )

    # Films les mieux notés
    stats["movies_top_rated"] = ingest_category(
        endpoint="/movie/top_rated",
        s3_prefix="raw/movies/top_rated",
        label="Films top rated",
    )

    # ---- SÉRIES --------------------------------------------------- #

    # Séries populaires du moment
    stats["series_popular"] = ingest_category(
        endpoint="/tv/popular",
        s3_prefix="raw/series/popular",
        label="Séries populaires",
    )

    # Séries les mieux notées
    stats["series_top_rated"] = ingest_category(
        endpoint="/tv/top_rated",
        s3_prefix="raw/series/top_rated",
        label="Séries top rated",
    )

    # ---- RÉSUMÉ --------------------------------------------------- #

    total = sum(stats.values())                                                      # Calcul du total toutes catégories confondues                                             

    print(f"[END] Ingestion terminée — {total} résultats au total : {stats}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Ingestion TMDB réussie",
            "stats": stats,
            "total": total,
        }),
    }
