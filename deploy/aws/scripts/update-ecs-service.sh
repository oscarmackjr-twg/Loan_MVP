#!/usr/bin/env bash
# Force ECS service to deploy new task definition (new image).
# Usage: ./update-ecs-service.sh [region]
set -e
REGION="${1:-us-east-1}"
CLUSTER="${ECS_CLUSTER:-test-cluster}"
SERVICE="${ECS_SERVICE:-loan-engine-test}"
aws ecs update-service --cluster "$CLUSTER" --service "$SERVICE" --region "$REGION" --force-new-deployment --output json | jq -r '.service.deployments[0].status'
echo "Deployment triggered for $SERVICE on $CLUSTER"
