# terraform/redshift.tf
# Configuration de Redshift Serverless et du job Glue

# REDSHIFT SERVERLESS — NAMESPACE

resource "aws_redshiftserverless_namespace" "canal" {
  namespace_name      = "canal-data-platform"                                  # Nom du namespace Redshift Serverless
  db_name             = "canal_db"                                             # Nom de la base de données
  admin_username      = var.redshift_user                                      # Utilisateur admin (défini en variable sensible)
  admin_user_password = var.redshift_password                                  # Mot de passe admin (défini en variable sensible)

  tags = {
    Project   = "canal-data-platform"
    ManagedBy = "terraform"
  }
}


# REDSHIFT SERVERLESS — WORKGROUP

resource "aws_redshiftserverless_workgroup" "canal" {
  namespace_name = aws_redshiftserverless_namespace.canal.namespace_name       # Lié au namespace créé ci-dessus
  workgroup_name = "canal-workgroup"                                           # Nom du workgroup visible dans la console AWS
  base_capacity  = 8                                                           # Capacité en RPU (Redshift Processing Units) — minimum facturable

  tags = {
    Project   = "canal-data-platform"
    ManagedBy = "terraform"
  }
}


# IAM — RÔLE POUR GLUE

resource "aws_iam_role" "glue_role" {
  name = "canal-glue-role"                                                     # Nom du rôle IAM pour le job Glue

  assume_role_policy = jsonencode({                                            # Politique de confiance : seul Glue peut endosser ce rôle
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "glue.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"      # Politique AWS standard pour les jobs Glue
}

resource "aws_iam_role_policy_attachment" "glue_s3" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"                   # Accès S3 complet pour lire les données brutes et écrire les fichiers temporaires
}


# S3 — DOSSIER TEMPORAIRE POUR GLUE

resource "aws_s3_object" "glue_tmp" {
  bucket  = var.s3_bucket_name                                                 # Bucket existant créé dans s3.tf
  key     = "glue-tmp/"                                                        # Dossier temporaire utilisé par Glue lors du chargement dans Redshift
  content = ""                                                                 # Objet vide — crée juste le dossier
}


# S3 — UPLOAD DU SCRIPT GLUE

resource "aws_s3_object" "glue_script" {
  bucket = var.s3_bucket_name                                                  # Bucket où stocker le script Glue
  key    = "glue-scripts/transform_job.py"                                    # Chemin du script dans S3
  source = "../glue/transform_job.py"                                         # Chemin local du script Python
  etag   = filemd5("../glue/transform_job.py")                                # Hash du fichier pour détecter les changements
}


# GLUE JOB

resource "aws_glue_job" "transform" {
  name         = "canal-transform-job"                                         # Nom du job visible dans la console Glue
  role_arn     = aws_iam_role.glue_role.arn                                   # Rôle IAM attaché au job
  glue_version = "4.0"                                                         # Version de Glue (4.0 = Spark 3.3)
  worker_type  = "G.1X"                                                        # Type de worker — G.1X = 1 DPU, suffisant pour ce volume
  number_of_workers = 2                                                        # Nombre de workers Spark (minimum pour Glue)

  command {
    script_location = "s3://${var.s3_bucket_name}/glue-scripts/transform_job.py"  # Chemin S3 du script Python
    python_version  = "3"                                                      # Version Python
  }

  default_arguments = {                                                        # Arguments passés au job à chaque exécution
    "--JOB_NAME"          = "canal-transform-job"
    "--S3_BUCKET"         = var.s3_bucket_name
    "--REDSHIFT_URL"      = "jdbc:redshift://${aws_redshiftserverless_workgroup.canal.endpoint[0].address}:5439/canal_db"  # URL JDBC construite depuis l'endpoint Redshift
    "--REDSHIFT_USER"     = var.redshift_user
    "--REDSHIFT_PASSWORD" = var.redshift_password
    "--REDSHIFT_TMP_DIR"  = "s3://${var.s3_bucket_name}/glue-tmp/"
    "--enable-glue-datacatalog" = "true"                                       # Active le catalogue de données Glue
  }

  tags = {
    Project   = "canal-data-platform"
    ManagedBy = "terraform"
  }
}


# VARIABLES SENSIBLES

variable "redshift_user" {
  description = "Utilisateur admin Redshift"
  type        = string
  sensitive   = true                                                           # Masqué dans les logs Terraform
}

variable "redshift_password" {
  description = "Mot de passe admin Redshift — ne jamais commiter en clair"
  type        = string
  sensitive   = true                                                           # Masqué dans les logs Terraform
}


# OUTPUTS

output "redshift_endpoint" {
  description = "Endpoint de connexion Redshift Serverless"
  value       = aws_redshiftserverless_workgroup.canal.endpoint[0].address    # Adresse de connexion à utiliser dans DBT et Airflow
}

output "glue_job_name" {
  description = "Nom du job Glue"
  value       = aws_glue_job.transform.name
}
