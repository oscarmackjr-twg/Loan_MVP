# S3 Setup for IAM Identity Center (SSO) Organizations

This is a quick reference guide specifically for AWS organizations using **IAM Identity Center** (formerly AWS SSO).

## Key Differences

In IAM Identity Center organizations:
- ❌ **Don't create IAM users** with access keys (usually not allowed)
- ✅ **Use IAM Roles** attached to your ECS tasks
- ✅ **Use AWS SSO** for local development credentials

---

## Quick Setup Guide

### 1. Create S3 Bucket

Same as standard setup - create bucket in AWS Console → S3.

### 2. Create IAM Role for ECS Tasks

**This is the main step for SSO organizations:**

1. **IAM Console** → **Roles** → **Create role**
2. **Trusted entity type**: AWS service
3. **Service**: Elastic Container Service → **Elastic Container Service Task**
4. **Permissions**: Attach `AmazonS3FullAccess` (or custom policy)
5. **Role name**: `loan-engine-ecs-s3-role`
6. **Create role**

### 3. Update ECS Task Definition

In your `deploy/aws/deploy-aws.ps1` or task definition JSON:

```json
{
  "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/loan-engine-ecs-s3-role",
  ...
}
```

Or in PowerShell (deploy-aws.ps1):
```powershell
# Find where task role is set and ensure it points to your S3 role
$TaskRoleArn = "arn:aws:iam::$accountId:role/loan-engine-ecs-s3-role"
```

### 4. Configure Application

**No credentials needed!** Just set:

```env
STORAGE_TYPE=s3
S3_BUCKET_NAME=your-bucket-name
S3_REGION=us-east-1
# No S3_ACCESS_KEY_ID or S3_SECRET_ACCESS_KEY
```

The ECS task will automatically use the IAM role.

---

## Local Development with SSO

### Option 1: Use SSO Profile (Recommended)

1. **Configure SSO** (if not already done):
   ```powershell
   aws configure sso
   ```
   - Enter SSO start URL (from your org admin)
   - Enter account ID
   - Choose a profile name (e.g., `loan-engine-dev`)

2. **Login**:
   ```powershell
   aws sso login --profile loan-engine-dev
   ```

3. **Set Environment Variable**:
   ```env
   AWS_PROFILE=loan-engine-dev
   STORAGE_TYPE=s3
   S3_BUCKET_NAME=your-bucket-name
   S3_REGION=us-east-1
   ```

4. **Run Application**:
   - boto3 will automatically use your SSO credentials
   - Credentials refresh automatically when they expire

### Option 2: Export Temporary Credentials

If you need explicit credentials:

```powershell
# After aws sso login
$creds = aws configure export-credentials --profile loan-engine-dev --format env
# Outputs:
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...
# AWS_SESSION_TOKEN=...
# AWS_SESSION_EXPIRATION=...

# Add to .env (note: expires in ~8-12 hours)
```

---

## Troubleshooting

### "Access Denied" Errors

1. **Check IAM Role Permissions**:
   - IAM → Roles → `loan-engine-ecs-s3-role`
   - Verify `AmazonS3FullAccess` is attached (or custom policy)

2. **Verify Task Role in ECS**:
   - ECS Console → Task Definition → Your task
   - Check "Task role" matches your role ARN

3. **Check Bucket Policy** (if any):
   - S3 → Your bucket → Permissions → Bucket policy
   - Ensure it allows your role (if custom policy exists)

### "No Credentials Found"

**For ECS:**
- Ensure task role is set in task definition
- Check task role ARN is correct

**For Local Development:**
- Run `aws sso login --profile your-profile`
- Check `AWS_PROFILE` environment variable is set
- Verify SSO session hasn't expired

### SSO Session Expired

```powershell
# Re-login
aws sso login --profile your-profile

# Or check status
aws sts get-caller-identity --profile your-profile
```

---

## Best Practices for SSO Organizations

1. ✅ **Always use IAM Roles** for ECS tasks (never access keys)
2. ✅ **Use SSO profiles** for local development
3. ✅ **Create custom IAM policies** (more restrictive than `AmazonS3FullAccess`)
4. ✅ **Use separate roles** for test vs production environments
5. ✅ **Document role ARNs** in your deployment scripts

---

## Custom IAM Policy (More Secure)

Instead of `AmazonS3FullAccess`, create a policy that only allows access to your specific bucket:

**IAM → Policies → Create policy → JSON:**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name",
                "arn:aws:s3:::your-bucket-name/*"
            ]
        }
    ]
}
```

Name it: `loan-engine-s3-policy` and attach to your role.

---

## Quick Reference

**ECS Task Role Setup:**
```powershell
# Role ARN format
arn:aws:iam::ACCOUNT_ID:role/loan-engine-ecs-s3-role

# In deploy-aws.ps1, ensure task definition includes:
"taskRoleArn": "arn:aws:iam::$accountId:role/loan-engine-ecs-s3-role"
```

**Environment Variables (ECS):**
```env
STORAGE_TYPE=s3
S3_BUCKET_NAME=loan-engine-test-files
S3_REGION=us-east-1
# No credentials needed - uses task role
```

**Local Development:**
```powershell
# Login
aws sso login --profile loan-engine-dev

# Set in .env
AWS_PROFILE=loan-engine-dev
STORAGE_TYPE=s3
S3_BUCKET_NAME=loan-engine-test-files
S3_REGION=us-east-1
```

---

## Need Help?

- **Check with your AWS Organization Admin** if you need help creating roles
- **Verify SSO Configuration**: `aws configure sso`
- **Test Role Permissions**: Use AWS Console → IAM → Roles → Your role → "Access advisor"
