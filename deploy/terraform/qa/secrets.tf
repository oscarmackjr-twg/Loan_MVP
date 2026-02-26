# SECRET_KEY (random per apply unless we use a fixed value)
resource "random_password" "secret_key" {
  length  = 64
  special = true
}

# Secrets Manager: DATABASE_URL (injected into ECS task)
resource "aws_secretsmanager_secret" "database_url" {
  name        = "${var.app_name}/${var.environment}/DATABASE_URL"
  description = "DATABASE_URL for ${var.app_name} QA"
  tags        = { Name = "${var.app_name}/${var.environment}/DATABASE_URL" }
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id = aws_secretsmanager_secret.database_url.id
  secret_string = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.main.address}:5432/${var.db_name}?sslmode=require"
}

# Secrets Manager: SECRET_KEY (JWT/session signing)
resource "aws_secretsmanager_secret" "secret_key" {
  name        = "${var.app_name}/${var.environment}/SECRET_KEY"
  description = "SECRET_KEY for ${var.app_name} QA"
  tags        = { Name = "${var.app_name}/${var.environment}/SECRET_KEY" }
}

resource "aws_secretsmanager_secret_version" "secret_key" {
  secret_id     = aws_secretsmanager_secret.secret_key.id
  secret_string = random_password.secret_key.result
}
