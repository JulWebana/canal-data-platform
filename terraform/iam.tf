# terraform/iam.tf
# -----------------
# Définit le rôle IAM et les permissions attachées à la Lambda.
# Principe du moindre privilège : on n'accorde que ce qui est nécessaire.

# ------------------------------------------------------------------ #
# RÔLE IAM POUR LAMBDA                                                 #
# ------------------------------------------------------------------ #

# Un rôle IAM est une identité AWS que la Lambda va "endosser"
# pour avoir le droit d'appeler d'autres services (S3, CloudWatch...).
resource "aws_iam_role" "lambda_role" {
  name = "canal-lambda-tmdb-role"

  # Politique de confiance (trust policy) : définit qui peut assumer ce rôle.
  # Ici, seul le service Lambda (lambda.amazonaws.com) peut l'utiliser.
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "lambda.amazonaws.com" }
        Action    = "sts:AssumeRole"  # Lambda s'authentifie en assumant ce rôle
      }
    ]
  })

  tags = {
    Project   = "canal-data-platform"
    ManagedBy = "terraform"
  }
}


# ------------------------------------------------------------------ #
# POLITIQUE S3 — LECTURE/ÉCRITURE SUR LE BUCKET RAW                   #
# ------------------------------------------------------------------ #

resource "aws_iam_policy" "lambda_s3_policy" {
  name        = "canal-lambda-s3-policy"
  description = "Autorise la Lambda à écrire dans le bucket S3 raw data"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",     # Écrire un fichier dans S3
          "s3:GetObject",     # Lire un fichier depuis S3
          "s3:ListBucket",    # Lister le contenu d'un bucket
          "s3:DeleteObject"   # Supprimer un fichier (utile pour les tests)
        ]
        # Restriction au seul bucket du projet (pas d'accès à tous les buckets)
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}",       # Le bucket lui-même
          "arn:aws:s3:::${var.s3_bucket_name}/*"      # Tous les objets dedans
        ]
      }
    ]
  })
}


# ------------------------------------------------------------------ #
# POLITIQUE CLOUDWATCH — LOGS                                          #
# ------------------------------------------------------------------ #

# Attache la politique AWS gérée pour les logs CloudWatch.
# Permet à la Lambda d'écrire ses logs (print() → CloudWatch Logs).
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_role.name

  # Politique AWS gérée standard pour les logs Lambda
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}


# ------------------------------------------------------------------ #
# ATTACHEMENT DE LA POLITIQUE S3 AU RÔLE                              #
# ------------------------------------------------------------------ #

# Attache la politique S3 custom créée ci-dessus au rôle Lambda.
# Sans cet attachement, la politique existe mais n'est pas active.
resource "aws_iam_role_policy_attachment" "lambda_s3" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_s3_policy.arn
}


# ------------------------------------------------------------------ #
# FONCTION LAMBDA                                                      #
# ------------------------------------------------------------------ #

# Déploiement de la Lambda depuis un fichier ZIP local.
# Le ZIP doit contenir lambda_tmdb.py à la racine.
resource "aws_lambda_function" "tmdb_ingestion" {
  function_name = "canal-tmdb-ingestion"     # Nom visible dans la console AWS
  role          = aws_iam_role.lambda_role.arn  # Rôle IAM attaché ci-dessus
  runtime       = "python3.12"               # Runtime Python
  handler       = "lambda_tmdb.lambda_handler"  # fichier.fonction
  timeout       = 300                        # Timeout en secondes (5 min max ici)
  memory_size   = 256                        # RAM allouée en Mo

  # Chemin vers le ZIP contenant le code Lambda
  # À créer avec : zip -j ingestion.zip ingestion/lambda_tmdb.py
  filename         = "../ingestion/ingestion.zip"
  source_code_hash = filebase64sha256("../ingestion/ingestion.zip")

  # Variables d'environnement injectées dans la Lambda au runtime
  environment {
    variables = {
      TMDB_API_KEY = var.tmdb_api_key   # Clé API TMDB (variable sensible)
      S3_BUCKET    = var.s3_bucket_name  # Nom du bucket cible
    }
  }

  tags = {
    Project   = "canal-data-platform"
    ManagedBy = "terraform"
  }
}


# ------------------------------------------------------------------ #
# VARIABLE SENSIBLE — CLÉ API TMDB                                    #
# ------------------------------------------------------------------ #

# Déclaration de la variable pour la clé TMDB.
# En pratique : passée via terraform.tfvars ou variable d'environnement
# TF_VAR_tmdb_api_key pour ne pas l'écrire en clair dans le code.
variable "tmdb_api_key" {
  description = "Clé API TMDB — ne jamais commiter en clair"
  type        = string
  sensitive   = true  # Masque la valeur dans les logs Terraform
}
