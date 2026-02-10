# AWS Deployment Plan: Loan Engine (Test Environment)

**Audience:** Junior AWS Dev/Ops engineers  
**Scope:** Initial deployment into an existing AWS test environment + CI/CD for ongoing changes.  
**Related:** Cookbook and verification checklist are in **`docs/DEPLOYMENT_COOKBOOK.md`**.

---

## 1. Deployment Type Recommendation: **Docker**

**Recommendation: use Docker (containerized) deployment.**

| Approach | Pros | Cons |
|----------|------|------|
| **Docker (recommended)** | Same image in dev/test/prod; easy CI/CD (build once, push to ECR, deploy to ECS/App Runner); no host drift; fits existing AWS container services. | Requires Docker/ECR/ECS or App Runner in the test account. |
| **Native (EC2 + Python/Node)** | No container runtime; direct install. | Different env per host; harder to replicate locally; more manual steps for updates. |

**Why Docker for test:**

- **Reproducibility:** The same image runs locally and in AWS test.
- **CI/CD:** Build image → push to Amazon ECR → deploy to ECS Fargate (or App Runner) in a few steps.
- **Consistency:** Python version, system libs, and app code are fixed in the image.
- **Existing test env:** If the test account already has ECR, ECS, and RDS, adding one more ECS service is straightforward.

**Architecture (recommended for test):**

- **One container** (backend + static frontend): Backend serves the built React app from `/static` and handles `/api` and `/auth`. Single ECS task, one ALB, minimal moving parts.
- **Database:** Use existing **RDS PostgreSQL** in the test VPC (do not run Postgres in the app container in test/prod).
- **Secrets:** Database URL and `SECRET_KEY` from **AWS Secrets Manager** or **SSM Parameter Store** (or env vars from ECS task definition).

Alternative: Frontend on **S3 + CloudFront**, backend on ECS. More setup; use if the team already standardizes on static hosting for SPAs.

---

## 2. High-Level Architecture (Test)

```
[User] → [ALB] → [ECS Fargate: Loan Engine container]
                        ↓
                  [RDS PostgreSQL]
                  (existing test DB or new instance)

Optional later: [S3] + [CloudFront] for frontend static assets.
```

- **ALB:** HTTPS (recommended); target group = ECS service; health check = `/health/ready`.
- **ECS:** Fargate task; 0.5 vCPU / 1 GB RAM minimum; scale 1–2 tasks for test.
- **RDS:** PostgreSQL 14+; security group allows ECS task SG on 5432.

---

## 3. What’s in This Repo for Deployment

| Asset | Purpose |
|-------|--------|
| `deploy/Dockerfile` | Multi-stage: build frontend, then backend + static files. |
| `deploy/docker-compose.yml` | Local/test run with Postgres (optional). |
| `deploy/aws/` | ECR repo creation, ECS task definition, task execution role, sample env. |
| `deploy/aws/ecs-task-definition.json` | ECS Fargate task definition (fill placeholders). |
| `deploy/aws/scripts/` | Scripts to create ECR repo, build/push, deploy (or update) ECS service. |
| `.github/workflows/deploy-test.yml` | CI/CD: build, push to ECR, deploy to ECS test. |
| `docs/DEPLOYMENT_COOKBOOK.md` | Step-by-step cookbook and verification checklist. |

---

## 4. CI/CD Flow (Summary)

1. **On push to `main` (or chosen branch):**  
   GitHub Actions builds the Docker image (frontend + backend), pushes to **Amazon ECR** in the test account, updates **ECS service** to use the new image.
2. **Secrets:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (or OIDC), `ECR_REPO_URI`, `ECS_CLUSTER`, `ECS_SERVICE`, `TASK_DEFINITION` (or full task def path) in GitHub Secrets.
3. **Database migrations:** Run Alembic migrations as part of the deploy (e.g. in a deploy script or a separate “migrate” step before updating the service). See cookbook.

---

## 5. Initial vs. Ongoing

- **Initial deployment:** Follow **`docs/DEPLOYMENT_COOKBOOK.md`** (create ECR, ECS cluster/service, ALB, RDS if needed, run migrations, deploy first image).
- **Ongoing changes:** Push to the configured branch → workflow builds and deploys to test; verify using the cookbook checklist.

---

## 6. Security and Compliance (Test)

- Use **IAM roles for ECS task execution** and **task role** (no long-lived keys in the image).
- Store **DATABASE_URL** and **SECRET_KEY** in Secrets Manager or SSM; inject via ECS task definition.
- Restrict **security groups**: ALB → ECS only; ECS → RDS only; no direct internet to RDS.
- Prefer **HTTPS** on the ALB (ACM certificate).

---

## 7. Next Steps

1. Read **`docs/DEPLOYMENT_COOKBOOK.md`** for the step-by-step and checklist.
2. Confirm test account has (or create): VPC, RDS PostgreSQL, ECS cluster, ALB, and IAM roles.
3. Run the **initial deployment** from the cookbook.
4. Configure the **GitHub Actions** workflow and secrets, then run a **CI/CD** deploy and verify.
