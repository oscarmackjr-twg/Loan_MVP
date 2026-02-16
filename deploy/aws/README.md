# AWS Deployment Scripts

This directory contains scripts to deploy the Loan Engine application to AWS from scratch.

**Multiple web apps from the same account:** To run several Loan Engine deployments (e.g. dev, test, prod) each with its **own URL**, use [Elastic Beanstalk](ELASTIC_BEANSTALK_COOKBOOK.md). The [EB cookbook](ELASTIC_BEANSTALK_COOKBOOK.md) covers one EB Application, multiple EB Environments, and reusing the same Docker image.

## Prerequisites

1. **AWS CLI installed and configured**
   ```powershell
   # Install AWS CLI (if not installed)
   # Download from: https://aws.amazon.com/cli/
   
   # Configure credentials
   aws configure
   # Enter: Access Key ID, Secret Access Key, Region, Output format
   ```

2. **Docker Desktop running** (for building and pushing images)

3. **PowerShell 5.1+** (Windows PowerShell or PowerShell Core)

4. **AWS Permissions**: Your AWS credentials need permissions to create:
   - VPC, Subnets, Security Groups, Internet Gateways
   - RDS instances
   - ECR repositories
   - ECS clusters, services, task definitions
   - Application Load Balancers
   - IAM roles and policies
   - Secrets Manager secrets
   - CloudWatch Log Groups

## Quick Start

### Initial Deployment

Run the deployment script from the repository root:

```powershell
cd c:\Users\omack\Intrepid\pythonFramework\cursor_loan_engine
.\deploy\aws\deploy-aws.ps1 -Region us-east-1
```

This will create all AWS resources from scratch:
- VPC with public/private subnets
- Security groups (ALB, ECS, RDS)
- RDS PostgreSQL database
- ECR repository
- ECS Fargate cluster and service
- Application Load Balancer
- IAM roles
- Secrets Manager secrets
- CloudWatch log group

### Customization

```powershell
# Specify custom region and app name
.\deploy\aws\deploy-aws.ps1 -Region us-west-2 -AppName my-loan-engine

# Skip Docker build (if image already exists in ECR)
.\deploy\aws\deploy-aws.ps1 -SkipBuild

# Provide custom database password and secret key
.\deploy\aws\deploy-aws.ps1 -DBPassword "MySecurePassword123!" -SecretKey "MySecretKey123!"
```

## Script Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `-Region` | `us-east-1` | AWS region to deploy to |
| `-AppName` | `loan-engine` | Application name (used for resource naming) |
| `-Environment` | `test` | Environment name (test/prod) |
| `-DBUsername` | `postgres` | RDS master username |
| `-DBPassword` | *(auto-generated)* | RDS master password (auto-generated if not provided) |
| `-SecretKey` | *(auto-generated)* | JWT secret key (auto-generated if not provided) |
| `-SkipBuild` | `$false` | Skip Docker build and push |
| `-S3BucketName` | *(none)* | If set, app uses S3 for inputs, outputs, and archive (file upload, pipeline, and run archives all use this bucket) |
| `-S3BasePrefix` | *(none)* | Optional key prefix for S3 paths (e.g. `loan-engine/test`) |
| `-Profile` | *(none)* | AWS CLI profile (e.g. for IAM Identity Center) |

**Using S3:** When you pass `-S3BucketName MyBucket`, the app expects that bucket to **already exist** in the same region. Create it first, e.g. `aws s3 mb s3://MyBucket --region us-east-1`. All file uploads, pipeline inputs/outputs, and run archives go to that bucket (under the prefixes implied by `S3_BASE_PREFIX` and area: inputs, outputs, archive).

## What Gets Created

### Networking
- **VPC**: `10.0.0.0/16` CIDR block
- **Public Subnets**: `10.0.1.0/24`, `10.0.2.0/24` (across 2 AZs)
- **Private Subnets**: `10.0.11.0/24`, `10.0.12.0/24` (across 2 AZs)
- **Internet Gateway**: For public subnet internet access
- **Route Tables**: Public subnets route to IGW

### Security Groups
- **ALB SG**: Allows HTTP (80) and HTTPS (443) from internet
- **ECS SG**: Allows port 8000 from ALB SG only
- **RDS SG**: Allows PostgreSQL (5432) from ECS SG only

### Database
- **RDS PostgreSQL 15.4**: `db.t3.micro` instance (free tier eligible)
- **Database Name**: `loan_engine`
- **Credentials**: Stored in Secrets Manager

### Container Infrastructure
- **ECR Repository**: `loan-engine` (or custom app name)
- **ECS Cluster**: `loan-engine-test` (Fargate)
- **ECS Service**: Runs 1 task initially
- **Task Definition**: 512 CPU, 1024 MB memory

### Load Balancing
- **Application Load Balancer**: Internet-facing, HTTP on port 80
- **Target Group**: Health check on `/health/ready`
- **Listener**: Routes HTTP traffic to target group

### IAM Roles
- **Task Execution Role**: Allows ECS to pull images, write logs, access secrets
- **Task Role**: Allows app to read Secrets Manager secrets

### Secrets Manager
- `loan-engine/test/DATABASE_URL`: PostgreSQL connection string
- `loan-engine/test/SECRET_KEY`: JWT signing key

### CloudWatch
- **Log Group**: `/ecs/loan-engine-test`

## Post-Deployment Steps

### 1. Wait for Service to be Healthy

```powershell
# Check service status
aws ecs describe-services --cluster loan-engine-test --services loan-engine-test --region us-east-1

# Check task status
aws ecs list-tasks --cluster loan-engine-test --service-name loan-engine-test --region us-east-1
```

### 2. Migrate local database schema to AWS (initialize RDS)

You need to create the same tables on AWS RDS that you have locally. Two ways:

#### Option A: Use the init-database script (easiest)

The script reads `DATABASE_URL` from AWS Secrets Manager and runs `init_db.py` + `seed_admin.py` locally against RDS:

```powershell
# From repo root. Requires: Python, backend deps (pip install -r backend/requirements.txt), and network access to RDS.
.\deploy\aws\init-database.ps1 -Region us-east-1

# With IAM Identity Center profile:
.\deploy\aws\init-database.ps1 -Region us-east-1 -Profile AWSAdministratorAccess-014148916722
```

Your machine must reach RDS on port 5432. The RDS security group only allows ECS by default. If you get **Connection timed out**, run `.\deploy\aws\allow-my-ip-rds.ps1 -Region us-east-1 -Profile YourProfile` once, then run init-database again. This creates all tables from the app’s SQLAlchemy models and seeds the admin user.

#### Option B: Manual (set DATABASE_URL and run scripts)

```powershell
# 1. Get the connection string from Secrets Manager
$dbSecret = aws secretsmanager get-secret-value --secret-id loan-engine/test/DATABASE_URL --region us-east-1 --query SecretString --output text
# If using a profile: add --profile YourProfile to the aws command

# 2. Run schema creation and seed from backend
cd backend
$env:DATABASE_URL = $dbSecret
python scripts/init_db.py
python scripts/seed_admin.py
```

#### Using Alembic instead of init_db.py

If you use Alembic migrations in this project:

```powershell
cd backend
$env:DATABASE_URL = $dbSecret   # (from Secrets Manager as above)
alembic upgrade head
python scripts/seed_admin.py
```

#### Option C: Run migrations via ECS Exec (no direct RDS access)

If you can’t reach RDS from your machine, run inside a running ECS task (requires SSM Session Manager):

```powershell
$taskId = (aws ecs list-tasks --cluster loan-engine-test --service-name loan-engine-test --query "taskArns[0]" --output text --region us-east-1).Split("/")[-1]
aws ecs execute-command --cluster loan-engine-test --task $taskId --container app --command "python scripts/init_db.py" --interactive --region us-east-1
# Then: python scripts/seed_admin.py in the same way
```

### 3. Create Admin User (run seed_admin in AWS)

**Recommended: one-off ECS task (no Session Manager plugin, no direct RDS access from your PC)**

```powershell
# Full init: create tables + admin user (run inside AWS, same VPC as RDS)
.\deploy\aws\init-database.ps1 -Region us-east-1 -Method ecs-task -Profile AWSAdministratorAccess-014148916722

# Only seed admin (tables already exist; create or update admin user)
.\deploy\aws\init-database.ps1 -Region us-east-1 -Method ecs-task -SeedOnly -Profile AWSAdministratorAccess-014148916722
```

Omit `-Profile ...` if you use the default AWS profile. The task runs in the same VPC as RDS and uses `DATABASE_URL` from Secrets Manager.

**Other options**

```powershell
# From local machine (requires DB access)
cd backend
$env:DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@$dbEndpoint:5432/loan_engine"
python scripts/seed_admin.py

# Via ECS Exec (requires Session Manager plugin and a running task)
aws ecs execute-command --cluster loan-engine-test --task $taskId --container app --command "python scripts/seed_admin.py" --interactive --region us-east-1
```

### 4. Access the Application

Once healthy, access the app at:
```
http://<ALB_DNS_NAME>
```

Default admin credentials (change after first login):
- Username: `admin`
- Password: `admin123`

### Create application users

Use `create-app-user.ps1` to add users via the admin API (no direct DB access needed). Run from repo root; replace `<ALB_URL>` with your app URL (e.g. `http://loan-engine-test-xxxxx.us-east-1.elb.amazonaws.com`).

**List sales teams** (to get IDs for `sales_team` users):

```powershell
.\deploy\aws\create-app-user.ps1 `
  -BaseUrl "http://<ALB_URL>" `
  -AdminUsername "admin" `
  -AdminPassword "admin123" `
  -ListSalesTeams
```

**Create analyst or admin user:**

```powershell
.\deploy\aws\create-app-user.ps1 `
  -BaseUrl "http://<ALB_URL>" `
  -AdminUsername "admin" `
  -AdminPassword "admin123" `
  -Username "jdoe" `
  -Email "jdoe@company.com" `
  -Password "TempPass!123" `
  -FullName "Jane Doe" `
  -Role analyst
```

**Create sales team user** (requires `-SalesTeamId` from the list above):

```powershell
.\deploy\aws\create-app-user.ps1 `
  -BaseUrl "http://<ALB_URL>" `
  -AdminUsername "admin" `
  -AdminPassword "admin123" `
  -Username "steam1" `
  -Email "steam1@company.com" `
  -Password "TempPass!123" `
  -FullName "Sales Team User" `
  -Role sales_team `
  -SalesTeamId 1
```

Valid `-Role` values: `admin`, `analyst`, `sales_team`.

## Updating the Application

### Rebuild and Redeploy

```powershell
# Build and push new image
.\deploy\aws\deploy-aws.ps1 -Region us-east-1

# Or manually:
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ECR_URI>
docker build -f deploy/Dockerfile -t <ECR_URI>:latest .
docker push <ECR_URI>:latest

# Force new deployment
aws ecs update-service --cluster loan-engine-test --service loan-engine-test --force-new-deployment --region us-east-1
```

## Troubleshooting

### 503 Service Temporarily Unavailable

This usually means the **Application Load Balancer has no healthy targets** (no ECS tasks passing the health check). Do the following:

1. **Check target health**
   ```powershell
   # Get target group ARN (replace region/profile as needed)
   $tgArn = aws elbv2 describe-target-groups --names loan-engine-test-tg --region us-east-1 --query "TargetGroups[0].TargetGroupArn" --output text
   aws elbv2 describe-target-health --target-group-arn $tgArn --region us-east-1
   ```
   If all targets are `Unhealthy` or there are no targets, the app or health check is failing.

2. **Check ECS service and tasks**
   ```powershell
   aws ecs describe-services --cluster loan-engine-test --services loan-engine-test --region us-east-1 --query "services[0].{runningCount:runningCount,desiredCount:desiredCount,events:events[0:3]}"
   aws ecs list-tasks --cluster loan-engine-test --service-name loan-engine-test --region us-east-1
   ```
   If `runningCount` is 0, tasks are failing to start or are being stopped.

3. **Check app logs** (database errors, missing env, crash on startup)
   ```powershell
   aws logs tail /ecs/loan-engine-test --region us-east-1
   ```

4. **Common causes**
   - **Database not reachable** – RDS security group must allow ECS security group on port 5432. App fails `/health/ready` (DB check) and ALB marks target unhealthy.
   - **Secrets not found** – Task execution role needs permission to read Secrets Manager; wrong secret name/region.
   - **App crash on startup** – See CloudWatch log group `/ecs/loan-engine-test` for Python tracebacks.
   - **Tasks in private subnet without NAT** – If tasks need internet (e.g. pull secrets), they need a NAT gateway or use public subnets for the service.

5. **Quick fix: force new deployment** (after fixing config)
   ```powershell
   aws ecs update-service --cluster loan-engine-test --service loan-engine-test --force-new-deployment --region us-east-1
   ```
   Wait 3–5 minutes, then check target health again.

### Service Not Starting

```powershell
# Check service events
aws ecs describe-services --cluster loan-engine-test --services loan-engine-test --region us-east-1 --query "services[0].events"

# Check task logs
aws logs tail /ecs/loan-engine-test --follow --region us-east-1

# Check task stopped reason
aws ecs describe-tasks --cluster loan-engine-test --tasks <TASK_ID> --region us-east-1 --query "tasks[0].stoppedReason"
```

### Database Connection Issues

- Verify RDS security group allows traffic from ECS security group on port 5432
- Check Secrets Manager secrets are correctly formatted
- Verify task execution role has permissions to read secrets

### ALB Health Check Failing

- Verify `/health/ready` endpoint is accessible
- Check ECS task is running and healthy
- Verify security groups allow ALB → ECS traffic on port 8000

### Docker Build Issues

- Ensure Docker Desktop is running
- Check you're logged into ECR: `aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ECR_URI>`
- Verify Dockerfile path is correct relative to repo root

## Cleanup

To delete all created resources:

```powershell
# Delete ECS service (scales to 0)
aws ecs update-service --cluster loan-engine-test --service loan-engine-test --desired-count 0 --region us-east-1
aws ecs delete-service --cluster loan-engine-test --service loan-engine-test --region us-east-1

# Delete task definition revisions
aws ecs list-task-definitions --family-prefix loan-engine-test --region us-east-1 | ForEach-Object { aws ecs deregister-task-definition --task-definition $_ --region us-east-1 }

# Delete ALB and target group
aws elbv2 delete-load-balancer --load-balancer-arn <ALB_ARN> --region us-east-1
aws elbv2 delete-target-group --target-group-arn <TG_ARN> --region us-east-1

# Delete RDS instance
aws rds delete-db-instance --db-instance-identifier loan-engine-test-db --skip-final-snapshot --region us-east-1

# Delete ECR repository
aws ecr delete-repository --repository-name loan-engine --force --region us-east-1

# Delete Secrets Manager secrets
aws secretsmanager delete-secret --secret-id loan-engine/test/DATABASE_URL --force-delete-without-recovery --region us-east-1
aws secretsmanager delete-secret --secret-id loan-engine/test/SECRET_KEY --force-delete-without-recovery --region us-east-1

# Delete IAM roles (detach policies first)
aws iam delete-role-policy --role-name ecsTaskExecutionRole-loan-engine --policy-name CloudWatchLogsPolicy --region us-east-1
aws iam detach-role-policy --role-name ecsTaskExecutionRole-loan-engine --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy --region us-east-1
aws iam delete-role --role-name ecsTaskExecutionRole-loan-engine --region us-east-1
aws iam delete-role-policy --role-name ecsTaskRole-loan-engine --policy-name SecretsManagerPolicy --region us-east-1
aws iam delete-role --role-name ecsTaskRole-loan-engine --region us-east-1

# Delete CloudWatch log group
aws logs delete-log-group --log-group-name /ecs/loan-engine-test --region us-east-1

# Delete VPC (delete subnets, route tables, IGW, security groups first)
# This is complex - use AWS Console or delete resources manually
```

## Cost Estimation

Approximate monthly costs (us-east-1, as of 2024):

- **RDS db.t3.micro**: ~$15/month (free tier eligible for first 12 months)
- **ECS Fargate** (1 task, 0.5 vCPU, 1GB): ~$15/month
- **ALB**: ~$16/month + data transfer
- **ECR**: Storage ~$0.10/GB/month
- **CloudWatch Logs**: ~$0.50/GB ingested
- **VPC**: Free
- **Secrets Manager**: $0.40/secret/month

**Total**: ~$47-50/month (or ~$32/month if RDS is in free tier)

## Security Notes

- Database password and SECRET_KEY are auto-generated and stored in Secrets Manager
- RDS is publicly accessible (for initial setup). Consider moving to private subnet and using VPN/Bastion for production
- ALB uses HTTP only. Add HTTPS with ACM certificate for production
- Security groups follow least-privilege principle
- IAM roles use minimal required permissions

## Next Steps

- [ ] Add HTTPS/SSL certificate to ALB
- [ ] Move RDS to private subnet
- [ ] Set up CloudWatch alarms
- [ ] Configure auto-scaling for ECS service
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Add backup strategy for RDS
- [ ] Configure VPC endpoints for AWS services (reduce NAT Gateway costs)
