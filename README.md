# 🎬 Canal Data Platform

Pipeline de données end-to-end sur AWS inspiré du contexte Canal+.
Ingestion de données TMDB → Transformation → Lineage Tracking.

## 🏗️ Architecture globale

```
TMDB API
   │
   ▼
AWS Lambda (Python)          ← Jour 1 ✅
   │  Ingestion des films/séries
   ▼
Amazon S3 (raw/)             ← Jour 1 ✅
   │  Stockage JSON brut
   ▼
AWS Glue (PySpark)           ← Jour 2
   │  Nettoyage & transformation
   ▼
Amazon Redshift Serverless   ← Jour 2
   │  Data Warehouse
   ▼
DBT (SQL models)             ← Jour 3
   │  Couche analytique
   ▼
Apache Airflow (DAGs)        ← Jour 4
   │  Orchestration
   ▼
OpenLineage + Marquez        ← Jour 4
   Data Lineage Tracking
```

## 📁 Structure du projet

```
canal-data-platform/
├── README.md
├── ingestion/
│   ├── lambda_tmdb.py        # Fonction Lambda d'ingestion TMDB
│   ├── test_local.py         # Tests unitaires locaux
│   └── deploy_lambda.sh      # Script de déploiement
├── glue/                     # Jour 2
├── dbt/                      # Jour 3
├── dags/                     # Jour 4
└── terraform/
    ├── main.tf               # Provider + variables + outputs
    ├── s3.tf                 # Bucket S3 raw data
    └── iam.tf                # Rôle IAM Lambda + politique S3
```

## 🚀 Démarrage rapide — Jour 1

### Prérequis
- AWS CLI configuré (`aws configure`)
- Terraform >= 1.3
- Python 3.12
- Clé API TMDB gratuite sur [themoviedb.org](https://www.themoviedb.org/settings/api)

### 1. Cloner et configurer
```bash
git clone https://github.com/ton-username/canal-data-platform.git
cd canal-data-platform

# Définir la clé TMDB (ne jamais commiter ce fichier !)
echo 'tmdb_api_key = "ta_clé_ici"' > terraform/terraform.tfvars
```

### 2. Tester en local AVANT de déployer
```bash
export TMDB_API_KEY="ta_clé_ici"
export S3_BUCKET="canal-data-platform-raw"

cd ingestion
python test_local.py
```

### 3. Déployer sur AWS
```bash
bash ingestion/deploy_lambda.sh
```

### 4. Invoquer la Lambda manuellement
```bash
aws lambda invoke \
  --function-name canal-tmdb-ingestion \
  --log-type Tail \
  output.json

cat output.json
```

### 5. Vérifier les données dans S3
```bash
aws s3 ls s3://canal-data-platform-raw/raw/ --recursive
```

## 🛠️ Stack technique

| Outil | Usage |
|-------|-------|
| AWS Lambda | Ingestion des données TMDB |
| Amazon S3 | Stockage raw (JSON) |
| AWS IAM | Gestion des permissions |
| Terraform | Infrastructure as Code |
| Python 3.12 | Code Lambda |
| TMDB API | Source de données films/séries |

## 💰 Coûts AWS estimés (projet complet)

| Service | Estimation |
|---------|-----------|
| S3 | ~0€ (free tier) |
| Lambda | ~0€ (free tier) |
| Glue | ~1-2€ |
| Redshift Serverless | ~3-5€ |
| **Total** | **< 10€** |

---
*Projet réalisé dans le cadre de la préparation à un entretien Data Engineer.*
