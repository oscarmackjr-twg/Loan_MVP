#!/usr/bin/env bash
# Create ECR repository for Loan Engine (run once per account/region)
# Usage: ./create-ecr-repo.sh [repo-name] [region]
set -e
REPO_NAME="${1:-loan-engine}"
REGION="${2:-us-east-1}"
aws ecr describe-repositories --repository-names "$REPO_NAME" --region "$REGION" 2>/dev/null && echo "Repo $REPO_NAME already exists" && exit 0
aws ecr create-repository --repository-name "$REPO_NAME" --region "$REGION" --image-scanning-configuration scanOnPush=true
echo "Created ECR repo: $REPO_NAME in $REGION"
