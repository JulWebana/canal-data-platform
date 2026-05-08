
# Création et configuration du bucket S3 qui recevra toutes les données brutes ingérées depuis TMDB.


# Bucket S3 principal                                                 

resource "aws_s3_bucket" "raw_data" {
 
  bucket = var.s3_bucket_name

  
  tags = {                                                                           # Tags pour identifier et organiser la ressource dans la console AWS
    Name        = var.s3_bucket_name
    Environment = var.environment
    Project     = "canal-data-platform"
    ManagedBy   = "terraform"
  }
}


# Versioning                                                          


resource "aws_s3_bucket_versioning" "raw_data_versioning" {                           # Active le versioning sur le bucket. chaque fichier écrasé conserve ses versions précédentes.
  bucket = aws_s3_bucket.raw_data.id                                                  # Référence au bucket créé ci-dessus

  versioning_configuration {
    status = "Enabled"  # "Enabled" ou "Suspended"
  }
}


# Chiffrement                                                          


resource "aws_s3_bucket_server_side_encryption_configuration" "raw_data_encryption" {       # Active le chiffrement côté serveur (SSE) avec une clé AWS gérée (SSE-S3).
  bucket = aws_s3_bucket.raw_data.id

  rule {
    apply_server_side_encryption_by_default {
      
      sse_algorithm = "AES256"                                                              # AES256 = chiffrement SSE-S3 géré automatiquement par AWS
    }
  }
}


# Blocage de l'accès publique                                            


resource "aws_s3_bucket_public_access_block" "raw_data_block" {                           # Bloque tout accès public au bucket.
  bucket = aws_s3_bucket.raw_data.id

  block_public_acls       = true                                                          # Bloque les ACL publiques
  block_public_policy     = true                                                          # Bloque les policies publiques
  ignore_public_acls      = true                                                          # Ignore les ACL publiques existantes
  restrict_public_buckets = true                                                          # Restreint les buckets publics
}


# Lifecicle - nettoyage automatique                                   


resource "aws_s3_bucket_lifecycle_configuration" "raw_data_lifecycle" {                  # Règle de cycle de vie : supprime automatiquement les données brutes après 90 jours pour maîtriser les coûts S3.
  bucket = aws_s3_bucket.raw_data.id

  rule {
    id     = "expire-raw-data"                                                           # Identifiant de la règle
    status = "Enabled"                                                                   # Règle active

                                                                
    filter {                                                                             # Filtre sur le préfixe "raw/" — ne s'applique qu'aux données brutes
      prefix = "raw/"
    }

    expiration {
      days = 90                                                                          # Suppression automatique après 90 jours
    }
  }
}
