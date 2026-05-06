# terraform/main.tf
# -----------------
# Point d'entrée Terraform : configure le provider AWS
# et définit les variables globales du projet.

# ------------------------------------------------------------------ #
# PROVIDER AWS                                                         #
# ------------------------------------------------------------------ #

terraform {
  # Version minimale de Terraform requise
  required_version = ">= 1.3.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"  # Version 5.x du provider AWS
    }
  }
}

# Configuration du provider AWS
provider "aws" {
  # La région est lue depuis la variable var.aws_region
  region = var.aws_region
}


# ------------------------------------------------------------------ #
# VARIABLES                                                            #
# ------------------------------------------------------------------ #

# Région AWS cible (modifiable au déploiement)
variable "aws_region" {
  description = "Région AWS où déployer les ressources"
  type        = string
  default     = "eu-west-1"  # Irlande — proche de la France, bon choix pour Canal+
}

# Nom du bucket S3 (doit être globalement unique sur AWS)
variable "s3_bucket_name" {
  description = "Nom du bucket S3 pour stocker les données brutes TMDB"
  type        = string
  default     = "canal-data-platform-raw"
}

# Environnement de déploiement (dev, staging, prod)
variable "environment" {
  description = "Environnement cible"
  type        = string
  default     = "dev"
}


# ------------------------------------------------------------------ #
# OUTPUTS                                                              #
# ------------------------------------------------------------------ #

# Affiche le nom du bucket après apply (utile pour configurer Lambda)
output "s3_bucket_name" {
  description = "Nom du bucket S3 créé"
  value       = aws_s3_bucket.raw_data.bucket
}

# Affiche l'ARN du rôle IAM Lambda (utile pour le déploiement)
output "lambda_role_arn" {
  description = "ARN du rôle IAM attaché à la Lambda"
  value       = aws_iam_role.lambda_role.arn
}
