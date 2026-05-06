"""
test_local.py
-------------
Script de test LOCAL de la Lambda TMDB.
Permet de valider le code AVANT de déployer sur AWS,
sans coûts et sans avoir besoin de zipper/déployer.

Usage :
    export TMDB_API_KEY="ta_clé_ici"
    export S3_BUCKET="canal-data-platform-raw"
    python ingestion/test_local.py
"""

import os           # Pour lire les variables d'environnement
import json         # Pour afficher les résultats proprement
import unittest     # Framework de tests standard Python
from unittest.mock import patch, MagicMock  # Pour simuler (mocker) boto3/S3

# On importe notre Lambda comme un module Python classique
from lambda_tmdb import lambda_handler, fetch_tmdb, save_to_s3


# ------------------------------------------------------------------ #
# TESTS UNITAIRES                                                      #
# ------------------------------------------------------------------ #

class TestLambdaTMDB(unittest.TestCase):
    """
    Suite de tests unitaires pour la Lambda TMDB.
    Chaque méthode test_xxx est exécutée automatiquement.
    """

    def test_fetch_tmdb_movies_popular(self):
        """
        Vérifie que fetch_tmdb retourne bien une liste de films
        depuis l'endpoint /movie/popular.
        Ce test fait un VRAI appel API — nécessite TMDB_API_KEY.
        """
        print("\n[TEST] fetch_tmdb — films populaires...")

        # Appel réel à l'API TMDB
        result = fetch_tmdb("/movie/popular", page=1)

        # Vérifications sur la structure de la réponse
        self.assertIn("results", result)           # La clé "results" doit exister
        self.assertIsInstance(result["results"], list)  # Ce doit être une liste
        self.assertGreater(len(result["results"]), 0)   # La liste ne doit pas être vide

        # Vérifie que chaque film a les champs attendus
        first_movie = result["results"][0]
        self.assertIn("title", first_movie)         # Titre du film
        self.assertIn("vote_average", first_movie)  # Note moyenne
        self.assertIn("popularity", first_movie)    # Score de popularité

        print(f"      ✅ {len(result['results'])} films récupérés")
        print(f"      Premier film : {first_movie['title']} (note: {first_movie['vote_average']})")

    def test_fetch_tmdb_series_popular(self):
        """
        Vérifie que fetch_tmdb retourne bien une liste de séries
        depuis l'endpoint /tv/popular.
        """
        print("\n[TEST] fetch_tmdb — séries populaires...")

        result = fetch_tmdb("/tv/popular", page=1)

        self.assertIn("results", result)
        self.assertGreater(len(result["results"]), 0)

        # Les séries ont "name" au lieu de "title"
        first_series = result["results"][0]
        self.assertIn("name", first_series)

        print(f"      ✅ {len(result['results'])} séries récupérées")
        print(f"      Première série : {first_series['name']}")

    @patch("lambda_tmdb.s3_client")  # On remplace boto3 par un mock (faux S3)
    def test_save_to_s3(self, mock_s3):
        """
        Vérifie que save_to_s3 appelle correctement boto3.put_object.
        On utilise un MOCK pour ne pas vraiment écrire sur S3.
        """
        print("\n[TEST] save_to_s3 — écriture S3 mockée...")

        # Données de test à sauvegarder
        test_data = {"results": [{"title": "Test Film", "vote_average": 8.5}]}
        test_key = "raw/movies/popular/2026-05-06/page_1.json"

        # Appel de la fonction avec le mock S3
        save_to_s3(test_data, test_key)

        # Vérifie que put_object a bien été appelé une fois
        mock_s3.put_object.assert_called_once()

        # Récupère les arguments passés à put_object
        call_kwargs = mock_s3.put_object.call_args.kwargs

        # Vérifie que les bons paramètres ont été passés
        self.assertEqual(call_kwargs["Key"], test_key)
        self.assertEqual(call_kwargs["ContentType"], "application/json")

        print("      ✅ put_object appelé avec les bons paramètres")

    @patch("lambda_tmdb.s3_client")  # Mock S3 pour éviter les vrais appels
    def test_lambda_handler_full(self, mock_s3):
        """
        Test d'intégration du handler complet :
        fait de vrais appels TMDB mais mocke S3.
        """
        print("\n[TEST] lambda_handler — test d'intégration complet...")

        # Simule un événement Lambda vide (pas de payload nécessaire ici)
        fake_event = {}
        fake_context = MagicMock()  # Objet context simulé

        # Exécution du handler
        response = lambda_handler(fake_event, fake_context)

        # Vérifie le code de retour HTTP
        self.assertEqual(response["statusCode"], 200)

        # Parse le body JSON retourné
        body = json.loads(response["body"])

        # Vérifie que toutes les catégories ont été ingérées
        self.assertIn("movies_popular", body["stats"])
        self.assertIn("movies_top_rated", body["stats"])
        self.assertIn("series_popular", body["stats"])
        self.assertIn("series_top_rated", body["stats"])

        # Vérifie que le total est cohérent (> 0)
        self.assertGreater(body["total"], 0)

        print(f"      ✅ Handler exécuté — {body['total']} résultats ingérés")
        print(f"      Stats : {body['stats']}")


# ------------------------------------------------------------------ #
# EXÉCUTION DIRECTE                                                    #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    """
    Point d'entrée quand on lance directement : python test_local.py
    Lance tous les tests et affiche un rapport.
    """
    print("=" * 50)
    print("  Tests locaux — Canal Data Platform J1")
    print("=" * 50)

    # Vérifie que les variables d'environnement sont définies
    if not os.environ.get("TMDB_API_KEY"):
        print("\n⚠️  ATTENTION : TMDB_API_KEY non définie !")
        print("   export TMDB_API_KEY='ta_clé_ici'")
        exit(1)

    if not os.environ.get("S3_BUCKET"):
        # Valeur par défaut pour les tests locaux
        os.environ["S3_BUCKET"] = "canal-data-platform-raw"
        print(f"\n💡 S3_BUCKET non définie, utilisation de la valeur par défaut : {os.environ['S3_BUCKET']}")

    # Lance les tests avec un niveau de verbosité élevé
    unittest.main(verbosity=2)
