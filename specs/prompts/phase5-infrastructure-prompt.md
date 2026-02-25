Task: Implement AWS Infrastructure as Code for the Loan Engine Application



You are extending the Loan Engine application (Phases 0-4 complete) with

production-ready infrastructure as code. Generate Terraform modules for all

AWS resources, a production Docker configuration, and a GitHub Actions CI/CD

pipeline. After this phase, the entire application can be deployed to AWS

with a single terraform apply and subsequent pushes auto-deploy via CI/CD.





Context: What Already Exists



Application Architecture (Phases 0-4 complete)





Backend:   Python 3.11, FastAPI, SQLAlchemy 2.0 async, asyncpg

Frontend:  React 18, Vite (builds to frontend/dist/)

Database:  PostgreSQL 15

Storage:   S3 (prod) / local filesystem (dev)

Auth:      OAuth2 password bearer, JWT (python-jose), bcrypt

Container: Multi-stage Docker build (Node → Python)



Existing Deploy Artifacts (from Phase 0 scaffold)





deploy/

├── Dockerfile              # Multi-stage build — EXISTS, may need updates

├── .dockerignore           # EXISTS

├── docker-compose.yml      # Local dev — EXISTS, no changes needed

└── entrypoint.sh           # Container startup — EXISTS, may need updates



terraform/                  # Directory exists with stub files

├── main.tf

├── variables.tf

├── terraform.tfvars

├── outputs.tf

└── modules/

&nbsp;   ├── networking/

&nbsp;   ├── ecs/

&nbsp;   ├── rds/

&nbsp;   ├── alb/

&nbsp;   ├── iam/

&nbsp;   └── secrets/



.github/workflows/

└── deploy.yml              # EXISTS as stub



Target AWS Architecture (extracted from existing deployment)





Region: us-east-1

Naming: {app\_name}-{environment}-{resource}



┌─────────────────────────────────────────────────────────┐

│                  VPC (10.0.0.0/16)                       │

│                                                          │

│  ┌─────────── Public Subnets ─────────────┐              │

│  │  10.0.1.0/24 (us-east-1a)             │              │

│  │  10.0.2.0/24 (us-east-1b)             │              │

│  │                                        │              │

│  │  ┌──────────────────────┐              │              │

│  │  │  ALB                 │              │              │

│  │  │  (loan-engine-test-  │              │              │

│  │  │   alb)               │              │              │

│  │  └──────────┬───────────┘              │              │

│  │             │                          │              │

│  │  ┌──────────┴───────────┐              │              │

│  │  │  NAT Gateway         │              │              │

│  │  └──────────┬───────────┘              │              │

│  └─────────────┼──────────────────────────┘              │

│                │                                          │

│  ┌─────────── Private Subnets ────────────┐              │

│  │  10.0.10.0/24 (us-east-1a)            │              │

│  │  10.0.20.0/24 (us-east-1b)            │              │

│  │                                        │              │

│  │  ┌──────────────────────┐              │              │

│  │  │  ECS Fargate         │              │              │

│  │  │  (loan-engine-test)  │              │              │

│  │  │                      │              │              │

│  │  │  ┌────────────────┐  │              │              │

│  │  │  │ FastAPI + React │  │              │              │

│  │  │  │ Container       │  │              │              │

│  │  │  │ Port 8000       │  │              │              │

│  │  │  └────────────────┘  │              │              │

│  │  └──────────────────────┘              │              │

│  │                                        │              │

│  │  ┌──────────────────────┐              │              │

│  │  │  RDS PostgreSQL 15   │              │              │

│  │  │  db.t3.micro         │              │              │

│  │  │  (loan-engine-test-  │              │              │

│  │  │   db)                │              │              │

│  │  └──────────────────────┘              │              │

│  └────────────────────────────────────────┘              │

└──────────────────────────────────────────────────────────┘



External Services:

&nbsp; ┌────────────┐  ┌──────────────────┐  ┌─────────────┐

&nbsp; │ ECR        │  │ Secrets Manager  │  │ S3 Bucket   │

&nbsp; │ (container │  │ - DATABASE\_URL   │  │ (loan data) │

&nbsp; │  registry) │  │ - SECRET\_KEY     │  └─────────────┘

&nbsp; └────────────┘  └──────────────────┘



&nbsp; ┌──────────────────────────────────────────────────────┐

&nbsp; │ IAM Roles                                            │

&nbsp; │ - ecsTaskExecutionRole (ECR pull, secrets read, logs)│

&nbsp; │ - ecsTaskRole (S3 read/write, secrets read)          │

&nbsp; └──────────────────────────────────────────────────────┘



&nbsp; ┌──────────────────────┐

&nbsp; │ CloudWatch Logs      │

&nbsp; │ /ecs/loan-engine-test│

&nbsp; │ 30-day retention     │

&nbsp; └──────────────────────┘



Security Group Chain





ALB SG (loan-engine-test-alb-sg):

&nbsp; Inbound:  80/tcp from 0.0.0.0/0, 443/tcp from 0.0.0.0/0

&nbsp; Outbound: All traffic



ECS SG (loan-engine-test-ecs-sg):

&nbsp; Inbound:  8000/tcp from ALB SG only

&nbsp; Outbound: All traffic (needs internet via NAT for ECR, S3, Secrets Manager)



RDS SG (loan-engine-test-rds-sg):

&nbsp; Inbound:  5432/tcp from ECS SG only

&nbsp; Outbound: None needed



Environment Variables for ECS Task





ENVIRONMENT=test

DATABASE\_URL=<from Secrets Manager>

DATABASE\_URL\_SYNC=<derived from DATABASE\_URL, replace +asyncpg with nothing>

SECRET\_KEY=<from Secrets Manager>

STORAGE\_TYPE=s3

S3\_BUCKET\_NAME=<from Terraform>

S3\_REGION=us-east-1

AWS\_DEFAULT\_REGION=us-east-1

CORS\_ORIGINS=\["https://{alb\_dns\_name}"]





Files to Create or Modify



FULL REWRITE



| File | Purpose |

|------|---------|

| terraform/main.tf | Root module, provider, state backend |

| terraform/variables.tf | All input variables |

| terraform/terraform.tfvars | Test environment defaults |

| terraform/outputs.tf | Key outputs |

| terraform/modules/networking/main.tf | VPC, subnets, NAT, route tables, SGs |

| terraform/modules/networking/variables.tf | |

| terraform/modules/networking/outputs.tf | |

| terraform/modules/ecs/main.tf | Cluster, service, task definition, ECR, logs |

| terraform/modules/ecs/variables.tf | |

| terraform/modules/ecs/outputs.tf | |

| terraform/modules/rds/main.tf | PostgreSQL instance, subnet group |

| terraform/modules/rds/variables.tf | |

| terraform/modules/rds/outputs.tf | |

| terraform/modules/alb/main.tf | Load balancer, target group, listeners |

| terraform/modules/alb/variables.tf | |

| terraform/modules/alb/outputs.tf | |

| terraform/modules/iam/main.tf | Task execution role, task role, policies |

| terraform/modules/iam/variables.tf | |

| terraform/modules/iam/outputs.tf | |

| terraform/modules/secrets/main.tf | Secrets Manager entries |

| terraform/modules/secrets/variables.tf | |

| terraform/modules/secrets/outputs.tf | |

| deploy/Dockerfile | Production multi-stage build |

| deploy/entrypoint.sh | Production container startup |

| deploy/.dockerignore | Build context exclusions |

| .github/workflows/deploy.yml | Full CI/CD pipeline |



NEW FILES



| File | Purpose |

|------|---------|

| terraform/modules/s3/main.tf | S3 bucket for loan data |

| terraform/modules/s3/variables.tf | |

| terraform/modules/s3/outputs.tf | |

| terraform/backend.tf.example | S3 backend state configuration template |

| scripts/terraform-init.ps1 | Terraform setup helper |

| scripts/deploy-manual.ps1 | Manual deployment script (build, push, update) |



DO NOT MODIFY

• All backend/ Python code (Phases 1-3 complete)

• All frontend/ code (Phase 4 complete)

• deploy/docker-compose.yml (local dev, works as-is)





Terraform Root Module



terraform/main.tf



hcl

─────────────────────────────────────────────────────────

Loan Engine — Root Terraform Configuration

─────────────────────────────────────────────────────────

Provisions all AWS infrastructure for the Loan Engine

application. Uses modular design for reuse across

environments (test, staging, production).

Usage:

cd terraform

terraform init

terraform plan -var-file="terraform.tfvars"

terraform apply -var-file="terraform.tfvars"

─────────────────────────────────────────────────────────



terraform {

&nbsp; required\_version = ">= 1.5.0"



&nbsp; required\_providers {

&nbsp;   aws = {

&nbsp;     source  = "hashicorp/aws"

&nbsp;     version = "~> 5.0"

&nbsp;   }

&nbsp;   random = {

&nbsp;     source  = "hashicorp/random"

&nbsp;     version = "~> 3.5"

&nbsp;   }

&nbsp; }



&nbsp; # Uncomment and configure for remote state:

&nbsp; # backend "s3" {

&nbsp; #   bucket         = "loan-engine-terraform-state"

&nbsp; #   key            = "test/terraform.tfstate"

&nbsp; #   region         = "us-east-1"

&nbsp; #   dynamodb\_table = "loan-engine-terraform-locks"

&nbsp; #   encrypt        = true

&nbsp; # }

}



provider "aws" {

&nbsp; region = var.region



&nbsp; default\_tags {

&nbsp;   tags = {

&nbsp;     Project     = var.app\_name

&nbsp;     Environment = var.environment

&nbsp;     ManagedBy   = "terraform"

&nbsp;   }

&nbsp; }

}



─── Local Values ────────────────────────────────────────



locals {

&nbsp; name\_prefix = "${var.app\_name}-${var.environment}"



&nbsp; common\_tags = {

&nbsp;   Project     = var.app\_name

&nbsp;   Environment = var.environment

&nbsp; }

}



─── Random password for RDS ─────────────────────────────



resource "random\_password" "db\_password" {

&nbsp; length           = 32

&nbsp; special          = true

&nbsp; override\_special = "!#$%\&\*()-\_=+\[]{}<>:?"

}



resource "random\_password" "secret\_key" {

&nbsp; length  = 64

&nbsp; special = false

}



─── Modules ─────────────────────────────────────────────



module "networking" {

&nbsp; source = "./modules/networking"



&nbsp; name\_prefix       = local.name\_prefix

&nbsp; vpc\_cidr          = var.vpc\_cidr

&nbsp; public\_subnet\_cidrs  = var.public\_subnet\_cidrs

&nbsp; private\_subnet\_cidrs = var.private\_subnet\_cidrs

&nbsp; availability\_zones   = var.availability\_zones

&nbsp; container\_port    = var.container\_port

}



module "iam" {

&nbsp; source = "./modules/iam"



&nbsp; name\_prefix        = local.name\_prefix

&nbsp; app\_name           = var.app\_name

&nbsp; s3\_bucket\_arn      = module.s3.bucket\_arn

&nbsp; secrets\_arns       = module.secrets.secret\_arns

&nbsp; log\_group\_arn      = module.ecs.log\_group\_arn

}



module "secrets" {

&nbsp; source = "./modules/secrets"



&nbsp; name\_prefix   = local.name\_prefix

&nbsp; app\_name      = var.app\_name

&nbsp; environment   = var.environment

&nbsp; db\_password   = random\_password.db\_password.result

&nbsp; db\_username   = var.db\_username

&nbsp; db\_name       = var.db\_name

&nbsp; db\_endpoint   = module.rds.db\_endpoint

&nbsp; db\_port       = module.rds.db\_port

&nbsp; secret\_key    = random\_password.secret\_key.result

}



module "s3" {

&nbsp; source = "./modules/s3"



&nbsp; name\_prefix = local.name\_prefix

&nbsp; environment = var.environment

}



module "rds" {

&nbsp; source = "./modules/rds"



&nbsp; name\_prefix        = local.name\_prefix

&nbsp; db\_name            = var.db\_name

&nbsp; db\_username        = var.db\_username

&nbsp; db\_password        = random\_password.db\_password.result

&nbsp; db\_instance\_class  = var.db\_instance\_class

&nbsp; private\_subnet\_ids = module.networking.private\_subnet\_ids

&nbsp; rds\_security\_group\_id = module.networking.rds\_security\_group\_id

}



module "alb" {

&nbsp; source = "./modules/alb"



&nbsp; name\_prefix        = local.name\_prefix

&nbsp; vpc\_id             = module.networking.vpc\_id

&nbsp; public\_subnet\_ids  = module.networking.public\_subnet\_ids

&nbsp; alb\_security\_group\_id = module.networking.alb\_security\_group\_id

&nbsp; container\_port     = var.container\_port

&nbsp; health\_check\_path  = var.health\_check\_path

}



module "ecs" {

&nbsp; source = "./modules/ecs"



&nbsp; name\_prefix            = local.name\_prefix

&nbsp; app\_name               = var.app\_name

&nbsp; environment            = var.environment

&nbsp; region                 = var.region

&nbsp; container\_port         = var.container\_port

&nbsp; container\_cpu          = var.container\_cpu

&nbsp; container\_memory       = var.container\_memory

&nbsp; desired\_count          = var.desired\_count

&nbsp; ecr\_repository\_name    = var.app\_name

&nbsp; private\_subnet\_ids     = module.networking.private\_subnet\_ids

&nbsp; ecs\_security\_group\_id  = module.networking.ecs\_security\_group\_id

&nbsp; target\_group\_arn       = module.alb.target\_group\_arn

&nbsp; execution\_role\_arn     = module.iam.execution\_role\_arn

&nbsp; task\_role\_arn          = module.iam.task\_role\_arn

&nbsp; database\_url\_secret\_arn    = module.secrets.database\_url\_secret\_arn

&nbsp; secret\_key\_secret\_arn      = module.secrets.secret\_key\_secret\_arn

&nbsp; s3\_bucket\_name         = module.s3.bucket\_name

&nbsp; alb\_dns\_name           = module.alb.alb\_dns\_name

&nbsp; log\_retention\_days     = var.log\_retention\_days

}



terraform/variables.tf



hcl

─────────────────────────────────────────────────────────

Input Variables

─────────────────────────────────────────────────────────



─── General ─────────────────────────────────────────────



variable "app\_name" {

&nbsp; description = "Application name, used in resource naming"

&nbsp; type        = string

&nbsp; default     = "loan-engine"

}



variable "environment" {

&nbsp; description = "Deployment environment (test, staging, production)"

&nbsp; type        = string

&nbsp; default     = "test"



&nbsp; validation {

&nbsp;   condition     = contains(\["test", "staging", "production"], var.environment)

&nbsp;   error\_message = "Environment must be test, staging, or production."

&nbsp; }

}



variable "region" {

&nbsp; description = "AWS region"

&nbsp; type        = string

&nbsp; default     = "us-east-1"

}



─── Networking ──────────────────────────────────────────



variable "vpc\_cidr" {

&nbsp; description = "CIDR block for VPC"

&nbsp; type        = string

&nbsp; default     = "10.0.0.0/16"

}



variable "public\_subnet\_cidrs" {

&nbsp; description = "CIDR blocks for public subnets"

&nbsp; type        = list(string)

&nbsp; default     = \["10.0.1.0/24", "10.0.2.0/24"]

}



variable "private\_subnet\_cidrs" {

&nbsp; description = "CIDR blocks for private subnets"

&nbsp; type        = list(string)

&nbsp; default     = \["10.0.10.0/24", "10.0.20.0/24"]

}



variable "availability\_zones" {

&nbsp; description = "Availability zones for multi-AZ deployment"

&nbsp; type        = list(string)

&nbsp; default     = \["us-east-1a", "us-east-1b"]

}



─── Database ────────────────────────────────────────────



variable "db\_name" {

&nbsp; description = "PostgreSQL database name"

&nbsp; type        = string

&nbsp; default     = "loan\_engine"

}



variable "db\_username" {

&nbsp; description = "PostgreSQL master username"

&nbsp; type        = string

&nbsp; default     = "postgres"

}



variable "db\_instance\_class" {

&nbsp; description = "RDS instance class"

&nbsp; type        = string

&nbsp; default     = "db.t3.micro"

}



─── Container ───────────────────────────────────────────



variable "container\_port" {

&nbsp; description = "Port the container listens on"

&nbsp; type        = number

&nbsp; default     = 8000

}



variable "container\_cpu" {

&nbsp; description = "Fargate task CPU units (256 = 0.25 vCPU)"

&nbsp; type        = number

&nbsp; default     = 512

}



variable "container\_memory" {

&nbsp; description = "Fargate task memory in MB"

&nbsp; type        = number

&nbsp; default     = 1024

}



variable "desired\_count" {

&nbsp; description = "Number of ECS tasks to run"

&nbsp; type        = number

&nbsp; default     = 1

}



─── Monitoring ──────────────────────────────────────────



variable "health\_check\_path" {

&nbsp; description = "Health check endpoint path"

&nbsp; type        = string

&nbsp; default     = "/health/ready"

}



variable "log\_retention\_days" {

&nbsp; description = "CloudWatch log retention in days"

&nbsp; type        = number

&nbsp; default     = 30

}



terraform/terraform.tfvars



hcl

─────────────────────────────────────────────────────────

Test Environment Configuration

─────────────────────────────────────────────────────────



app\_name          = "loan-engine"

environment       = "test"

region            = "us-east-1"



Networking

vpc\_cidr              = "10.0.0.0/16"

public\_subnet\_cidrs   = \["10.0.1.0/24", "10.0.2.0/24"]

private\_subnet\_cidrs  = \["10.0.10.0/24", "10.0.20.0/24"]

availability\_zones    = \["us-east-1a", "us-east-1b"]



Database (small for test)

db\_instance\_class = "db.t3.micro"

db\_name           = "loan\_engine"

db\_username       = "postgres"



Container (small for test)

container\_cpu    = 512

container\_memory = 1024

desired\_count    = 1



Monitoring

log\_retention\_days = 30



terraform/outputs.tf



hcl

─────────────────────────────────────────────────────────

Outputs — values needed for deployment and configuration

─────────────────────────────────────────────────────────



output "alb\_dns\_name" {

&nbsp; description = "ALB DNS name (application URL)"

&nbsp; value       = module.alb.alb\_dns\_name

}



output "ecr\_repository\_url" {

&nbsp; description = "ECR repository URL for Docker push"

&nbsp; value       = module.ecs.ecr\_repository\_url

}



output "ecs\_cluster\_name" {

&nbsp; description = "ECS cluster name"

&nbsp; value       = module.ecs.cluster\_name

}



output "ecs\_service\_name" {

&nbsp; description = "ECS service name"

&nbsp; value       = module.ecs.service\_name

}



output "rds\_endpoint" {

&nbsp; description = "RDS instance endpoint"

&nbsp; value       = module.rds.db\_endpoint

&nbsp; sensitive   = true

}



output "s3\_bucket\_name" {

&nbsp; description = "S3 bucket for loan data"

&nbsp; value       = module.s3.bucket\_name

}



output "database\_url\_secret\_arn" {

&nbsp; description = "ARN of DATABASE\_URL secret"

&nbsp; value       = module.secrets.database\_url\_secret\_arn

&nbsp; sensitive   = true

}



output "vpc\_id" {

&nbsp; description = "VPC ID"

&nbsp; value       = module.networking.vpc\_id

}



output "deployment\_instructions" {

&nbsp; description = "Post-apply instructions"

&nbsp; value       = <<-EOT



&nbsp;   ═══════════════════════════════════════════════

&nbsp;   Loan Engine — Deployment Complete

&nbsp;   ═══════════════════════════════════════════════



&nbsp;   Application URL:  http://${module.alb.alb\_dns\_name}

&nbsp;   ECR Repository:   ${module.ecs.ecr\_repository\_url}

&nbsp;   ECS Cluster:      ${module.ecs.cluster\_name}

&nbsp;   ECS Service:      ${module.ecs.service\_name}

&nbsp;   S3 Bucket:        ${module.s3.bucket\_name}



&nbsp;   Next steps:

1\. Build and push Docker image:

&nbsp;        docker build -f deploy/Dockerfile -t ${module.ecs.ecr\_repository\_url}:latest .

&nbsp;        docker push ${module.ecs.ecr\_repository\_url}:latest

2\. Force new deployment:

&nbsp;        aws ecs update-service --cluster ${module.ecs.cluster\_name} \\

&nbsp;          --service ${module.ecs.service\_name} --force-new-deployment

3\. Monitor deployment:

&nbsp;        aws ecs wait services-stable --cluster ${module.ecs.cluster\_name} \\

&nbsp;          --services ${module.ecs.service\_name}



&nbsp;   ═══════════════════════════════════════════════

&nbsp; EOT

}





Terraform Modules



Generate complete, production-ready Terraform code for each module.

Every module must include main.tf, variables.tf, and outputs.tf.



Module: networking



Resources to create:

• VPC with DNS support and hostnames enabled

• Internet Gateway attached to VPC

• 2 Public Subnets across availability zones, map\_public\_ip\_on\_launch=true

• 2 Private Subnets across availability zones

• NAT Gateway in first public subnet with Elastic IP (private subnets need outbound internet for ECR, S3, Secrets Manager)

• Public Route Table with route to Internet Gateway, associated with public subnets

• Private Route Table with route to NAT Gateway, associated with private subnets

• ALB Security Group: inbound 80 + 443 from 0.0.0.0/0, outbound all

• ECS Security Group: inbound var.container\_port from ALB SG only, outbound all

• RDS Security Group: inbound 5432 from ECS SG only, outbound none



Outputs: vpc\_id, public\_subnet\_ids, private\_subnet\_ids, alb\_security\_group\_id, ecs\_security\_group\_id, rds\_security\_group\_id



Module: ecs



Resources to create:

• ECR Repository with image scanning enabled, mutable tags, lifecycle policy keeping last 10 images

• ECS Cluster with container insights enabled

• CloudWatch Log Group with configurable retention

• ECS Task Definition (Fargate, requires compatibilities=\["FARGATE"]):

• Uses execution\_role\_arn and task\_role\_arn from IAM module

• Single container definition:

• Image: {ecr\_repo\_url}:latest

• Port mapping: container\_port

• Environment variables: ENVIRONMENT, STORAGE\_TYPE=s3, S3\_BUCKET\_NAME, S3\_REGION, AWS\_DEFAULT\_REGION, CORS\_ORIGINS

• Secrets (from Secrets Manager): DATABASE\_URL, DATABASE\_URL\_SYNC (same secret, app handles the conversion), SECRET\_KEY

• Log configuration: awslogs driver → CloudWatch log group

• Health check: \["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]

• Essential: true

• CPU and memory from variables

• ECS Service (Fargate):

• Desired count from variable

• Network configuration: private subnets, ECS security group, assign\_public\_ip=false

• Load balancer: target group from ALB module, container port

• Deployment configuration: minimum\_healthy\_percent=50, maximum\_percent=200

• Enable execute command (for debugging)

• Depends on ALB listener



Outputs: cluster\_name, service\_name, ecr\_repository\_url, log\_group\_arn, log\_group\_name



Module: rds



Resources to create:

• DB Subnet Group from private subnets

• RDS Instance:

• Engine: postgres, engine\_version: "15"

• Instance class from variable

• Database name, username, password from variables

• Allocated storage: 20GB, max 100GB (storage autoscaling)

• Storage type: gp3

• Multi-AZ: false for test (parameterize for prod)

• Publicly accessible: false

• DB subnet group and RDS security group

• Skip final snapshot for test (parameterize)

• Backup retention: 7 days

• Storage encrypted: true

• Performance insights: enabled for test (free tier)

• Deletion protection: false for test (true for prod)



Outputs: db\_endpoint, db\_port, db\_instance\_id



Module: alb



Resources to create:

• Application Load Balancer:

• Internal: false

• Public subnets

• ALB security group

• Enable deletion protection: false for test

• Drop invalid header fields: true

• Target Group:

• Port: container\_port, protocol: HTTP

• Target type: ip (required for Fargate)

• VPC from variable

• Health check: path=/health/ready, interval=30, timeout=5, healthy\_threshold=2, unhealthy\_threshold=3, matcher="200"

• Deregistration delay: 30 seconds

• Stickiness: disabled

• HTTP Listener (port 80):

• Forward to target group

• (HTTPS listener can be added when ACM certificate is available)



Outputs: alb\_arn, alb\_dns\_name, target\_group\_arn, listener\_arn



Module: iam



Resources to create:

• ECS Task Execution Role (ecsTaskExecutionRole-{app\_name}):

• Trust policy: ecs-tasks.amazonaws.com

• Managed policy: AmazonECSTaskExecutionRolePolicy

• Inline policy "secrets-read": secretsmanager:GetSecretValue on secret ARNs

• Inline policy "logs-write": logs:CreateLogStream, logs:PutLogEvents on log group

• ECS Task Role (ecsTaskRole-{app\_name}):

• Trust policy: ecs-tasks.amazonaws.com

• Inline policy "s3-access": s3:GetObject, s3:PutObject, s3:ListBucket, s3:DeleteObject on bucket ARN and bucket/\*

• Inline policy "secrets-read": secretsmanager:GetSecretValue on secret ARNs (app reads secrets at runtime too)



Outputs: execution\_role\_arn, execution\_role\_name, task\_role\_arn, task\_role\_name



Module: secrets



Resources to create:

• DATABASE\_URL Secret:

• Name: {app\_name}/{environment}/DATABASE\_URL

• Secret value: postgresql+asyncpg://{username}:{password}@{endpoint}:{port}/{dbname}?sslmode=require

• Description: "PostgreSQL connection string for Loan Engine"

• SECRET\_KEY Secret:

• Name: {app\_name}/{environment}/SECRET\_KEY

• Secret value: random 64-char string from random\_password

• Description: "JWT signing secret for Loan Engine"



Outputs: database\_url\_secret\_arn, secret\_key\_secret\_arn, secret\_arns (list of both)



Module: s3



Resources to create:

• S3 Bucket:

• Bucket name: {name\_prefix}-data (with random suffix to ensure uniqueness)

• Versioning: enabled

• Server-side encryption: AES256 (SSE-S3)

• Public access block: all blocked (block\_public\_acls, block\_public\_policy, ignore\_public\_acls, restrict\_public\_buckets)

• Lifecycle rule: transition to IA after 90 days for archive/ prefix, expire after 365 days

• CORS configuration: allow GET/PUT from ALB DNS



Outputs: bucket\_name, bucket\_arn, bucket\_domain\_name





Docker Configuration



deploy/Dockerfile



dockerfile

─────────────────────────────────────────────────────────

Loan Engine — Production Multi-Stage Dockerfile

─────────────────────────────────────────────────────────

Stage 1: Build frontend (React/Vite)

Stage 2: Production Python runtime with built frontend

─────────────────────────────────────────────────────────



── Stage 1: Frontend Build ──────────────────────────────

FROM node:20-alpine AS frontend-build



WORKDIR /app/frontend



Install dependencies first (cache layer)

COPY frontend/package.json frontend/package-lock.json\* ./

RUN npm ci --production=false



Build the frontend

COPY frontend/ ./

RUN npm run build



── Stage 2: Production Runtime ──────────────────────────

FROM python:3.11-slim AS production



Metadata

LABEL maintainer="Loan Engine Team"

LABEL description="Loan Engine API + Frontend"



Prevent Python from writing .pyc files and enable unbuffered output

ENV PYTHONDONTWRITEBYTECODE=1 \\

&nbsp;   PYTHONUNBUFFERED=1 \\

&nbsp;   PIP\_NO\_CACHE\_DIR=1 \\

&nbsp;   PIP\_DISABLE\_PIP\_VERSION\_CHECK=1



WORKDIR /app



Install system dependencies

RUN apt-get update \&\& \\

&nbsp;   apt-get install -y --no-install-recommends \\

&nbsp;       gcc \\

&nbsp;       libpq-dev \\

&nbsp;       curl \\

&nbsp;   \&\& rm -rf /var/lib/apt/lists/\*



Install Python dependencies (cache layer)

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt



Copy application code

COPY backend/ ./backend/

COPY alembic/ ./alembic/

COPY alembic.ini .



Copy entrypoint script

COPY deploy/entrypoint.sh .

RUN chmod +x entrypoint.sh



Copy built frontend from Stage 1

COPY --from=frontend-build /app/frontend/dist ./frontend/dist



Create non-root user

RUN groupadd -r appuser \&\& useradd -r -g appuser -d /app appuser

RUN mkdir -p /app/storage \&\& chown -R appuser:appuser /app



Switch to non-root user

USER appuser



Health check

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \\

&nbsp;   CMD curl -f http://localhost:8000/health || exit 1



EXPOSE 8000



ENTRYPOINT \["./entrypoint.sh"]



deploy/entrypoint.sh



bash

\#!/bin/bash

─────────────────────────────────────────────────────────

Loan Engine — Container Entrypoint

─────────────────────────────────────────────────────────

Runs database migrations and seed scripts before starting

the application server. Suitable for ECS Fargate deployment.

─────────────────────────────────────────────────────────

set -e



echo "============================================"

echo "Loan Engine — Container Startup"

echo "Environment: ${ENVIRONMENT:-production}"

echo "============================================"



── Step 1: Database Migrations ──────────────────────────

echo ""

echo "\[1/3] Running database migrations..."

MAX\_RETRIES=5

RETRY\_COUNT=0



until alembic upgrade head; do

&nbsp;   RETRY\_COUNT=$((RETRY\_COUNT + 1))

&nbsp;   if \[ $RETRY\_COUNT -ge $MAX\_RETRIES ]; then

&nbsp;       echo "ERROR: Migrations failed after $MAX\_RETRIES attempts"

&nbsp;       exit 1

&nbsp;   fi

&nbsp;   echo "  Migration attempt $RETRY\_COUNT failed. Retrying in 5s..."

&nbsp;   echo "  (Database may still be starting up)"

&nbsp;   sleep 5

done

echo "  Migrations complete."



── Step 2: Seed Admin User ─────────────────────────────

echo ""

echo "\[2/3] Ensuring admin user exists..."

python -m backend.auth.create\_admin || {

&nbsp;   echo "  WARNING: Admin user creation failed (may already exist)"

}

echo "  Admin user check complete."



── Step 3: Seed Reference Data ──────────────────────────

echo ""

echo "\[3/3] Seeding reference data..."

python -m backend.seed\_data || {

&nbsp;   echo "  WARNING: Seed data script failed (may already exist)"

}

echo "  Seed data complete."



── Start Application ────────────────────────────────────

echo ""

echo "============================================"

echo "Starting application server..."

echo "  Port: 8000"

echo "  Workers: ${WEB\_CONCURRENCY:-1}"

echo "============================================"



exec uvicorn backend.api.main:app \\

&nbsp;   --host 0.0.0.0 \\

&nbsp;   --port 8000 \\

&nbsp;   --workers "${WEB\_CONCURRENCY:-1}" \\

&nbsp;   --log-level info \\

&nbsp;   --access-log \\

&nbsp;   --proxy-headers \\

&nbsp;   --forwarded-allow-ips='\*'



deploy/.dockerignore





Version control

.git

.gitignore



Python

\_\_pycache\_\_

\*.pyc

\*.pyo

\*.egg-info

.venv

venv

env

.pytest\_cache

.ruff\_cache

.mypy\_cache



Node

node\_modules

frontend/node\_modules



IDE

.vscode

.idea

\*.swp

\*.swo



Build artifacts (frontend build happens in Docker)

frontend/dist



Infrastructure

terraform

.terraform



Documentation

\*.md

docs/



Specs and scripts (not needed in container)

specs/

scripts/



Environment files (secrets injected via Secrets Manager)

.env

.env.\*

!.env.example



Storage (mounted or S3 in production)

storage/



Deploy (only Dockerfile and entrypoint needed, handled by COPY)

deploy/docker-compose.yml

deploy/aws/





GitHub Actions CI/CD



.github/workflows/deploy.yml



yaml

─────────────────────────────────────────────────────────

Loan Engine — CI/CD Pipeline

─────────────────────────────────────────────────────────

Triggers on push to main branch.

Steps: Lint → Test → Build → Push to ECR → Deploy to ECS

─────────────────────────────────────────────────────────



name: Deploy to AWS ECS



on:

&nbsp; push:

&nbsp;   branches: \[main]

&nbsp; workflow\_dispatch:

&nbsp;   inputs:

&nbsp;     environment:

&nbsp;       description: 'Deployment environment'

&nbsp;       required: true

&nbsp;       default: 'test'

&nbsp;       type: choice

&nbsp;       options:

• test

• staging

• production



env:

&nbsp; AWS\_REGION: us-east-1

&nbsp; ECR\_REPOSITORY: loan-engine

&nbsp; ECS\_CLUSTER: loan-engine-${{ github.event.inputs.environment || 'test' }}

&nbsp; ECS\_SERVICE: loan-engine-${{ github.event.inputs.environment || 'test' }}



permissions:

&nbsp; contents: read

&nbsp; id-token: write



jobs:



&nbsp; # ── Job 1: Lint \& Type Check ───────────────────────────

&nbsp; lint:

&nbsp;   name: Lint

&nbsp;   runs-on: ubuntu-latest

&nbsp;   steps:

• uses: actions/checkout@v4

• uses: actions/setup-python@v5

&nbsp;       with:

&nbsp;         python-version: '3.11'

&nbsp;         cache: 'pip'

• name: Install dependencies

&nbsp;       run: pip install ruff

• name: Lint backend

&nbsp;       run: ruff check backend/



&nbsp; # ── Job 2: Backend Tests ───────────────────────────────

&nbsp; test-backend:

&nbsp;   name: Backend Tests

&nbsp;   runs-on: ubuntu-latest

&nbsp;   needs: lint



&nbsp;   services:

&nbsp;     postgres:

&nbsp;       image: postgres:15-alpine

&nbsp;       env:

&nbsp;         POSTGRES\_DB: loan\_engine\_test

&nbsp;         POSTGRES\_USER: postgres

&nbsp;         POSTGRES\_PASSWORD: postgres

&nbsp;       ports:

• 5432:5432

&nbsp;       options: >-

&nbsp;         --health-cmd "pg\_isready -U postgres"

&nbsp;         --health-interval 10s

&nbsp;         --health-timeout 5s

&nbsp;         --health-retries 5



&nbsp;   steps:

• uses: actions/checkout@v4

• uses: actions/setup-python@v5

&nbsp;       with:

&nbsp;         python-version: '3.11'

&nbsp;         cache: 'pip'

• name: Install dependencies

&nbsp;       run: pip install -e ".\[dev]"

• name: Run tests

&nbsp;       env:

&nbsp;         DATABASE\_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/loan\_engine\_test

&nbsp;         DATABASE\_URL\_SYNC: postgresql://postgres:postgres@localhost:5432/loan\_engine\_test

&nbsp;         SECRET\_KEY: test-secret-key-ci

&nbsp;         ENVIRONMENT: test

&nbsp;         STORAGE\_TYPE: local

&nbsp;         LOCAL\_STORAGE\_PATH: ./storage

&nbsp;       run: |

&nbsp;         pytest backend/tests/ -v --tb=short --timeout=30 \\

&nbsp;           --junitxml=test-results.xml

• name: Upload test results

&nbsp;       uses: actions/upload-artifact@v4

&nbsp;       if: always()

&nbsp;       with:

&nbsp;         name: test-results

&nbsp;         path: test-results.xml



&nbsp; # ── Job 3: Frontend Build Test ─────────────────────────

&nbsp; test-frontend:

&nbsp;   name: Frontend Build

&nbsp;   runs-on: ubuntu-latest

&nbsp;   needs: lint



&nbsp;   steps:

• uses: actions/checkout@v4

• uses: actions/setup-node@v4

&nbsp;       with:

&nbsp;         node-version: '20'

&nbsp;         cache: 'npm'

&nbsp;         cache-dependency-path: frontend/package-lock.json

• name: Install dependencies

&nbsp;       working-directory: frontend

&nbsp;       run: npm ci

• name: Build frontend

&nbsp;       working-directory: frontend

&nbsp;       run: npm run build

• name: Verify build output

&nbsp;       run: |

&nbsp;         test -f frontend/dist/index.html || (echo "Build failed: index.html missing" \&\& exit 1)

&nbsp;         echo "Frontend build successful"



&nbsp; # ── Job 4: Build \& Deploy ──────────────────────────────

&nbsp; deploy:

&nbsp;   name: Build \& Deploy

&nbsp;   runs-on: ubuntu-latest

&nbsp;   needs: \[test-backend, test-frontend]

&nbsp;   if: github.ref == 'refs/heads/main'



&nbsp;   steps:

• uses: actions/checkout@v4

• name: Configure AWS credentials

&nbsp;       uses: aws-actions/configure-aws-credentials@v4

&nbsp;       with:

&nbsp;         aws-access-key-id: ${{ secrets.AWS\_ACCESS\_KEY\_ID }}

&nbsp;         aws-secret-access-key: ${{ secrets.AWS\_SECRET\_ACCESS\_KEY }}

&nbsp;         aws-region: ${{ env.AWS\_REGION }}

• name: Login to Amazon ECR

&nbsp;       id: ecr-login

&nbsp;       uses: aws-actions/amazon-ecr-login@v2

• name: Build Docker image

&nbsp;       env:

&nbsp;         ECR\_REGISTRY: ${{ steps.ecr-login.outputs.registry }}

&nbsp;         IMAGE\_TAG: ${{ github.sha }}

&nbsp;       run: |

&nbsp;         docker build \\

&nbsp;           -f deploy/Dockerfile \\

&nbsp;           -t $ECR\_REGISTRY/$ECR\_REPOSITORY:$IMAGE\_TAG \\

&nbsp;           -t $ECR\_REGISTRY/$ECR\_REPOSITORY:latest \\

&nbsp;           .

&nbsp;         echo "image=$ECR\_REGISTRY/$ECR\_REPOSITORY:$IMAGE\_TAG" >> $GITHUB\_OUTPUT

• name: Push to ECR

&nbsp;       env:

&nbsp;         ECR\_REGISTRY: ${{ steps.ecr-login.outputs.registry }}

&nbsp;         IMAGE\_TAG: ${{ github.sha }}

&nbsp;       run: |

&nbsp;         docker push $ECR\_REGISTRY/$ECR\_REPOSITORY:$IMAGE\_TAG

&nbsp;         docker push $ECR\_REGISTRY/$ECR\_REPOSITORY:latest

• name: Update ECS task definition

&nbsp;       env:

&nbsp;         ECR\_REGISTRY: ${{ steps.ecr-login.outputs.registry }}

&nbsp;         IMAGE\_TAG: ${{ github.sha }}

&nbsp;       run: |

&nbsp;         # Get current task definition

&nbsp;         TASK\_DEF=$(aws ecs describe-services \\

&nbsp;           --cluster $ECS\_CLUSTER \\

&nbsp;           --services $ECS\_SERVICE \\

&nbsp;           --query 'services\[0].taskDefinition' \\

&nbsp;           --output text)



&nbsp;         # Get task definition JSON and update image

&nbsp;         aws ecs describe-task-definition \\

&nbsp;           --task-definition $TASK\_DEF \\

&nbsp;           --query 'taskDefinition' | \\

&nbsp;         jq --arg IMAGE "$ECR\_REGISTRY/$ECR\_REPOSITORY:$IMAGE\_TAG" \\

&nbsp;           '.containerDefinitions\[0].image = $IMAGE |

&nbsp;            del(.taskDefinitionArn, .revision, .status, .requiresAttributes,

&nbsp;                .compatibilities, .registeredAt, .registeredBy)' > updated-task-def.json



&nbsp;         # Register new task definition

&nbsp;         NEW\_TASK\_DEF=$(aws ecs register-task-definition \\

&nbsp;           --cli-input-json file://updated-task-def.json \\

&nbsp;           --query 'taskDefinition.taskDefinitionArn' \\

&nbsp;           --output text)



&nbsp;         echo "New task definition: $NEW\_TASK\_DEF"



&nbsp;         # Update service

&nbsp;         aws ecs update-service \\

&nbsp;           --cluster $ECS\_CLUSTER \\

&nbsp;           --service $ECS\_SERVICE \\

&nbsp;           --task-definition $NEW\_TASK\_DEF \\

&nbsp;           --force-new-deployment

• name: Wait for deployment

&nbsp;       run: |

&nbsp;         echo "Waiting for ECS service to stabilize..."

&nbsp;         aws ecs wait services-stable \\

&nbsp;           --cluster $ECS\_CLUSTER \\

&nbsp;           --services $ECS\_SERVICE

&nbsp;         echo "Deployment complete!"

• name: Verify deployment

&nbsp;       run: |

&nbsp;         ALB\_DNS=$(aws elbv2 describe-load-balancers \\

&nbsp;           --names "${{ env.ECS\_CLUSTER }}-alb" \\

&nbsp;           --query 'LoadBalancers\[0].DNSName' \\

&nbsp;           --output text 2>/dev/null || echo "")



&nbsp;         if \[ -n "$ALB\_DNS" ]; then

&nbsp;           echo "Application URL: http://$ALB\_DNS"

&nbsp;           # Wait a moment for the new task to register

&nbsp;           sleep 10

&nbsp;           HTTP\_CODE=$(curl -s -o /dev/null -w "%{http\_code}" "http://$ALB\_DNS/health" || echo "000")

&nbsp;           if \[ "$HTTP\_CODE" = "200" ]; then

&nbsp;             echo "Health check passed!"

&nbsp;           else

&nbsp;             echo "WARNING: Health check returned $HTTP\_CODE (may still be deploying)"

&nbsp;           fi

&nbsp;         fi





Helper Scripts



scripts/terraform-init.ps1



powershell

scripts/terraform-init.ps1

Initialize Terraform and create the state backend resources



param(

&nbsp;   \[string]$Environment = "test",

&nbsp;   \[string]$Region = "us-east-1",

&nbsp;   \[switch]$CreateStateBackend

)



$ErrorActionPreference = "Stop"

Write-Host "=== Loan Engine Terraform Setup ===" -ForegroundColor Cyan



Verify Terraform installed

if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) {

&nbsp;   Write-Host "ERROR: Terraform not found. Install from https://developer.hashicorp.com/terraform/install" -ForegroundColor Red

&nbsp;   exit 1

}



terraform --version



Verify AWS credentials

Write-Host "`nVerifying AWS credentials..." -ForegroundColor Yellow

aws sts get-caller-identity

if ($LASTEXITCODE -ne 0) {

&nbsp;   Write-Host "ERROR: AWS credentials not configured. Run 'aws configure' or set environment variables." -ForegroundColor Red

&nbsp;   exit 1

}



Create state backend if requested

if ($CreateStateBackend) {

&nbsp;   Write-Host "`nCreating Terraform state backend..." -ForegroundColor Yellow



&nbsp;   $StateBucket = "loan-engine-terraform-state"

&nbsp;   $LockTable = "loan-engine-terraform-locks"



&nbsp;   # Create S3 bucket for state

&nbsp;   aws s3api create-bucket --bucket $StateBucket --region $Region 2>$null

&nbsp;   aws s3api put-bucket-versioning --bucket $StateBucket --versioning-configuration Status=Enabled

&nbsp;   aws s3api put-bucket-encryption --bucket $StateBucket --server-side-encryption-configuration '{

&nbsp;       "Rules": \[{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]

&nbsp;   }'

&nbsp;   aws s3api put-public-access-block --bucket $StateBucket --public-access-block-configuration '{

&nbsp;       "BlockPublicAcls": true, "IgnorePublicAcls": true,

&nbsp;       "BlockPublicPolicy": true, "RestrictPublicBuckets": true

&nbsp;   }'



&nbsp;   # Create DynamoDB table for state locking

&nbsp;   aws dynamodb create-table --table-name $LockTable --region $Region `

&nbsp;       --attribute-definitions AttributeName=LockID,AttributeType=S `

&nbsp;       --key-schema AttributeName=LockID,KeyType=HASH `

&nbsp;       --billing-mode PAY\_PER\_REQUEST 2>$null



&nbsp;   Write-Host "  State bucket: $StateBucket" -ForegroundColor Green

&nbsp;   Write-Host "  Lock table:   $LockTable" -ForegroundColor Green

&nbsp;   Write-Host "`n  Uncomment the backend block in terraform/main.tf to use remote state." -ForegroundColor Yellow

}



Initialize Terraform

Write-Host "`nInitializing Terraform..." -ForegroundColor Yellow

Push-Location terraform

terraform init

Pop-Location



Write-Host "`n=== Setup Complete ===" -ForegroundColor Cyan

Write-Host "Next steps:"

Write-Host "  cd terraform"

Write-Host "  terraform plan -var-file=terraform.tfvars"

Write-Host "  terraform apply -var-file=terraform.tfvars"



scripts/deploy-manual.ps1



powershell

scripts/deploy-manual.ps1

Manual deployment: build, push to ECR, update ECS service



param(

&nbsp;   \[string]$Environment = "test",

&nbsp;   \[string]$Region = "us-east-1",

&nbsp;   \[string]$AppName = "loan-engine",

&nbsp;   \[switch]$SkipBuild,

&nbsp;   \[switch]$SkipPush

)



$ErrorActionPreference = "Stop"



$Cluster = "$AppName-$Environment"

$Service = "$AppName-$Environment"

$EcrRepo = $AppName



Write-Host "=== Loan Engine Manual Deployment ===" -ForegroundColor Cyan

Write-Host "  Environment: $Environment"

Write-Host "  Cluster:     $Cluster"

Write-Host "  Service:     $Service"



Get AWS account ID and ECR URL

$AccountId = (aws sts get-caller-identity --query Account --output text)

$EcrUrl = "$AccountId.dkr.ecr.$Region.amazonaws.com/$EcrRepo"

$ImageTag = "$(Get-Date -Format 'yyyyMMdd-HHmmss')"



Write-Host "  ECR URL:     $EcrUrl"

Write-Host "  Image Tag:   $ImageTag"



Step 1: Build

if (-not $SkipBuild) {

&nbsp;   Write-Host "`n\[1/4] Building Docker image..." -ForegroundColor Yellow

&nbsp;   docker build -f deploy/Dockerfile -t "${EcrUrl}:${ImageTag}" -t "${EcrUrl}:latest" .

&nbsp;   if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Build failed" -ForegroundColor Red; exit 1 }

&nbsp;   Write-Host "  Build complete." -ForegroundColor Green

} else {

&nbsp;   Write-Host "`n\[1/4] Skipping build." -ForegroundColor Gray

}



Step 2: Push

if (-not $SkipPush) {

&nbsp;   Write-Host "`n\[2/4] Pushing to ECR..." -ForegroundColor Yellow

&nbsp;   aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "$AccountId.dkr.ecr.$Region.amazonaws.com"

&nbsp;   docker push "${EcrUrl}:${ImageTag}"

&nbsp;   docker push "${EcrUrl}:latest"

&nbsp;   Write-Host "  Push complete." -ForegroundColor Green

} else {

&nbsp;   Write-Host "`n\[2/4] Skipping push." -ForegroundColor Gray

}



Step 3: Update ECS

Write-Host "`n\[3/4] Updating ECS service..." -ForegroundColor Yellow

aws ecs update-service --cluster $Cluster --service $Service --force-new-deployment | Out-Null

Write-Host "  Service update triggered." -ForegroundColor Green



Step 4: Wait for stability

Write-Host "`n\[4/4] Waiting for deployment to stabilize..." -ForegroundColor Yellow

aws ecs wait services-stable --cluster $Cluster --services $Service

Write-Host "  Deployment complete!" -ForegroundColor Green



Show application URL

$AlbDns = (aws elbv2 describe-load-balancers --names "$Cluster-alb" --query 'LoadBalancers\[0].DNSName' --output text 2>$null)

if ($AlbDns) {

&nbsp;   Write-Host "`n  Application URL: http://$AlbDns" -ForegroundColor Cyan

}





Validation Criteria for Phase 5



After implementation, ALL must pass:

1\. terraform -chdir=terraform init                       → initializes successfully

2\. terraform -chdir=terraform validate                   → configuration is valid

3\. terraform -chdir=terraform plan -var-file=terraform.tfvars → plan shows expected resources

4\. All 7 module directories contain main.tf, variables.tf, outputs.tf

5\. Terraform plan creates these resource types:

• aws\_vpc, aws\_subnet (x4), aws\_nat\_gateway, aws\_internet\_gateway

• aws\_security\_group (x3), aws\_route\_table (x2)

• aws\_ecs\_cluster, aws\_ecs\_service, aws\_ecs\_task\_definition

• aws\_ecr\_repository, aws\_cloudwatch\_log\_group

• aws\_db\_instance, aws\_db\_subnet\_group

• aws\_lb, aws\_lb\_target\_group, aws\_lb\_listener

• aws\_iam\_role (x2), aws\_iam\_role\_policy (x4+)

• aws\_secretsmanager\_secret (x2), aws\_secretsmanager\_secret\_version (x2)

• aws\_s3\_bucket, aws\_s3\_bucket\_versioning, aws\_s3\_bucket\_public\_access\_block

6\. docker build -f deploy/Dockerfile -t loan-engine:test . → builds successfully

7\. Docker image runs and /health returns 200:

&nbsp;     docker run -d -p 8000:8000 -e ENVIRONMENT=test \\

&nbsp;       -e DATABASE\_URL=sqlite+aiosqlite:///test.db \\

&nbsp;       -e SECRET\_KEY=test loan-engine:test

&nbsp;     curl http://localhost:8000/health

8\. deploy/entrypoint.sh includes retry logic for migrations

9\. .github/workflows/deploy.yml is valid YAML with lint, test-backend,

&nbsp;     test-frontend, and deploy jobs

10\. deploy/.dockerignore excludes node\_modules, .git, terraform, specs, .env

11\. Terraform outputs include: alb\_dns\_name, ecr\_repository\_url,

&nbsp;     ecs\_cluster\_name, ecs\_service\_name, s3\_bucket\_name

12\. Security groups follow least-privilege chain: ALB→ECS→RDS

13\. RDS is in private subnets with no public access

14\. S3 bucket has versioning enabled and public access blocked

15\. ECS task definition references Secrets Manager ARNs (not plaintext secrets)

16\. Non-root user in Dockerfile

17\. HEALTHCHECK instruction in Dockerfile

18\. scripts/terraform-init.ps1 and scripts/deploy-manual.ps1 exist and parse correctly



Run validation:



bash

cd terraform

terraform init

terraform validate

terraform plan -var-file=terraform.tfvars



Docker

docker build -f deploy/Dockerfile -t loan-engine:validate .



Workflow syntax

python -c "import yaml; yaml.safe\_load(open('.github/workflows/deploy.yml')); print('Valid')"





Chunking Guide (if prompt exceeds context limits)



| Chunk | File(s) | Focus |

|-------|---------|-------|

| 5a | terraform/main.tf, variables.tf, terraform.tfvars, outputs.tf | Root module |

| 5b | terraform/modules/networking/\* | VPC, subnets, NAT, security groups |

| 5c | terraform/modules/iam/, terraform/modules/secrets/ | IAM roles, policies, Secrets Manager |

| 5d | terraform/modules/rds/, terraform/modules/s3/ | Database and storage |

| 5e | terraform/modules/alb/, terraform/modules/ecs/ | Load balancer, ECS cluster/service/task |

| 5f | deploy/Dockerfile, deploy/entrypoint.sh, deploy/.dockerignore | Container configuration |

| 5g | .github/workflows/deploy.yml | CI/CD pipeline |

| 5h | scripts/terraform-init.ps1, scripts/deploy-manual.ps1 | Helper scripts |



Prepend specs/context/project-context.md to each chunk.

The Terraform chunks need the architecture diagram and security group chain

from the Context section above.



