
# Point d'entrée Terraform : configure le provider AWS et définit les variables globales du projet.


# PROVIDER AWS                                                         


terraform {
  
  required_version = ">= 1.3.0"                               # Version minimale de Terraform requise

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"                                      # Version 5.x du provider AWS
    }
  }
}

# Configuration du provider AWS

provider "aws" {
  region = var.aws_region
}


# VARIABLES                                                            


# Région AWS cible 

variable "aws_region" {
  description = "Région AWS où déployer les ressources"
  type        = string
  default     = "eu-west-1"  # Irlande — proche de la France, bon choix pour Canal+
}


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


# OUTPUTS                                                              

output "s3_bucket_name" {
  description = "Nom du bucket S3 créé"
  value       = aws_s3_bucket.raw_data.bucket
}


output "lambda_role_arn" {                                        # Affiche l'ARN du rôle IAM Lambda 
  description = "ARN du rôle IAM attaché à la Lambda"
  value       = aws_iam_role.lambda_role.arn
}
