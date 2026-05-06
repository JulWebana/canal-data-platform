"""

Script de test LOCAL de la Lambda TMDB. Il Permet de valider le code AVANT de déployer sur AWS, sans coûts et sans avoir besoin de zipper/déployer.

Usage :
    export TMDB_API_KEY="ta_clé_ici"
    export S3_BUCKET="canal-data-platform-raw"
    python ingestion/test_local.py
"""

import os                                                                 # Pour lire les variables d'environnement
import json                                                               # Pour afficher les résultats proprement
import unittest                                                           # Framework de tests standard Python
from unittest.mock import patch, MagicMock                                # Simule de faux objets AWS pour tester sans connexion réelle à S3 car cela coûte de l'argent
from lambda_tmdb import lambda_handler, fetch_tmdb, save_to_s3            # Importe les fonctions principales de lambda_tmdb.py à tester



# TESTS UNITAIRES                                                      


class TestLambdaTMDB(unittest.TestCase):                                  # Suite de tests unitaires pour la Lambda TMDB. Chaque méthode test_xxx est exécutée automatiquement.
 

    def test_fetch_tmdb_movies_popular(self):                             # Vérifie que fetch_tmdb retourne bien une liste de films depuis l'endpoint /movie/popular.

        print("\n[TEST] fetch_tmdb — films populaires...")

        result = fetch_tmdb("/movie/popular", page=1)                     # Appel réel à l'API TMDB

        # Vérifications sur la structure de la réponse

        self.assertIn("results", result)                                  # La clé "results" doit exister
        self.assertIsInstance(result["results"], list)                    # Ce doit être une liste
        self.assertGreater(len(result["results"]), 0)                     # La liste ne doit pas être vide

        first_movie = result["results"][0]                                # Vérifie que chaque film a les champs attendus 
        self.assertIn("title", first_movie)                               # Titre du film
        self.assertIn("vote_average", first_movie)                        # Note moyenne
        self.assertIn("popularity", first_movie)                          # Score de popularité

        print(f"      {len(result['results'])} films récupérés")
        print(f"      Premier film : {first_movie['title']} (note: {first_movie['vote_average']})")


    def test_fetch_tmdb_series_popular(self):                             # Vérifie que fetch_tmdb retourne bien une liste de séries depuis l'endpoint /tv/popular.
        
        print("\n[TEST] fetch_tmdb — séries populaires...")

        result = fetch_tmdb("/tv/popular", page=1)

        self.assertIn("results", result)
        self.assertGreater(len(result["results"]), 0)


        first_series = result["results"][0]                               # Les séries ont name au lieu de title
        self.assertIn("name", first_series)

        print(f"      {len(result['results'])} séries récupérées")
        print(f"      Première série : {first_series['name']}")

    @patch("lambda_tmdb.s3_client")                                      # On remplace boto3 par un mock (faux S3)


    def test_save_to_s3(self, mock_s3):                                  # Vérifie que save_to_s3 appelle correctement boto3.put_object.

        print("\n[TEST] save_to_s3 — écriture S3 mockée...")


        test_data = {"results": [{"title": "Test Film", "vote_average": 8.5}]}           # Données de test à sauvegarder
        test_key = "raw/movies/popular/2026-05-06/page_1.json"


        save_to_s3(test_data, test_key)                                                  # Appel de la fonction avec le mock S3


        mock_s3.put_object.assert_called_once()                                          # Vérifie que put_object a été appelé exactement une fois

        call_kwargs = mock_s3.put_object.call_args.kwargs                                # Récupère les arguments passés à put_object


        self.assertEqual(call_kwargs["Key"], test_key)                                   # Vérifie que les bons paramètres ont été passés                           
        self.assertEqual(call_kwargs["ContentType"], "application/json")

        print(" put_object appelé avec les bons paramètres")

    @patch("lambda_tmdb.s3_client")                                                       # Mock S3 pour éviter les vrais appels


    def test_lambda_handler_full(self, mock_s3):                                          # Test d'intégration du handler complet : fait de vrais appels TMDB mais mocke S3.
    
        print("\n[TEST] lambda_handler — test d'intégration complet...")

        fake_event = {}                                                                   # Simule un événement Lambda vide      

        fake_context = MagicMock()                                                        # Objet context simulé

        response = lambda_handler(fake_event, fake_context)                               # Exécution du handler

        self.assertEqual(response["statusCode"], 200)                                     # Vérifie que le handler retourne un statusCode 200 

        body = json.loads(response["body"])                                               # Parse le corps de la réponse (JSON string) en dict Python                                                 


        # Vérifie que toutes les catégories ont été ingérées

        self.assertIn("movies_popular", body["stats"])
        self.assertIn("movies_top_rated", body["stats"])
        self.assertIn("series_popular", body["stats"])
        self.assertIn("series_top_rated", body["stats"])

        
        self.assertGreater(body["total"], 0)                                              # Vérifie que le total de résultats ingérés est supérieur à 0                                                

        print(f"      Handler exécuté — {body['total']} résultats ingérés")
        print(f"      Stats : {body['stats']}")



# EXÉCUTION DIRECTE                                                    


if __name__ == "__main__":                                                                 #  Lance tous les tests et affiche un rapport.
    
    print("  Tests locaux — Canal Data Platform J1")

    if not os.environ.get("TMDB_API_KEY"):                                                # Vérifie que les variables d'environnement sont définies
        print("\n  ATTENTION : TMDB_API_KEY non définie !")
        print("   export TMDB_API_KEY='ta_clé_ici'")
        exit(1)

    if not os.environ.get("S3_BUCKET"):
       
        os.environ["S3_BUCKET"] = "canal-data-platform-raw"                                # Valeur par défaut pour les tests locaux

        print(f"\n S3_BUCKET non définie, utilisation de la valeur par défaut : {os.environ['S3_BUCKET']}")


    unittest.main(verbosity=2)                                                            # Lance les tests avec un niveau de verbosité élevé c-à-d affiche beaucoup de détails.
