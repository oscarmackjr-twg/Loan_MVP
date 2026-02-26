# ECR repository for QA (loan-engine-qa)
resource "aws_ecr_repository" "app" {
  name = var.ecr_repository_name
  image_scanning_configuration { scan_on_push = true }
  tags = { Name = var.ecr_repository_name }
}
