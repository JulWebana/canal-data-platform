#!/bin/bash
# deploy_lambda.sh
# ----------------
# Script de déploiement de la Lambda TMDB.
# À exécuter depuis la racine du projet : bash ingestion/deploy_lambda.sh
#
# Ce script :
# 1. Crée un ZIP du code Lambda
# 2. Lance terraform init + apply pour déployer l'infra
# 3. Affiche les outputs Terraform (nom du bucket, ARN du rôle)

set -e  # Arrête le script immédiatement si une commande échoue

echo "========================================"
echo "  Canal Data Platform — Déploiement J1  "
echo "========================================"

# ------------------------------------------------------------------ #
# ÉTAPE 1 — ZIP DU CODE LAMBDA                                        #
# ------------------------------------------------------------------ #

echo ""
echo "[1/3] Création du ZIP de la Lambda..."

# On se place dans le dossier ingestion pour zipper le fichier seul
# (sans le chemin complet du dossier dans le ZIP)
cd ingestion
zip -j ingestion.zip lambda_tmdb.py

echo "      ✅ ingestion/ingestion.zip créé"
cd ..


# ------------------------------------------------------------------ #
# ÉTAPE 2 — TERRAFORM INIT (première fois seulement)                  #
# ------------------------------------------------------------------ #

echo ""
echo "[2/3] Initialisation Terraform..."

cd terraform

# terraform init télécharge le provider AWS et configure le backend
# L'option -input=false désactive les prompts interactifs
terraform init -input=false

echo "      ✅ Terraform initialisé"


# ------------------------------------------------------------------ #
# ÉTAPE 3 — TERRAFORM APPLY                                           #
# ------------------------------------------------------------------ #

echo ""
echo "[3/3] Déploiement de l'infrastructure AWS..."
echo "      (La clé TMDB sera demandée si TF_VAR_tmdb_api_key n'est pas définie)"

# terraform apply déploie toutes les ressources définies dans les .tf
# -auto-approve évite la confirmation manuelle (à ne pas utiliser en prod !)
terraform apply -auto-approve

echo ""
echo "========================================"
echo "  ✅ Déploiement terminé !"
echo "========================================"

# Affiche les outputs définis dans main.tf (bucket name, role ARN)
terraform output

cd ..

echo ""
echo "💡 Prochaine étape : tester la Lambda depuis la console AWS"
echo "   ou via : aws lambda invoke --function-name canal-tmdb-ingestion output.json"
