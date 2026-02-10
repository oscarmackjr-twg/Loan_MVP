# Redeploy Loan Engine to AWS (including Docker)

Use these steps when you’ve changed code and want to rebuild the image, push to ECR, and roll out to ECS.

## Prerequisites

- **Docker Desktop** running (so `docker build` and `docker push` work).
- **AWS CLI** installed and configured (e.g. profile `AWSAdministratorAccess-014148916722`).
- You’re in the **repo root** for all commands below.

---

## Option A: One-command redeploy (recommended)

From the repository root, run the full deploy script **without** `-SkipBuild`. It will reuse existing AWS resources, rebuild the Docker image, push to ECR, and force a new ECS deployment.

```powershell
cd c:\Users\omack\Intrepid\pythonFramework\cursor_loan_engine

.\deploy\aws\deploy-aws.ps1 -Region us-east-1 -Profile AWSAdministratorAccess-014148916722
```

- Omit `-Profile ...` if you use the default AWS profile.
- Same region/app/environment as your first deploy (defaults: `us-east-1`, `loan-engine`, `test`).

The script will:

1. Ensure ECR repo exists.
2. Log Docker into ECR.
3. Build the image: `docker build -f deploy/Dockerfile -t <ecr-uri>:latest .`
4. Push: `docker push <ecr-uri>:latest`
5. Register the ECS task definition (unchanged) and update the ECS service with `--force-new-deployment`.

Wait 2–5 minutes for the new task to become healthy, then open your ALB URL (shown at the end of the script).

---

## Option B: Manual Docker build, push, and ECS update

Use this when you only want to rebuild the image and roll out, without running the rest of the deploy script.

### 1. Set variables (match your existing deploy)

```powershell
$Region   = "us-east-1"
$AppName  = "loan-engine"
$Profile  = "AWSAdministratorAccess-014148916722"   # or omit if using default profile
```

### 2. Get AWS account ID and ECR URI

```powershell
# Add --profile $Profile to aws if you use a named profile
$accountId = aws sts get-caller-identity --query Account --output text
$ECRRepoUri = "${accountId}.dkr.ecr.${Region}.amazonaws.com/${AppName}"
```

### 3. Open repo root and build the image

```powershell
cd c:\Users\omack\Intrepid\pythonFramework\cursor_loan_engine

docker build -f deploy/Dockerfile -t "${ECRRepoUri}:latest" .
```

### 4. Log Docker into ECR

```powershell
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $ECRRepoUri
```

If you use a profile:

```powershell
aws ecr get-login-password --region $Region --profile $Profile | docker login --username AWS --password-stdin $ECRRepoUri
```

### 5. Push the image

```powershell
docker push "${ECRRepoUri}:latest"
```

### 6. Force a new ECS deployment

```powershell
$ClusterName = "${AppName}-cluster"
$ServiceName = "${AppName}-${Environment}-service"
$Environment = "test"

aws ecs update-service `
  --cluster $ClusterName `
  --service $ServiceName `
  --force-new-deployment `
  --region $Region
```

If you use a profile, add `--profile $Profile` to the `aws ecs update-service` command.

### 7. Wait and check

- Wait 2–5 minutes for the new task to pass health checks.
- Open your ALB URL (e.g. `http://<alb-dns-name>`) and confirm the app (and the new login status message) loads.

---

## Summary

| Goal                         | Command / steps |
|-----------------------------|------------------|
| Full redeploy (Docker + ECS) | Run `.\deploy\aws\deploy-aws.ps1 -Region us-east-1 -Profile ...` (no `-SkipBuild`). |
| Only rebuild and roll out   | Build → ECR login → push → `aws ecs update-service ... --force-new-deployment`. |

After redeploy, the frontend (including the “Backend connected” / “Backend unreachable” message on the login page) is served from the new image.
