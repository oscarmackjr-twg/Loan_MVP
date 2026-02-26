# Loan Engine – Deploy Assets

- **Dockerfile** – Multi-stage build (frontend + backend); run from repo root: `docker build -f deploy/Dockerfile .`
- **docker-compose.yml** – Local/test run with Postgres: `docker compose -f deploy/docker-compose.yml up -d` (from repo root)
- **aws/** – **Development** deployment: PowerShell scripts for ECS/Fargate, RDS, ALB, ECR (e.g. `deploy-aws.ps1`).
- **terraform/qa/** – **QA** deployment: Terraform for S3 `loan-engine-qa`, RDS `loan-engine-qa`, ECS cluster/service `loan-engine-qa`, and ECR `loan-engine-qa`. See `terraform/qa/README.md` and `deploy-qa.ps1`.
- **CI/CD** – `.github/workflows/deploy-test.yml` builds and deploys to AWS test on push to `main`

See **`docs/AWS_DEPLOYMENT_PLAN.md`** and **`docs/DEPLOYMENT_COOKBOOK.md`** for the full deployment plan and step-by-step checklist.

**Docker build fails with "failed to solve: process ..."**  
The message is truncated. Scroll up in the build output to see which `RUN` step failed and the real error (e.g. `npm ci`, `npm run build`, or `pip install`). The Dockerfile uses `pip install --upgrade pip` before backend deps and relaxed version pins in `requirements.txt` so wheels resolve in Docker; if a step still fails, fix the reported package or command.

**Building on Windows:**  
The Dockerfile normalizes CRLF to LF in the frontend stage (using `dos2unix`) so that files checked out with Windows line endings don’t break `npm run build` in the Linux container. Ensure you’re building from the repo root: `docker build -f deploy/Dockerfile .`
