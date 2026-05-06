# terraform/s3.tf
# ----------------
# Création et configuration du bucket S3 qui recevra
# toutes les données brutes ingérées depuis TMDB.

# ------------------------------------------------------------------ #
# BUCKET S3 PRINCIPAL                                                  #
# ------------------------------------------------------------------ #

resource "aws_s3_bucket" "raw_data" {
  # Nom du bucket, défini dans main.tf via variable
  bucket = var.s3_bucket_name

  # Tags pour identifier et organiser la ressource dans la console AWS
  tags = {
    Name        = var.s3_bucket_name
    Environment = var.environment
    Project     = "canal-data-platform"
    ManagedBy   = "terraform"
  }
}


# ------------------------------------------------------------------ #
# VERSIONING                                                           #
# ------------------------------------------------------------------ #

# Active le versioning sur le bucket :
# chaque fichier écrasé conserve ses versions précédentes.
# Utile pour rejouer un pipeline sans perdre les données brutes.
resource "aws_s3_bucket_versioning" "raw_data_versioning" {
  bucket = aws_s3_bucket.raw_data.id  # Référence au bucket créé ci-dessus

  versioning_configuration {
    status = "Enabled"  # "Enabled" ou "Suspended"
  }
}


# ------------------------------------------------------------------ #
# CHIFFREMENT                                                          #
# ------------------------------------------------------------------ #

# Active le chiffrement côté serveur (SSE) avec une clé AWS gérée (SSE-S3).
# Bonne pratique de sécurité même pour des données non sensibles.
resource "aws_s3_bucket_server_side_encryption_configuration" "raw_data_encryption" {
  bucket = aws_s3_bucket.raw_data.id

  rule {
    apply_server_side_encryption_by_default {
      # AES256 = chiffrement SSE-S3 géré automatiquement par AWS
      sse_algorithm = "AES256"
    }
  }
}


# ------------------------------------------------------------------ #
# BLOCAGE DE L'ACCÈS PUBLIC                                            #
# ------------------------------------------------------------------ #

# Bloque tout accès public au bucket.
# Les données ne doivent être accessibles que par les services AWS internes
# (Lambda, Glue) via IAM — jamais exposées publiquement.
resource "aws_s3_bucket_public_access_block" "raw_data_block" {
  bucket = aws_s3_bucket.raw_data.id

  block_public_acls       = true  # Bloque les ACL publiques
  block_public_policy     = true  # Bloque les policies publiques
  ignore_public_acls      = true  # Ignore les ACL publiques existantes
  restrict_public_buckets = true  # Restreint les buckets publics
}


# ------------------------------------------------------------------ #
# LIFECYCLE — NETTOYAGE AUTOMATIQUE                                    #
# ------------------------------------------------------------------ #

# Règle de cycle de vie : supprime automatiquement les données brutes
# après 90 jours pour maîtriser les coûts S3.
resource "aws_s3_bucket_lifecycle_configuration" "raw_data_lifecycle" {
  bucket = aws_s3_bucket.raw_data.id

  rule {
    id     = "expire-raw-data"  # Identifiant de la règle
    status = "Enabled"          # Règle active

    # Filtre sur le préfixe "raw/" — ne s'applique qu'aux données brutes
    filter {
      prefix = "raw/"
    }

    # Expiration automatique après 90 jours
    expiration {
      days = 90
    }
  }
}
