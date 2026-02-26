# Elastic Beanstalk config for Loan Engine

- **Dockerfile** — Docker image for EB. Build from repo root (set `$ECRUri` first, e.g. `123456789012.dkr.ecr.us-east-1.amazonaws.com/loan-engine`):  
  `docker build -f deploy/aws/eb/Dockerfile -t "${ECRUri}:latest" .`  
  Includes a HEALTHCHECK for `/health/ready`.
- **Dockerrun.aws.json** — Single-container Docker descriptor for EB. Replace `YOUR_ACCOUNT` and `YOUR_REGION` (or the full `Image.Name` value) with your ECR URI before creating the application version.

See [ELASTIC_BEANSTALK_COOKBOOK.md](../ELASTIC_BEANSTALK_COOKBOOK.md).
