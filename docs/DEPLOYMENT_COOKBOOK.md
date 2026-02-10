# Deployment Cookbook & Verification Checklist

**Audience:** Junior AWS Dev/Ops engineers  
**Use with:** `docs/AWS_DEPLOYMENT_PLAN.md` (architecture and recommendation).

This cookbook covers: (1) initial deployment to AWS test, and (2) CI/CD workflow setup, with a **verification checklist** at the end.

---

## Prerequisites

- [ ] AWS CLI installed and configured (or CI identity with ECR + ECS permissions)
- [ ] Docker installed (for local build and optional compose)
- [ ] Access to the existing AWS test account/VPC
- [ ] RDS PostgreSQL instance in test (or plan to create one)
- [ ] ECS cluster in test (or plan to create one)
- [ ] ALB + target group for the service (or plan to create)

---

## Part A: Initial Deployment

### A.1 Create ECR repository (one-time)

```bash
cd /path/to/cursor_loan_engine
chmod +x deploy/aws/scripts/*.sh
./deploy/aws/scripts/create-ecr-repo.sh loan-engine us-east-1
```

**Verify:** `aws ecr describe-repositories --repository-names loan-engine --region us-east-1` returns the repo.

---

### A.2 Prepare secrets (RDS URL, SECRET_KEY)

Store in **AWS Secrets Manager** (recommended) or SSM Parameter Store:

- `DATABASE_URL`: e.g. `postgresql://user:pass@your-rds-endpoint:5432/loan_engine`
- `SECRET_KEY`: strong random string for JWT signing

Example (Secrets Manager, one secret per key or one JSON secret):

```bash
aws secretsmanager create-secret --name loan-engine/test/DATABASE_URL --secret-string "postgresql://..."
aws secretsmanager create-secret --name loan-engine/test/SECRET_KEY --secret-string "your-secret-key"
```

**Verify:** Secrets exist and ECS task execution role has `secretsmanager:GetSecretValue` on these ARNs.

---

### A.3 Create ECS task definition

1. Copy `deploy/aws/ecs-task-definition.json` and replace placeholders:
   - `YOUR_ACCOUNT_ID` → AWS account ID
   - `YOUR_REGION` → e.g. `us-east-1`
   - `YOUR_ALB_DNS` → ALB hostname (for CORS)
   - Secret ARNs → actual ARNs from A.2
   - Image → ECR URI after first push (e.g. `123456789012.dkr.ecr.us-east-1.amazonaws.com/loan-engine:latest`)
2. Create log group: `aws logs create-log-group --log-group-name /ecs/loan-engine-test`
3. Register task definition:

```bash
aws ecs register-task-definition --cli-input-json file://deploy/aws/ecs-task-definition.json --region us-east-1
```

**Verify:** `aws ecs describe-task-definition --task-definition loan-engine-test` shows the task definition.

---

### A.4 Build and push image (first time)

From repo root:

```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=us-east-1
./deploy/aws/scripts/build-and-push.sh us-east-1 latest
```

**Verify:** `aws ecr describe-images --repository-name loan-engine --region us-east-1` lists the new image.

---

### A.5 Create ECS service (one-time)

If the cluster and ALB already exist:

```bash
aws ecs create-service \
  --cluster test-cluster \
  --service-name loan-engine-test \
  --task-definition loan-engine-test \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=app,containerPort=8000" \
  --region us-east-1
```

Replace `subnet-xxx`, `sg-xxx`, and `targetGroupArn` with your test VPC values. Ensure ALB listener forwards to this target group (e.g. path `/` or `/*`).

**Verify:** Service is running: `aws ecs describe-services --cluster test-cluster --services loan-engine-test` shows `runningCount: 1`.

---

### A.6 Database migrations (one-time and after schema changes)

Run Alembic against the **test RDS** database:

```bash
cd backend
export DATABASE_URL="postgresql://user:pass@rds-endpoint:5432/loan_engine"
alembic upgrade head
```

Or run a one-off ECS task that executes migrations, or add a migration step to your deploy script.

**Verify:** Connect to RDS and confirm tables exist: `\dt` in `psql`.

---

### A.7 Seed admin user (one-time)

From a machine that can reach RDS (or run as ECS one-off task):

```bash
cd backend
export DATABASE_URL="postgresql://..."
python scripts/seed_admin.py
```

**Verify:** Login at `https://YOUR_ALB_DNS/login` with the seeded credentials.

---

## Part B: CI/CD (GitHub Actions)

### B.1 GitHub repository variables and secrets

In the repo: **Settings → Secrets and variables → Actions.**

**Secrets (required for deploy):**

| Secret               | Description                    |
|----------------------|--------------------------------|
| `AWS_ACCESS_KEY_ID`  | IAM user/role access key      |
| `AWS_SECRET_ACCESS_KEY` | IAM secret key            |

**Variables (optional; can hardcode in workflow):**

| Variable       | Example          | Description        |
|----------------|------------------|--------------------|
| `AWS_REGION`   | `us-east-1`      | AWS region         |
| `ECS_CLUSTER`  | `test-cluster`   | ECS cluster name   |
| `ECS_SERVICE`  | `loan-engine-test` | ECS service name |

**Verify:** Workflow file uses `vars.AWS_REGION`, `vars.ECS_CLUSTER`, etc., or defaults.

---

### B.2 Trigger deployment

- Push to `main` (or the branch configured in `on.push.branches`).
- Or run **Actions → Deploy to AWS Test → Run workflow**.

**Verify:** Actions tab shows a successful run; ECS service has a new deployment with the new task revision.

---

## Part C: Verification Checklist

Use this after **initial deploy** and after **any CI/CD deploy**.

### Build & image

- [ ] `docker build -f deploy/Dockerfile .` succeeds from repo root.
- [ ] Image runs locally with `docker run -e DATABASE_URL=... -p 8000:8000 <image>`; `curl http://localhost:8000/health/ready` returns 200.

### ECR

- [ ] ECR repo `loan-engine` exists in the test account/region.
- [ ] New image is present after build-and-push (tag `latest` and/or git SHA).

### ECS

- [ ] Task definition `loan-engine-test` is registered and references the correct image and secret ARNs.
- [ ] Service `loan-engine-test` has desired count ≥ 1 and running count matches.
- [ ] Latest task is in RUNNING state; no repeated STOPPED tasks (check Events for errors).

### Application

- [ ] ALB DNS resolves; HTTPS (or HTTP for test) returns the app or API response.
- [ ] `GET https://YOUR_ALB/health` returns `{"status":"healthy"}`.
- [ ] `GET https://YOUR_ALB/health/ready` returns `{"status":"ready","database":"connected"}`.
- [ ] `GET https://YOUR_ALB/docs` returns Swagger UI (or 200).
- [ ] Login page loads at `https://YOUR_ALB/login`; login with seeded admin succeeds.
- [ ] Dashboard loads; can open Runs, Exceptions, Rejected Loans.

### Security & config

- [ ] No secrets in task definition environment (only in `secrets` or SSM).
- [ ] CORS allows the ALB/origin you use; no browser CORS errors when using the UI.
- [ ] RDS is not publicly accessible; only ECS tasks (and optional bastion) can reach it.

### CI/CD

- [ ] Push to `main` triggers the workflow (or manual run succeeds).
- [ ] Workflow completes: build → push to ECR → ECS update-service.
- [ ] After workflow, ECS service shows a new deployment and new tasks with the new image.

---

## Optional: Local Docker Compose

From repo root:

```bash
docker compose -f deploy/docker-compose.yml up -d
# Run migrations and seed (see backend scripts)
curl http://localhost:8000/health/ready
```

**Verify:** Same as “Application” above, using `http://localhost:8000`.

---

## Troubleshooting

| Issue | Check |
|-------|--------|
| Task fails to start | ECS Events; task logs in CloudWatch `/ecs/loan-engine-test`; task execution role has ECR pull + Secrets Manager. |
| 503 at ALB | Target group health check (path `/health/ready`); security group allows ALB → task on 8000. |
| DB connection failed | DATABASE_URL in secrets; RDS security group allows ECS task SG on 5432; subnet routing. |
| CORS errors in browser | CORS_ORIGINS in task def includes the frontend origin (e.g. ALB URL). |

---

## Document control

| Version | Date  | Notes        |
|---------|-------|--------------|
| 0.1     | Draft | Initial cookbook and checklist |
