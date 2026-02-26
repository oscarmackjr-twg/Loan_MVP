# Loan Engine – QA deployment (Terraform)

This directory provisions the **QA** environment on AWS using Terraform. It is separate from the **development** deployment (PowerShell scripts in `deploy/aws/`).

## QA resources

| Resource | Name / value |
|----------|----------------|
| **S3** | `loan-engine-qa` |
| **RDS** | Instance identifier `loan-engine-qa`, database `loan_engine` |
| **ECS cluster / service** | `loan-engine-qa` (Fargate) |
| **ECR** | `loan-engine-qa` (QA Docker images) |
| **Secrets Manager** | `loan-engine/qa/DATABASE_URL`, `loan-engine/qa/SECRET_KEY` |

## EC2 key pair (optional)

QA runs the app on **ECS Fargate** (no EC2 instances). If you have **`loan-engine-qa.pem`** in the project root (e.g. for a bastion or future EC2), it is **ignored by git** (`.gitignore` includes `*.pem`). To register the key in AWS so you can use it for EC2 instances (e.g. a bastion to reach RDS), pass the **public** key when applying:

```bash
# Get the public key from your .pem (run from repo root)
ssh-keygen -y -f loan-engine-qa.pem
```

Then set `TF_VAR_ec2_key_pair_public_key` to that one-line output (or add `ec2_key_pair_public_key = "..."` to `terraform.tfvars`). Terraform will create an EC2 key pair named **loan-engine-qa** in the region. You can then use `loan-engine-qa.pem` to SSH into any EC2 launched with that key.

## Prerequisites

- [Terraform](https://www.terraform.io/downloads) >= 1.0
- AWS CLI configured (e.g. `aws configure` or `aws sso login --profile YourProfile`)
- Docker (for building and pushing the QA image)

## 1. Set the database password

QA uses a fixed database password. Set it so Terraform can use it without putting it in a committed file:

**PowerShell:**

```powershell
$env:TF_VAR_db_password = 'Intrepid456$%'
```

**Bash:**

```bash
export TF_VAR_db_password='Intrepid456$%'
```

Alternatively, create a `terraform.tfvars` file (do **not** commit it) and set `db_password = "Intrepid456$%"`. Copy from `terraform.tfvars.example`.

## 2. Deploy infrastructure

From this directory (`deploy/terraform/qa/`):

```bash
terraform init
terraform plan    # optional: review changes
terraform apply
```

Apply may take **about 10 minutes** (RDS creation). When it finishes, note the `application_url` output.

## 3. Build and push the Docker image to QA ECR

After the first apply, push the app image to the QA ECR repository so ECS can run it:

**PowerShell (from repo root):**

```powershell
$region   = "us-east-1"
$repoUrl  = (terraform -chdir=deploy/terraform/qa output -raw ecr_repository_url)
$repoHost = $repoUrl.Split("/")[0]
aws ecr get-login-password --region $region | docker login --username AWS --password-stdin $repoHost
docker build -f deploy/Dockerfile -t $repoUrl`:latest .
docker push $repoUrl`:latest
```

**Or use the helper script (from repo root):**

```powershell
.\deploy\terraform\qa\deploy-qa.ps1 -PushImage
```

## 4. (Optional) Force ECS to pull the new image

If you pushed a new image and the service is already running:

```powershell
aws ecs update-service --cluster loan-engine-qa --service loan-engine-qa --force-new-deployment --region us-east-1
```

## 5. Initialize the database (migrations + seed)

After the first deploy, run migrations and seed the admin user. From the repo root you can use the existing init script against QA RDS (ensure network access: same VPC or RDS publicly accessible and your IP allowed).

Example (adjust profile and region as needed):

```powershell
# Set DATABASE_URL for QA (get endpoint from Terraform output)
$endpoint = terraform -chdir=deploy/terraform/qa output -raw rds_endpoint 2>$null
$env:DATABASE_URL = "postgresql://postgres:Intrepid456%25%25@${endpoint}:5432/loan_engine?sslmode=require"
# Then run migrations / seed (e.g. from backend or via ECS task)
```

Or use `deploy/aws/init-database.ps1` with the QA database endpoint and password if you adapt it for QA.

## Outputs

After `terraform apply`:

- **application_url** – QA app URL (e.g. `http://loan-engine-qa-alb-xxxx.us-east-1.elb.amazonaws.com`)
- **ecr_repository_url** – Use this to tag and push your Docker image
- **rds_endpoint** – RDS hostname for running migrations or debugging

## Destroying QA

To tear down the QA environment:

```bash
terraform destroy
```

You will be prompted to confirm. RDS may have a final snapshot option; this config uses `skip_final_snapshot = true` for simplicity.
