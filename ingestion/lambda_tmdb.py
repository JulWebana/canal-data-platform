"""
lambda_tmdb.py
--------------
Fonction AWS Lambda qui récupère les données de films et séries
depuis l'API TMDB, puis les stocke en format JSON brut dans S3.

Déclenchement : manuel ou via EventBridge (scheduler)
Destination   : S3 bucket, dossiers raw/movies/ et raw/series/
"""

import json          # Pour sérialiser les données en JSON
import os            # Pour lire les variables d'environnement
import boto3         # SDK AWS pour interagir avec S3
import urllib.request  # Pour faire des requêtes HTTP sans dépendance externe
from datetime import datetime  # Pour horodater les fichiers déposés dans S3


# ------------------------------------------------------------------ #
# CONFIGURATION                                                        #
# ------------------------------------------------------------------ #

# Clé API TMDB — injectée via variable d'environnement Lambda
# (ne jamais hardcoder une clé dans le code !)
TMDB_API_KEY = os.environ["TMDB_API_KEY"]

# Nom du bucket S3 où seront déposées les données brutes
S3_BUCKET = os.environ["S3_BUCKET"]

# URL de base de l'API TMDB v3
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Langue des résultats (fr-FR pour coller au contexte Canal+)
LANGUAGE = "fr-FR"

# Nombre de pages à récupérer par catégorie (1 page = 20 résultats)
MAX_PAGES = 3


# ------------------------------------------------------------------ #
# CLIENT S3                                                            #
# ------------------------------------------------------------------ #

# Initialisation du client S3 (boto3 utilise automatiquement
# les credentials du rôle IAM attaché à la Lambda)
s3_client = boto3.client("s3")


# ------------------------------------------------------------------ #
# FONCTIONS UTILITAIRES                                                #
# ------------------------------------------------------------------ #

def fetch_tmdb(endpoint: str, page: int = 1) -> dict:
    """
    Appelle un endpoint de l'API TMDB et retourne la réponse JSON.

    Args:
        endpoint : chemin de l'API, ex: "/movie/popular"
        page     : numéro de page pour la pagination

    Returns:
        dict contenant la réponse JSON de l'API
    """
    # Construction de l'URL complète avec clé API, langue et page
    url = (
        f"{TMDB_BASE_URL}{endpoint}"
        f"?api_key={TMDB_API_KEY}"
        f"&language={LANGUAGE}"
        f"&page={page}"
    )

    # Ouverture de la requête HTTP GET
    with urllib.request.urlopen(url) as response:
        # Lecture et décodage de la réponse en UTF-8
        raw = response.read().decode("utf-8")

    # Conversion de la chaîne JSON en dictionnaire Python
    return json.loads(raw)


def save_to_s3(data: dict, s3_key: str) -> None:
    """
    Sérialise un dictionnaire Python en JSON et le dépose dans S3.

    Args:
        data   : dictionnaire Python à sauvegarder
        s3_key : chemin complet dans le bucket S3
                 ex: "raw/movies/popular/2026-05-06_page1.json"
    """
    # Conversion du dictionnaire en chaîne JSON bien formatée
    json_body = json.dumps(data, ensure_ascii=False, indent=2)

    # Envoi vers S3 via put_object
    s3_client.put_object(
        Bucket=S3_BUCKET,           # Nom du bucket cible
        Key=s3_key,                 # Chemin du fichier dans le bucket
        Body=json_body.encode("utf-8"),  # Contenu encodé en bytes
        ContentType="application/json",  # Métadonnée MIME type
    )

    # Log pour le suivi dans CloudWatch
    print(f"[S3] Fichier déposé : s3://{S3_BUCKET}/{s3_key}")


def ingest_category(endpoint: str, s3_prefix: str, label: str) -> int:
    """
    Récupère plusieurs pages d'un endpoint TMDB et les stocke dans S3.

    Args:
        endpoint  : endpoint TMDB, ex: "/movie/popular"
        s3_prefix : préfixe S3, ex: "raw/movies/popular"
        label     : nom lisible pour les logs, ex: "Films populaires"

    Returns:
        Nombre total de résultats ingérés
    """
    # Date du jour pour partitionner les fichiers par date
    today = datetime.utcnow().strftime("%Y-%m-%d")

    total_results = 0  # Compteur de résultats ingérés

    # Boucle sur les pages (de 1 à MAX_PAGES inclus)
    for page in range(1, MAX_PAGES + 1):

        print(f"[TMDB] Récupération : {label} — page {page}/{MAX_PAGES}")

        # Appel à l'API TMDB pour cette page
        data = fetch_tmdb(endpoint, page=page)

        # Construction du chemin S3 avec partitionnement par date
        # Structure : raw/movies/popular/2026-05-06/page_1.json
        s3_key = f"{s3_prefix}/{today}/page_{page}.json"

        # Sauvegarde dans S3
        save_to_s3(data, s3_key)

        # Comptage des résultats de cette page
        page_count = len(data.get("results", []))
        total_results += page_count

        print(f"[TMDB] {page_count} résultats récupérés pour la page {page}")

    return total_results


# ------------------------------------------------------------------ #
# HANDLER PRINCIPAL (point d'entrée Lambda)                           #
# ------------------------------------------------------------------ #

def lambda_handler(event: dict, context) -> dict:
    """
    Point d'entrée de la fonction Lambda.
    AWS appelle automatiquement cette fonction lors du déclenchement.

    Args:
        event   : données de l'événement déclencheur (non utilisé ici)
        context : contexte d'exécution Lambda (non utilisé ici)

    Returns:
        dict avec statusCode HTTP et un message de résumé
    """
    print("[START] Début de l'ingestion TMDB")

    # Dictionnaire pour accumuler les stats d'ingestion
    stats = {}

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

    # Calcul du total toutes catégories confondues
    total = sum(stats.values())
    print(f"[END] Ingestion terminée — {total} résultats au total : {stats}")

    # Retour standard Lambda (compatible API Gateway si besoin)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Ingestion TMDB réussie",
            "stats": stats,
            "total": total,
        }),
    }
