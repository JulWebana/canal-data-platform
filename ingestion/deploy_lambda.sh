#!/bin/bash

# Script de déploiement de la Lambda TMDB.

# Ce script crée un ZIP du code Lambda ensuite lance terraform init + apply pour déployer l'infra et enfin affiche les outputs Terraform (nom du bucket, ARN du rôle)


set -e  # Arrête le script immédiatement si une commande échoue

echo "  Canal Data Platform"

# ÉTAPE 1 — ZIP DU CODE LAMBDA                                       

echo ""
echo "[1/3] Création du ZIP de la Lambda..."

# Création d'une archive ZIP contenant uniquement le fichier lambda_tmdb.py (sans structure de dossiers)

cd ingestion
zip -j ingestion.zip lambda_tmdb.py

echo " ingestion/ingestion.zip créé"
cd ..


# ÉTAPE 2 — TERRAFORM INIT

echo ""
echo "[2/3] Initialisation Terraform..."

cd terraform

terraform init -input=false                  #télécharge le provider AWS et configure le backend. -input=false désactive les prompts interactifs

echo " Terraform initialisé" 


# ÉTAPE 3 — TERRAFORM APPLY                                           

echo ""
echo "[3/3] Déploiement de l'infrastructure AWS..."
echo "      (La clé TMDB sera demandée si TF_VAR_tmdb_api_key n'est pas définie)"

terraform apply -auto-approve              # terraform apply déploie toutes les ressources définies dans les fichiers .tf

echo " Déploiement terminé !"


terraform output                            # Affiche les outputs définis dans main.tf (bucket name, role ARN)

cd ..

echo ""
echo " Prochaine étape : tester la Lambda depuis la console AWS"
echo "   ou via : aws lambda invoke --function-name canal-tmdb-ingestion output.json"
