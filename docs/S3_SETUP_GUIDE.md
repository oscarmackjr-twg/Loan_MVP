# S3 Storage Setup Guide for Beginners

This guide will help you set up AWS S3 (Simple Storage Service) so your Loan Engine application can store files in the cloud instead of on your local computer.

> **🔐 Using IAM Identity Center (SSO)?** If your AWS organization uses IAM Identity Center, see the dedicated guide: **[S3 Setup for IAM Identity Center](./S3_SETUP_IAM_IDENTITY_CENTER.md)** - it's simpler and follows organizational best practices.

## What is S3?

**S3 (Simple Storage Service)** is Amazon's cloud storage service. Think of it like a giant hard drive in the cloud where you can store files (like Dropbox or Google Drive, but for applications).

- **Development**: Files are stored on your local computer
- **Test/Production**: Files are stored in S3 buckets in AWS

## Prerequisites

Before you start, you need:
1. An AWS account (if you don't have one, sign up at https://aws.amazon.com/)
2. Access to the AWS Console (web interface)
3. Basic understanding of your application's environment (test vs production)

---

## Step 1: Create an S3 Bucket

A **bucket** is like a folder in S3 where your files will be stored.

### 1.1 Log into AWS Console

1. Go to https://console.aws.amazon.com/
2. Sign in with your AWS account
3. Make sure you're in the correct **region** (e.g., `us-east-1` - shown in the top-right corner)

### 1.2 Navigate to S3

1. In the AWS Console search bar, type **"S3"**
2. Click on **"S3"** service
3. You'll see the S3 dashboard

### 1.3 Create a New Bucket

1. Click the **"Create bucket"** button (orange button, top-right)
2. Fill in the bucket details:

   **Bucket name:**
   - Must be globally unique (no two buckets in AWS can have the same name)
   - Use lowercase letters, numbers, and hyphens only
   - Example: `loan-engine-test-files` or `loan-engine-prod-files`
   - **Tip**: Include your company/org name to make it unique

   **AWS Region:**
   - Select the same region as your application (e.g., `US East (N. Virginia) us-east-1`)
   - **Important**: Use the same region as your ECS/RDS to avoid extra costs

   **Object Ownership:**
   - Leave default: **"ACLs disabled (recommended)"**

   **Block Public Access settings:**
   - **Uncheck** "Block all public access" (or leave checked if you want private-only)
   - For this application, you can leave it checked (private) since we'll use presigned URLs

   **Bucket Versioning:**
   - Leave disabled (unless you need file version history)

   **Default encryption:**
   - **Enable** encryption (recommended)
   - Choose **"Amazon S3 managed keys (SSE-S3)"** (simplest option)

   **Tags (optional):**
   - Add tags like `Environment: test` or `Project: loan-engine` for organization

3. Click **"Create bucket"** at the bottom

### 1.4 Note Your Bucket Name

Write down your bucket name - you'll need it later:
```
Bucket Name: _____________________________
Region: _____________________________
```

---

## Step 2: Set Up Access Credentials

> **⚠️ Important**: If you're in an **AWS Organization with IAM Identity Center (SSO)**, skip to [Step 2A: IAM Identity Center Setup](#step-2a-iam-identity-center-setup) below. Otherwise, continue with Step 2B.

---

### Step 2A: IAM Identity Center Setup (For AWS Organizations)

If your AWS account uses **IAM Identity Center** (formerly AWS SSO), you typically **don't create IAM users**. Instead, you use **IAM Roles** that your application assumes.

#### Option 1: Use ECS Task Role (Recommended for ECS Deployments)

This is the **best and most secure** option for applications running on AWS ECS:

1. **Create an IAM Role for ECS Tasks**:
   - Go to **IAM** → **Roles** → **Create role**
   - Select **"AWS service"** → **"Elastic Container Service"** → **"Elastic Container Service Task"**
   - Click **"Next"**

2. **Attach S3 Permissions**:
   - Search for and select: **"AmazonS3FullAccess"** (or create a custom policy - see Advanced section)
   - Click **"Next"**

3. **Name the Role**:
   - Role name: `loan-engine-ecs-s3-role` (or similar)
   - Add description: "Allows ECS tasks to access S3 for file storage"
   - Click **"Create role"**

4. **Update Your ECS Task Definition**:
   - In your `deploy/aws/deploy-aws.ps1` or task definition JSON, ensure the task role is set to this role
   - The ECS task will automatically use this role - **no access keys needed!**

5. **Configure Application** (no credentials needed):
   ```env
   STORAGE_TYPE=s3
   S3_BUCKET_NAME=your-bucket-name
   S3_REGION=us-east-1
   # No S3_ACCESS_KEY_ID or S3_SECRET_ACCESS_KEY - uses IAM role automatically
   ```

#### Option 2: Use AWS SSO CLI for Local Development

For **local development** on your computer, use AWS SSO to get temporary credentials:

1. **Install AWS CLI** (if not already installed):
   ```powershell
   # Download from: https://aws.amazon.com/cli/
   ```

2. **Configure AWS SSO**:
   ```powershell
   aws configure sso
   ```
   - Follow prompts to set up your SSO profile
   - You'll need your SSO start URL and account ID from your organization admin

3. **Login to SSO**:
   ```powershell
   aws sso login --profile your-sso-profile-name
   ```

4. **Get Temporary Credentials** (for testing):
   ```powershell
   # Credentials are automatically available when logged in via SSO
   # Your application can use the default AWS credential chain
   ```

5. **For Application Use** (if needed):
   - The AWS SDK (boto3) will automatically use your SSO credentials
   - Or set environment variables from SSO session (see below)

#### Option 3: Create a Service Account Role (If Allowed)

Some organizations allow creating service accounts for applications:

1. **Ask your AWS Organization Admin** to create a service account role
2. **Request permissions**:
   - Role name: `loan-engine-service-role`
   - Attach policy: `AmazonS3FullAccess` (or custom policy)
   - Note the **Role ARN**

3. **Assume the Role** from your application:
   ```python
   # The application can assume this role using STS
   # boto3 will handle this automatically if configured
   ```

#### Option 4: Use Cross-Account Role (If Application Runs in Different Account)

If your application runs in a different AWS account:

1. **Create a Role** in the S3 bucket's account:
   - IAM → Roles → Create role
   - Select **"Another AWS account"**
   - Enter your application's account ID
   - Attach S3 permissions
   - Note the **Role ARN**

2. **Configure Application** to assume this role:
   ```python
   # Use boto3 STS to assume the role
   ```

**For IAM Identity Center organizations, Option 1 (ECS Task Role) is recommended** - it's the most secure and requires no credential management.

---

### Step 2B: Standard IAM User Setup (For Non-SSO Accounts)

IAM (Identity and Access Management) controls who can access your AWS resources. You need to create a user with permission to read/write files in your S3 bucket.

### 2.1 Navigate to IAM

1. In the AWS Console search bar, type **"IAM"**
2. Click on **"IAM"** service

### 2.2 Create a New User

1. In the left sidebar, click **"Users"**
2. Click **"Create user"** button (top-right)

### 2.3 Set User Details

1. **User name:**
   - Example: `loan-engine-s3-user` or `loan-engine-file-storage`
   - Click **"Next"**

2. **Set permissions:**
   - Select **"Attach policies directly"**
   - Search for and select: **"AmazonS3FullAccess"**
   - **Note**: For production, create a custom policy that only allows access to your specific bucket (see "Advanced: Custom Policy" section below)
   - Click **"Next"**

3. **Review and create:**
   - Review the settings
   - Click **"Create user"**

### 2.4 Create Access Keys

1. Click on the user you just created
2. Click the **"Security credentials"** tab
3. Scroll down to **"Access keys"** section
4. Click **"Create access key"**

5. **Use case:**
   - Select **"Application running outside AWS"** (since your app runs on ECS or your computer)
   - Check the confirmation box
   - Click **"Next"**

6. **Description (optional):**
   - Add a description like "Loan Engine S3 access"
   - Click **"Create access key"**

7. **IMPORTANT - Save Your Credentials:**
   - **Access Key ID**: Copy this immediately (you can see it later, but Secret Key is shown only once)
   - **Secret Access Key**: Copy this immediately - **you won't be able to see it again!**
   - Click **"Download .csv"** to save them to a file, or copy them to a secure password manager

   ```
   Access Key ID: _____________________________
   Secret Access Key: _____________________________
   ```

8. Click **"Done"**

---

## Step 3: Configure Your Application

Now you need to tell your application to use S3 instead of local storage.

### 3.1 For Local Development (Testing S3 from Your Computer)

#### If Using IAM Identity Center (SSO):

**Option A: Use AWS SSO Credentials (Recommended)**

1. **Login via SSO**:
   ```powershell
   aws sso login --profile your-sso-profile
   ```

2. **Configure Application** (no keys needed - uses SSO session):
   ```env
   # Storage Configuration
   STORAGE_TYPE=s3
   S3_BUCKET_NAME=your-bucket-name-here
   S3_REGION=us-east-1
   # No S3_ACCESS_KEY_ID or S3_SECRET_ACCESS_KEY needed
   # boto3 will use your SSO credentials automatically
   ```

3. **Set AWS Profile** (if using named profile):
   ```env
   AWS_PROFILE=your-sso-profile-name
   ```

**Option B: Use Temporary Credentials from SSO**

If you need explicit credentials, export them from your SSO session:

```powershell
# After aws sso login, get credentials
$creds = aws configure export-credentials --profile your-sso-profile --format env
# This will output AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN
# Add these to your .env file (note: they expire after a few hours)
```

#### If Using Standard IAM User:

Create or edit a `.env` file in your `backend/` directory:

```env
# Storage Configuration
STORAGE_TYPE=s3
S3_BUCKET_NAME=your-bucket-name-here
S3_REGION=us-east-1
S3_ACCESS_KEY_ID=your-access-key-id-here
S3_SECRET_ACCESS_KEY=your-secret-access-key-here
S3_BASE_PREFIX=test/  # Optional: prefix for all files (e.g., "test/" or "dev/")
```

**Replace:**
- `your-bucket-name-here` with your actual bucket name
- `us-east-1` with your bucket's region
- `your-access-key-id-here` with your Access Key ID
- `your-secret-access-key-here` with your Secret Access Key

**Example:**
```env
STORAGE_TYPE=s3
S3_BUCKET_NAME=loan-engine-test-files
S3_REGION=us-east-1
S3_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
S3_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
S3_BASE_PREFIX=test/
```

### 3.2 For AWS ECS (Production/Test Environment)

If your application runs on AWS ECS, **use an IAM Role** (recommended and required for IAM Identity Center organizations):

#### Use IAM Role (Recommended - Required for SSO Organizations)

Instead of storing credentials in environment variables, use an IAM role attached to your ECS task:

1. **Create an IAM Role** (if you haven't already):
   - Go to IAM → Roles → Create role
   - Select **"AWS service"** → **"Elastic Container Service"** → **"Elastic Container Service Task"**
   - Click **"Next"**
   - Attach policy: **"AmazonS3FullAccess"** (or create custom policy - see Advanced section)
   - Click **"Next"**
   - Name it: `loan-engine-ecs-s3-role` (or similar)
   - Add description: "Allows ECS tasks to access S3 for file storage"
   - Click **"Create role"**
   - Note the **Role ARN** (you'll need this for your task definition)

2. **Update your ECS Task Definition**:
   - In `deploy/aws/deploy-aws.ps1`, find where the task role is configured
   - Set the `taskRoleArn` to your new role's ARN
   - The application will automatically use the task role credentials (no keys needed!)

3. **Set Environment Variables** (no credentials needed):
   ```env
   STORAGE_TYPE=s3
   S3_BUCKET_NAME=loan-engine-prod-files
   S3_REGION=us-east-1
   # No S3_ACCESS_KEY_ID or S3_SECRET_ACCESS_KEY needed - uses IAM role automatically
   ```

**For IAM Identity Center organizations, this is the ONLY recommended approach** - it's more secure and aligns with organizational policies.

#### Alternative: Use Secrets Manager (Only if IAM Role Not Possible)

If your organization doesn't allow IAM roles for some reason, store credentials in AWS Secrets Manager:

1. **Create a Secret**:
   ```powershell
   # Run from deploy/aws directory
   .\create-s3-credentials-secret.ps1 -Region us-east-1 -BucketName your-bucket-name -AccessKeyId your-key -SecretKey your-secret -Profile your-sso-profile
   ```

2. **Update ECS Task Definition** to pull the secret as environment variables
3. **Note**: This requires creating an IAM user with access keys, which may not be allowed in SSO organizations

---

## Step 4: Test Your Setup

### 4.1 Test from Your Computer

1. **Start your backend**:
   ```powershell
   cd backend
   python -m uvicorn api.main:app --reload
   ```

2. **Test via API** (using curl or Postman):
   ```bash
   # List files (should return empty or existing files)
   curl http://localhost:8000/api/files/list
   
   # Upload a test file
   curl -X POST http://localhost:8000/api/files/upload \
     -F "file=@test.txt" \
     -F "path=test/"
   ```

3. **Check in AWS Console**:
   - Go to S3 → Your bucket
   - You should see your uploaded files

### 4.2 Test from Frontend

1. Start your frontend: `npm run dev` (in `frontend/` directory)
2. Log in to the application
3. Go to **"File Manager"** page
4. Try uploading a file via drag-and-drop
5. Check that it appears in your S3 bucket

---

## Step 5: Verify Everything Works

### Checklist

- [ ] S3 bucket created and accessible
- [ ] IAM user created with S3 permissions
- [ ] Access keys saved securely
- [ ] `.env` file configured (or ECS task role set up)
- [ ] Application can list files in S3
- [ ] Application can upload files to S3
- [ ] Application can download files from S3
- [ ] Files appear in AWS S3 Console

---

## Common Issues and Solutions

### Issue: "Access Denied" or "403 Forbidden"

**Cause**: IAM user doesn't have permission, or credentials are wrong.

**Solution**:
1. Check IAM user has `AmazonS3FullAccess` policy (or custom policy)
2. Verify Access Key ID and Secret Access Key are correct
3. Check bucket name is correct
4. Ensure bucket region matches `S3_REGION` setting

### Issue: "Bucket does not exist" or "404 Not Found"

**Cause**: Bucket name is wrong, or bucket is in a different region.

**Solution**:
1. Double-check bucket name (case-sensitive)
2. Verify region matches
3. List your buckets: AWS Console → S3 → Buckets

### Issue: "Invalid credentials"

**Cause**: Access keys are incorrect or expired.

**Solution**:
1. Regenerate access keys in IAM → Users → Your user → Security credentials
2. Update `.env` file with new keys
3. Restart your application

### Issue: Files upload but can't download

**Cause**: Bucket has "Block public access" enabled, but you're trying to access files publicly.

**Solution**:
- The application uses **presigned URLs** (temporary, secure URLs) - this should work even with private buckets
- If downloads fail, check IAM permissions include `s3:GetObject`

### Issue: "Region mismatch"

**Cause**: Bucket is in one region, but `S3_REGION` setting is different.

**Solution**:
- Set `S3_REGION` to match your bucket's region exactly
- Common regions: `us-east-1`, `us-west-2`, `eu-west-1`

---

## Advanced: Custom IAM Policy (More Secure)

Instead of `AmazonS3FullAccess`, create a policy that only allows access to your specific bucket:

1. Go to IAM → Policies → Create policy
2. Click **"JSON"** tab
3. Paste this (replace `your-bucket-name`):

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

4. Name it: `loan-engine-s3-policy`
5. Attach this policy to your IAM user instead of `AmazonS3FullAccess`

---

## Cost Considerations

S3 pricing (as of 2024):
- **Storage**: ~$0.023 per GB/month (Standard storage)
- **Requests**: 
  - PUT requests: ~$0.005 per 1,000 requests
  - GET requests: ~$0.0004 per 1,000 requests
- **Data transfer**: Free within same region, charges for outbound data

**For small applications**: Usually costs less than $1-5/month

**Monitor costs**: AWS Console → Billing → Cost Explorer

---

## Next Steps

Once S3 is set up:

1. **Update your deployment scripts** to set S3 environment variables
2. **Test file uploads/downloads** in your test environment
3. **Migrate existing files** from local storage to S3 (if needed)
4. **Set up S3 lifecycle policies** (optional - auto-delete old files)
5. **Enable S3 versioning** (optional - keep file history)

---

## Getting Help

- **AWS Documentation**: https://docs.aws.amazon.com/s3/
- **AWS Support**: AWS Console → Support Center
- **Check application logs**: Look for S3-related errors in your backend logs

---

## Quick Reference

**Environment Variables:**
```env
STORAGE_TYPE=s3
S3_BUCKET_NAME=your-bucket-name
S3_REGION=us-east-1
S3_ACCESS_KEY_ID=your-access-key-id
S3_SECRET_ACCESS_KEY=your-secret-key
S3_BASE_PREFIX=test/  # Optional
```

**Switch back to local storage:**
```env
STORAGE_TYPE=local
# Comment out or remove S3_* variables
```

**Test S3 connection:**
```python
from storage import get_storage_backend
storage = get_storage_backend()
files = storage.list_files("")
print(f"Found {len(files)} files in S3")
```
