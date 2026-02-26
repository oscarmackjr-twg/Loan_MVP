# ECS Task Execution Role (pull image, logs, secrets at startup)
resource "aws_iam_role" "ecs_execution" {
  name_prefix        = "ecsTaskExecution-${var.app_name}-${var.environment}-"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
  tags = { Name = "ecsTaskExecutionRole-${var.app_name}-${var.environment}" }
}

resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_execution_logs" {
  name_prefix = "logs-"
  role        = aws_iam_role.ecs_execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
      Resource = "${aws_cloudwatch_log_group.ecs.arn}:*"
    }]
  })
}

resource "aws_iam_role_policy" "ecs_execution_secrets" {
  name_prefix = "secrets-"
  role        = aws_iam_role.ecs_execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
      Resource = [
        aws_secretsmanager_secret.database_url.arn,
        aws_secretsmanager_secret.secret_key.arn
      ]
    }]
  })
}

# ECS Task Role (app runtime: Secrets Manager, S3)
resource "aws_iam_role" "ecs_task" {
  name_prefix        = "ecsTaskRole-${var.app_name}-${var.environment}-"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
  tags = { Name = "ecsTaskRole-${var.app_name}-${var.environment}" }
}

resource "aws_iam_role_policy" "ecs_task_secrets" {
  name_prefix = "secrets-"
  role        = aws_iam_role.ecs_task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
      Resource = [
        aws_secretsmanager_secret.database_url.arn,
        aws_secretsmanager_secret.secret_key.arn
      ]
    }]
  })
}

resource "aws_iam_role_policy" "ecs_task_s3" {
  name_prefix = "s3-"
  role        = aws_iam_role.ecs_task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
        Resource = ["${aws_s3_bucket.app.arn}/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = [aws_s3_bucket.app.arn]
      }
    ]
  })
}
