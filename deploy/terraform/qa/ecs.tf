# CloudWatch log group for ECS
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${local.name_prefix}"
  retention_in_days  = 14
  tags              = { Name = "/ecs/${local.name_prefix}" }
}

# ECR image URL (repo created in ecr.tf)
locals {
  ecr_image = "${aws_ecr_repository.app.repository_url}:${var.docker_image_tag}"
}

# ECS cluster (QA compute: loan-engine-qa)
resource "aws_ecs_cluster" "main" {
  name = var.ecs_cluster_name
  tags = { Name = var.ecs_cluster_name }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name       = aws_ecs_cluster.main.name
  capacity_providers = ["FARGATE"]
  default_capacity_provider_strategy {
    base              = 0
    weight            = 1
    capacity_provider = "FARGATE"
  }
}

# Task definition
resource "aws_ecs_task_definition" "app" {
  family                   = local.name_prefix
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.ecs_cpu
  memory                   = var.ecs_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn             = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = "app"
    image     = local.ecr_image
    essential = true
    portMappings = [{ containerPort = 8000, protocol = "tcp" }]
    environment = concat(
      [
        { name = "CORS_ORIGINS", value = "[\"http://${aws_lb.main.dns_name}\"]" },
        { name = "ENABLE_SCHEDULER", value = "true" },
        { name = "NODE_ENV", value = "production" },
        { name = "STORAGE_TYPE", value = "s3" },
        { name = "S3_BUCKET_NAME", value = aws_s3_bucket.app.id },
        { name = "S3_REGION", value = var.aws_region }
      ]
    )
    secrets = [
      { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn },
      { name = "SECRET_KEY", valueFrom = aws_secretsmanager_secret.secret_key.arn }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8000/health/ready || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
  }])
  tags = { Name = local.name_prefix }
}

# ECS service
resource "aws_ecs_service" "app" {
  name            = var.ecs_service_name
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.ecs_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name  = "app"
    container_port   = 8000
  }

  tags = { Name = var.ecs_service_name }
}
