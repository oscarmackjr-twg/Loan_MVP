# Quick Start: Deploy Loan Engine to AWS

## Prerequisites Checklist

- [ ] AWS CLI installed: `aws --version`
- [ ] AWS credentials configured: `aws configure`
- [ ] Docker Desktop running
- [ ] PowerShell 5.1+ available

## Step 1: Deploy Everything

From the repository root:

```powershell
# For IAM Identity Center / AWS SSO profiles:
.\deploy\aws\deploy-aws.ps1 -Region us-east-1 -Profile AWSAdministratorAccess-014148916722

# For default AWS credentials:
.\deploy\aws\deploy-aws.ps1 -Region us-east-1
```

**What this does:**
- Creates VPC, subnets, security groups
- Creates RDS PostgreSQL database
- Creates ECR repository
- Builds and pushes Docker image
- Creates ECS cluster and service
- Creates Application Load Balancer
- Sets up IAM roles and secrets

**Time:** ~10-15 minutes (mostly waiting for RDS)

## Step 2: Wait for Service to be Healthy

```powershell
# Check status
aws ecs describe-services --cluster loan-engine-test --services loan-engine-test --region us-east-1 --query "services[0].{Status:status,Running:runningCount,Desired:desiredCount}"
```

Wait until `runningCount` equals `desiredCount` and status is `ACTIVE`.

## Step 3: Initialize Database

**Option A: From your local machine** (requires PostgreSQL client or Python)

```powershell
.\deploy\aws\init-database.ps1 -Region us-east-1
```

**Option B: Via ECS Exec** (requires SSM Session Manager plugin)

```powershell
.\deploy\aws\init-database.ps1 -Region us-east-1 -Method ecs
```

## Step 4: Get Application URL

```powershell
# Get ALB DNS name
aws elbv2 describe-load-balancers --names loan-engine-test-alb --region us-east-1 --query "LoadBalancers[0].DNSName" --output text
```

Open in browser: `http://<ALB_DNS_NAME>`

## Step 5: Login

- **Username:** `admin`
- **Password:** `admin123`
- **⚠️ Change password immediately!**

## Common Commands

### Check Service Status
```powershell
aws ecs describe-services --cluster loan-engine-test --services loan-engine-test --region us-east-1
```

### View Logs
```powershell
aws logs tail /ecs/loan-engine-test --follow --region us-east-1
```

### Update Application (after code changes)
```powershell
.\deploy\aws\deploy-aws.ps1 -Region us-east-1
```

### Get Database Endpoint
```powershell
aws rds describe-db-instances --db-instance-identifier loan-engine-test-db --region us-east-1 --query "DBInstances[0].Endpoint.Address" --output text
```

### Get Application URL
```powershell
aws elbv2 describe-load-balancers --names loan-engine-test-alb --region us-east-1 --query "LoadBalancers[0].DNSName" --output text
```

## Troubleshooting

**Service won't start?**
- Check logs: `aws logs tail /ecs/loan-engine-test --region us-east-1`
- Check service events: `aws ecs describe-services --cluster loan-engine-test --services loan-engine-test --region us-east-1 --query "services[0].events"`

**Can't connect to database?**
- Verify RDS is running: `aws rds describe-db-instances --db-instance-identifier loan-engine-test-db --region us-east-1`
- Check security groups allow ECS → RDS traffic

**Health check failing?**
- Verify `/health/ready` endpoint works
- Check ECS task is running: `aws ecs list-tasks --cluster loan-engine-test --region us-east-1`

## Next Steps

- [ ] Add HTTPS certificate to ALB
- [ ] Set up CloudWatch alarms
- [ ] Configure auto-scaling
- [ ] Set up CI/CD pipeline
- [ ] Review security groups and network architecture

## Need Help?

See `README.md` for detailed documentation and troubleshooting.
