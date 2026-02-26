output "application_url" {
  description = "QA application URL (allow 2-5 min for ECS to become healthy)"
  value       = "http://${aws_lb.main.dns_name}"
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.main.dns_name
}

output "s3_bucket" {
  description = "S3 bucket name (loan-engine-qa)"
  value       = aws_s3_bucket.app.id
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.address
  sensitive   = true
}

output "ecs_cluster_name" {
  description = "ECS cluster name (loan-engine-qa)"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.app.name
}

output "ecr_repository_url" {
  description = "ECR repository URL for pushing QA image"
  value       = aws_ecr_repository.app.repository_url
}
