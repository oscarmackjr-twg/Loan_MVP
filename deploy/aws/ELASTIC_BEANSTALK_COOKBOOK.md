# Elastic Beanstalk Deployment Cookbook — Loan Engine

This cookbook describes how to deploy the **Loan Engine** (Loan Processing) application on **AWS Elastic Beanstalk** so you can run **multiple web apps** (e.g. dev, test, prod or multiple products) from the same account, each with its **own URL**.

---

## Why Elastic Beanstalk for Multiple Apps?

- **One EB Application** = one “product” (e.g. Loan Engine).
- **Multiple EB Environments** = multiple deployments, each with a **unique URL**:
  - `loan-engine-dev.us-east-1.elasticbeanstalk.com`
  - `loan-engine-test.us-east-1.elasticbeanstalk.com`
  - `loan-engine-prod.us-east-1.elasticbeanstalk.com`
- No URL reuse: each environment has its own CNAME and (optionally) its own RDS, secrets, and config.
- Same codebase and Docker image; only environment name and config differ.

---

## Prerequisites

- AWS CLI installed and configured (or IAM Identity Center profile).
- Docker installed (for building the image).
- (Optional) EB CLI: `pip install awsebcli` — helpful but not required; you can use the AWS Console and CLI only.
- For RDS: an existing PostgreSQL instance per environment, or create one per environment (recommended for isolation).

---

## Architecture Overview

```mermaid
flowchart LR
  subgraph eb [Elastic Beanstalk]
    app[EB Application]
    env1[Environment dev]
    env2[Environment test]
    env3[Environment prod]
  end
  app --> env1
  app --> env2
  app --> env3
  env1 --> url1["URL dev"]
  env2 --> url2["URL test"]
  env3 --> url3["URL prod"]
```

- **Application**: `loan-engine` (or `loan-processing`).
- **Environments**: e.g. `loan-engine-dev`, `loan-engine-test`, `loan-engine-prod`.
- **Platform**: Docker running on 64bit Amazon Linux 2023.
- **App**: Single container; use [deploy/aws/eb/Dockerfile](aws/eb/Dockerfile) (includes HEALTHCHECK for EB) or [deploy/Dockerfile](../Dockerfile); uvicorn on port 8000.

---

## Part 1: Prepare the Project for EB

### 1.1 Dockerrun.aws.json (single-container Docker)

Elastic Beanstalk uses this file to run your container. Create it at the **repository root** (or in a deploy subfolder and reference it during deploy).

**File: `deploy/aws/eb/Dockerrun.aws.json`**

```json
{
  "AWSEBDockerrunVersion": "1",
  "Image": {
    "Name": "<ECR_URI>:latest",
    "Update": "true"
  },
  "Ports": [
    {
      "ContainerPort": 8000,
      "HostPort": 8000
    }
  ],
  "Logging": "/var/log/nginx"
}
```

Replace `<ECR_URI>` with your ECR image URI (e.g. `123456789012.dkr.ecr.us-east-1.amazonaws.com/loan-engine`). You will build and push this image the same way as today (see Part 2).

### 1.2 Environment Variables and Secrets

The app reads **DATABASE_URL**, **SECRET_KEY**, and optional **CORS_ORIGINS** from the environment. Options:

- **Option A (recommended):** Set environment variables in the EB **Environment configuration** (Console or CLI). For secrets, reference **AWS Secrets Manager** or **SSM Parameter Store** in `.platform/hooks` or use **Option B**.
- **Option B:** Use **.ebextensions** to fetch secrets at deploy time and export them (e.g. via `commands` that call AWS CLI and write env files). More moving parts; Option A is simpler.

Example **Option A** — set in EB Console → Configuration → Software → Environment properties:

| Name           | Value (or use “secret” reference if your EB supports it) |
|----------------|----------------------------------------------------------|
| DATABASE_URL   | `postgresql://user:pass@rds-endpoint:5432/loan_engine?sslmode=require` |
| SECRET_KEY     | (strong random string)                                   |
| CORS_ORIGINS   | `["https://loan-engine-dev.elasticbeanstalk.com","https://your-custom-domain.com"]` |
| STORAGE_TYPE   | `local` or `s3`                                          |

If you use **Secrets Manager**, create secrets per environment (e.g. `loan-engine/dev/DATABASE_URL`) and either inject them via `.platform/confighooks` or use IAM role + app code that calls Secrets Manager (current app expects env vars, so the simplest is to set them in EB config and keep secrets in a password manager or CI until then).

### 1.3 CORS

Set **CORS_ORIGINS** for each environment to that environment’s URL (and any custom domain). The app reads this from [config/settings.py](../../backend/config/settings.py).

---

## Part 2: Build and Push Docker Image (per environment or shared)

### 2.1 Create ECR repository (one-time per account/region)

Create the repository before the first build/push. Use the same name as in `Dockerrun.aws.json` (e.g. `loan-engine`).

```powershell
$Region = "us-east-1"
aws ecr create-repository `
  --repository-name loan-engine `
  --region $Region `
  --image-scanning-configuration scanOnPush=true
```

If the repository already exists, you'll get an error; that's fine. To verify: `aws ecr describe-repositories --repository-names loan-engine --region $Region`.

### 2.2 Build and push image

Use the EB Dockerfile (recommended) or the main Dockerfile. You can use one image (e.g. `latest`) for all environments or tag by environment (e.g. `dev`, `test`, `prod`).

From repo root:

```powershell
# Set these (run in the same PowerShell session as the commands below)
$Region = "us-east-1"
$AccountId = aws sts get-caller-identity --query Account --output text
$ECRUri = "$AccountId.dkr.ecr.$Region.amazonaws.com/loan-engine"
$Tag = "${ECRUri}:latest"

# Build from repo root (the trailing . is the build context and must be last)
docker build -f deploy/aws/eb/Dockerfile --tag $Tag .

# Login and push
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $ECRUri
docker push $Tag
```

If you use a **named profile** (e.g. IAM Identity Center), add `--profile YourProfile` to the `aws` commands.

---

## Part 3: Create the EB Application and Environments

### 3.1 Create the Application (once per “product”)

**Console:** Elastic Beanstalk → Create application → Application name: `loan-engine` (or `loan-processing`).

**CLI:**

```powershell
aws elasticbeanstalk create-application `
  --application-name loan-engine `
  --description "Loan Processing Application" `
  --region us-east-1
```

### 3.2 Create an Environment (repeat per URL: dev, test, prod)

Each environment gets its **own URL**. Use **Docker platform** and **single instance** or **load balanced**, depending on need.

**Example: create `loan-engine-dev` (single instance, Docker)**

- **Console:**  
  Elastic Beanstalk → Applications → loan-engine → Create environment → Web server environment → Docker → Single instance (or Load balanced) → Configure more options → set VPC, subnets, security groups, instance profile so the app can reach RDS and Secrets Manager if needed.

**CLI (minimal):** You must specify platform, solution stack name, and optionally a version label. Example for Docker on AL2023:

```powershell
# Create app version (tarball with Dockerrun) — see 3.3
# Then create environment linked to that version

aws elasticbeanstalk create-environment `
  --application-name loan-engine `
  --environment-name loan-engine-dev `
  --solution-stack-name "64bit Amazon Linux 2023 v4.3.0 running Docker" `
  --option-settings "
    Namespace=aws:elasticbeanstalk:application:environment,OptionName=ENVIRONMENT_VARIABLES,Value=[{\"Namespace\":\"aws:elasticbeanstalk:application:environment\",\"OptionName\":\"DATABASE_URL\",\"Value\":\"postgresql://...\"},{\"Namespace\":\"aws:elasticbeanstalk:application:environment\",\"OptionName\":\"SECRET_KEY\",\"Value\":\"your-secret\"}]
  " `
  --region us-east-1
```

Option settings are easier to manage in the Console or via a saved configuration. For a **cookbook**, prefer doing the first environment in the Console, then use “Save configuration” and reuse.

### 3.3 Deploy with a Dockerrun + image in ECR

- Build and push the image (Part 2).
- **Dockerrun.aws.json** must reference the same ECR URI and tag you pushed.
- Create an **application version** that points to a **source bundle** containing only `Dockerrun.aws.json` (and any .ebextensions). EB will pull the image from ECR when it runs the container.

**Create source bundle (example for Windows):**

```powershell
# From repo root; ensure deploy/aws/eb/Dockerrun.aws.json exists and Image.Name is set to your ECR URI
Compress-Archive -Path deploy\aws\eb\Dockerrun.aws.json -DestinationPath deploy\aws\eb\app.zip -Force
```

**Get or create the S3 bucket:** Elastic Beanstalk needs a bucket in your account for application versions. Use one of these:

- **Option A — Use EB’s default bucket** (if you’ve already used EB in this region, it was created for you):
  ```powershell
  # List buckets; look for one like elasticbeanstalk-us-east-1-<account-id>
  aws s3 ls --region us-east-1
  # Then set (replace with the actual bucket name from the list):
  $bucket = "elasticbeanstalk-us-east-1-123456789012"
  ```
- **Option B — Create a new bucket** (use your AWS account ID in the name, or any unique name):
  ```powershell
  $accountId = (aws sts get-caller-identity --query Account --output text)
  $bucket = "elasticbeanstalk-us-east-1-$accountId"
  aws s3 mb "s3://$bucket" --region us-east-1
  ```

Upload `app.zip` to S3, then create the application version and deploy:

```powershell
# If you didn't set $bucket above, set it now (use a real bucket name from "aws s3 ls")
$bucket = "elasticbeanstalk-us-east-1-123456789012"   # Replace with your bucket name
$key = "loan-engine/loan-engine-dev-1.0.0.zip"
aws s3 cp deploy/aws/eb/app.zip "s3://$bucket/$key" --region us-east-1

aws elasticbeanstalk create-application-version `
  --application-name loan-engine `
  --version-label "1.0.0" `
  --source-bundle S3Bucket=$bucket,S3Key=$key `
  --region us-east-1

aws elasticbeanstalk update-environment `
  --environment-name loan-engine-dev `
  --version-label "1.0.0" `
  --region us-east-1
```

After the environment update finishes, the **environment URL** (e.g. `loan-engine-dev.us-east-1.elasticbeanstalk.com`) is your app’s base URL. Use it for CORS and for running [create-app-user.ps1](create-app-user.ps1).

---

## Part 4: Multiple Environments = Multiple URLs

| Environment name   | Typical URL (EB default)                    | Use case   |
|--------------------|---------------------------------------------|------------|
| loan-engine-dev    | `loan-engine-dev.us-east-1.elasticbeanstalk.com` | Development |
| loan-engine-test   | `loan-engine-test.us-east-1.elasticbeanstalk.com` | Test / UAT  |
| loan-engine-prod   | `loan-engine-prod.us-east-1.elasticbeanstalk.com` | Production  |

- Create one **environment** per desired URL.
- Each environment has its own **configuration** (env vars, RDS endpoint, SECRET_KEY). Use different RDS instances or DB names per environment for isolation.
- Deploy the **same** application version to multiple environments, or use different version labels per environment (e.g. `dev-1.0.0`, `prod-1.0.0`).

---

## Part 5: RDS and Database

- **Option A:** One RDS instance per environment (recommended). Create e.g. `loan-engine-dev-db`, `loan-engine-test-db`, `loan-engine-prod-db` (or use existing RDS). Set **DATABASE_URL** per environment in EB config.
- **Option B:** Shared RDS with different **database names** per environment (e.g. `loan_engine_dev`, `loan_engine_test`). Set **DATABASE_URL** per environment accordingly.
- Ensure the EB **instance profile** (and security group) can reach RDS (same VPC or peering; security group allows 5432 from EB instances).
- Run **migrations / init** per environment (e.g. run `init_db.py` and `seed_admin.py` once per environment — via one-off task, EB deploy hook, or manual run against that environment’s DB).

---

## Part 6: Checklist for a New Environment

1. [ ] ECR repository exists; image built and pushed for the app.
2. [ ] EB Application created (e.g. `loan-engine`).
3. [ ] EB Environment created (e.g. `loan-engine-dev`) with **unique** environment name.
4. [ ] Platform: Docker (Amazon Linux 2023).
5. [ ] `Dockerrun.aws.json` uses correct ECR image URI and tag.
6. [ ] Environment variables set (DATABASE_URL, SECRET_KEY, CORS_ORIGINS for that environment’s URL).
7. [ ] RDS (or DB) and schema exist for this environment; init/seed run if needed.
8. [ ] Application version created and deployed to the environment.
9. [ ] Health: open `https://<env-url>/health` (or HTTP if no HTTPS).
10. [ ] Create users via [create-app-user.ps1](create-app-user.ps1) with `-BaseUrl "https://<env-url>"`.

---

## Part 7: Custom Domains (Optional)

- Use **Route 53** (or another DNS) to point a friendly name (e.g. `loan-engine-dev.yourcompany.com`) to the EB environment CNAME.
- In EB, add the custom domain in the environment’s configuration if the platform supports it, or use an ALB in front and point DNS to the ALB.
- Update **CORS_ORIGINS** for that environment to include the custom domain.

---

## Part 8: Coexistence with ECS

- You can run **both** ECS (current deploy) and Elastic Beanstalk in the same account:
  - ECS: e.g. existing `loan-engine-test` ALB/URL.
  - EB: e.g. `loan-engine-dev`, `loan-engine-prod` with their own URLs.
- Use different **environment names** and **RDS instances** (or DB names) so each deployment is isolated. No conflict as long as URLs and resources (e.g. RDS, secrets) are distinct per deployment.

---

## Troubleshooting

**`docker buildx build requires 1 argument`** — Usually means the build context (`.`) was lost. Do all of the following: (1) Run from the **repo root** (directory that contains `frontend/` and `backend/`). (2) Set `$Tag` in the same session before building (see 2.2). (3) Use a space before the final `.`: `docker build -f deploy/aws/eb/Dockerfile --tag $Tag .` If `$Tag` is empty, the `.` can be misinterpreted as the tag value.

---

## Summary

- **One EB Application** = Loan Engine (one product).
- **Multiple EB Environments** = multiple deployments, each with a **dedicated URL**.
- Use the **existing Dockerfile** and ECR image; configure **Dockerrun.aws.json** and env vars per environment.
- Set **DATABASE_URL**, **SECRET_KEY**, and **CORS_ORIGINS** per environment so each app points to the right DB and allows its own origin.
- Use [create-app-user.ps1](create-app-user.ps1) with each environment’s URL to create users in that deployment.

This gives you multiple Loan Engine web apps from the same account, each with its own URL and configuration.
