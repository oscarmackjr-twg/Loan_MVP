terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  # Optional: use S3 backend for team state (uncomment and set bucket/key)
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "loan-engine/qa/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-locks"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = "qa"
      Project     = "loan-engine"
      ManagedBy   = "terraform"
    }
  }
}
