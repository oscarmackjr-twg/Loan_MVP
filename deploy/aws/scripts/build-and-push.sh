#!/usr/bin/env bash
# Build image and push to ECR. Run from repo root.
# Requires: AWS CLI, Docker, aws ecr get-login-password
# Usage: ./build-and-push.sh [region] [tag]
set -e
REGION="${1:-us-east-1}"
TAG="${2:-latest}"
REPO_NAME="${ECR_REPO_NAME:-loan-engine}"
ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"
URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}"
docker build -f deploy/Dockerfile -t "${REPO_NAME}:${TAG}" .
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
docker tag "${REPO_NAME}:${TAG}" "${URI}:${TAG}"
docker push "${URI}:${TAG}"
echo "Pushed ${URI}:${TAG}"
