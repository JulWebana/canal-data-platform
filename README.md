# Canal Data Platform

Projet personnel réalisé dans le cadre de ma montée en compétence en Data Engineering.

L'idée de départ était simple : construire un pipeline de données complet sur AWS, 
du début à la fin en utilisant les mêmes outils que les équipes data en entreprise. 

Les données viennent de l'API TMDB (films et séries).

---

## Ce que fait ce projet

Les données de films et séries sont récupérées depuis l'API TMDB et stockées brutes dans S3.
Elles sont ensuite transformées via AWS Glue, chargées dans Redshift puis modélisées avec dbt 
pour produire des tables analytiques exploitables. Tout le pipeline est orchestré par Airflow
et chaque mouvement de données est tracé via OpenLineage (standard ouvert de traçabilité des données) 
et visualisé dans Marquez (interface graphique qui affiche le chemin complet des données).

En résumé, le pipeline suit cette logique :

    Ingestion (Lambda)
         |
    Stockage brut (S3)
         |
    Transformation (Glue)
         |
    Entrepôt de données (Redshift)
         |
    Modélisation analytique (dbt)
         |
    Orchestration (Airflow)
         |
    Data Lineage (OpenLineage / Marquez)

---

## Stack technique

- **AWS Lambda** : ingestion des données depuis l'API TMDB vers S3
- **Amazon S3** : stockage des données brutes en JSON
- **AWS Glue** : transformation et nettoyage des données (PySpark)
- **Amazon Redshift Serverless** : entrepôt de données analytique
- **dbt** : modélisation SQL, tests de qualité des données
- **Apache Airflow** : orchestration du pipeline
- **OpenLineage / Marquez** : data lineage - traçabilité des données
- **Terraform** : infrastructure as code pour provisionner les ressources AWS
- **Python** : Lambda, Glue, tests unitaires

---

## Structure du projet

    canal-data-platform/
    |
    |-- ingestion/
    |   |-- lambda_tmdb.py        Fonction Lambda qui appelle l'API TMDB et dépose les données dans S3
    |   |-- test_local.py         Tests unitaires pour valider la Lambda en local avant déploiement
    |   |-- deploy_lambda.sh      Script de déploiement : zip du code et terraform apply
    |
    |-- glue/
    |   |-- transform_job.py      Job Glue : lit le JSON brut depuis S3, nettoie et charge dans Redshift
    |   |-- setup_redshift.sql    Script SQL pour créer le schéma staging et les tables dans Redshift
    |
    |-- dbt/
    |   |-- dbt_project.yml       Configuration principale du projet dbt
    |   |-- models/
    |       |-- staging/
    |       |   |-- stg_movies.sql      Modèle staging des films
    |       |   |-- stg_series.sql      Modèle staging des séries
    |       |   |-- sources.yml         Déclaration des sources et tests de qualité
    |       |-- mart/
    |           |-- fct_top_content.sql     Top contenus films et séries classés par note
    |           |-- dim_languages.sql       Dimension des langues du catalogue
    |
    |-- dags/
    |   |-- canal_pipeline.py     DAG Airflow qui orchestre Lambda, Glue et DBT dans le bon ordre
    |
    |-- terraform/
    |   |-- main.tf               Configuration du provider AWS et des variables
    |   |-- s3.tf                 Bucket S3 avec versioning, chiffrement et lifecycle
    |   |-- iam.tf                Rôles IAM et politiques de sécurité pour Lambda et Glue
    |   |-- redshift.tf           Redshift Serverless et job Glue
    |
    |-- docker-compose.yml        Lance Airflow et Marquez en local via Docker

---

## Lancer le projet en local

### Prérequis

- AWS CLI configuré
- Terraform version 1.3 minimum
- Python 3.12
- Docker et Docker Compose
- Une clé API TMDB gratuite sur themoviedb.org

### 1. Configurer les variables d'environnement

Créer un fichier `.env` à la racine du projet :

    TMDB_API_KEY = votre_clé_api
    S3_BUCKET = canal-data-platform-raw

Créer un fichier `terraform/terraform.tfvars` :

    tmdb_api_key      = "votre_clé_api"
    redshift_user     = "admin"
    redshift_password = "votre_mot_de_passe"

### 2. Tester la Lambda en local

    export $(cat .env | xargs)
    cd ingestion && python3 test_local.py

### 3. Déployer l'infrastructure AWS

    bash ingestion/deploy_lambda.sh

### 4. Lancer Airflow et Marquez via Docker

    docker-compose up -d

    Interface Airflow : http://localhost:8080  (admin / admin)
    Interface Marquez : http://localhost:3000

---

## Estimation des coûts AWS

Ce projet a été conçu pour rester dans les limites du free tier AWS autant que possible.

| Service              | Coût estimé |
|----------------------|-------------|
| S3                   | 0 EUR       |
| Lambda               | 0 EUR       |
| Glue                 | 1 à 2 EUR   |
| Redshift Serverless  | 3 à 5 EUR   |
| Total                | moins de 10 EUR |

---

## Ce que j'ai appris

Ce projet m'a permis de pratiquer concrètement des concepts que je connaissais en théorie :
la différence entre données brutes et données transformées (Bronze / Silver / Gold), 
la notion de data lineage, l'orchestration d'un pipeline avec des dépendances entre tâches 
et l'importance des tests de qualité des données avec dbt.
