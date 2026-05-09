"""
DAG Airflow — Canal Data Platform

Ce DAG orchestre le pipeline de données complet dans le bon ordre :

Étape 1 : trigger_lambda   : déclenche la Lambda AWS qui ingère les données TMDB dans S3
Étape 2 : run_glue_job     : lance le job Glue qui transforme les données S3 et les charge dans Redshift
Étape 3 : run_dbt          : exécute les modèles DBT qui produisent les tables analytiques finales

Fréquence : tous les jours à minuit (schedule="@daily")

"""

from datetime import datetime, timedelta                             # Pour définir les dates et délais du DAG
from airflow import DAG                                              # Classe principale pour créer un DAG Airflow

from airflow.providers.amazon.aws.operators.lambda_function import LambdaInvokeFunctionOperator  # Opérateur pour déclencher une Lambda AWS
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator                          # Opérateur pour lancer un job Glue
from airflow.operators.bash import BashOperator                                                  # Opérateur pour exécuter des commandes bash (utilisé pour dbt)


# CONFIGURATION DU DAG

default_args = {                                                # Arguments par défaut appliqués à toutes les tâches du DAG
    "owner": "canal_data_team",                                 # Propriétaire du DAG - visible dans l'interface Airflow
    "retries": 1,                                               # Nombre de tentatives en cas d'échec d'une tâche
    "retry_delay": timedelta(minutes=5),                        # Délai entre deux tentatives : 5 minutes
    "email_on_failure": False,                                  # Pas d'email en cas d'échec
}

# Définition du DAG principal

with DAG(
    dag_id="canal_data_pipeline",                               
    description="Pipeline complet : Lambda - Glue - dbt",     
    default_args=default_args,                                 
    schedule="@daily",                                          # Fréquence d'exécution : tous les jours à minuit
    start_date=datetime(2026, 5, 1),                            # Date de début du DAG
    catchup=False,                                              # Ne pas rattraper les exécutions passées manquées
    tags=["canal", "tmdb", "data-platform"],                    # Tags pour filtrer les DAGs dans l'interface Airflow

) as dag:


    # ÉTAPE 1 - LAMBDA : ingestion des données TMDB dans S3

    trigger_lambda = LambdaInvokeFunctionOperator(

        task_id="trigger_lambda",                               # Identifiant unique de la tâche dans ce DAG
        function_name="canal-tmdb-ingestion",                   # Nom de la Lambda AWS à déclencher
        aws_conn_id="aws_default",                              # Connexion AWS configurée dans Airflow
        invocation_type="RequestResponse",                      # Attend la fin de l'exécution avant de passer à l'étape suivante
    )


    # ÉTAPE 2 - GLUE : transformation des données S3 et chargement dans Redshift

    run_glue_job = GlueJobOperator(

        task_id="run_glue_job",                              
        job_name="canal-transform-job",                         # Nom du job Glue AWS à exécuter
        aws_conn_id="aws_default",                              
        wait_for_completion=True,                               # Attend la fin du job Glue avant de passer à dbt

    )


    # ÉTAPE 3 - dbt : exécution des modèles analytiques

    run_dbt = BashOperator(

        task_id="run_dbt",                                     
        bash_command="cd /opt/airflow/dbt && dbt run && dbt test",  # Lance dbt run puis dbt test pour vérifier la qualité des données
    )


    # Ordre d’exécution du pipeline

    trigger_lambda > run_glue_job > run_dbt                   

