# AWS Deployment Script for Loan Engine
# This script creates all required AWS resources from scratch
# Prerequisites: AWS CLI installed and configured with valid credentials
# Usage: .\deploy-aws.ps1 -Region us-east-1 -AppName loan-engine

param(
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1",
    
    [Parameter(Mandatory=$false)]
    [string]$AppName = "loan-engine",
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "test",
    
    [Parameter(Mandatory=$false)]
    [string]$DBUsername = "postgres",
    
    [Parameter(Mandatory=$false)]
    [string]$DBPassword = "",  # Will generate if empty
    
    [Parameter(Mandatory=$false)]
    [string]$SecretKey = "",  # Will generate if empty
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBuild = $false,
    
    [Parameter(Mandatory=$false)]
    [string]$Profile = ""  # AWS CLI profile name (e.g., AWSAdministratorAccess-014148916722)
)

# Error handling
# Note: Script is idempotent - safe to re-run if it fails partway through
# It will skip resources that already exist and continue from where it left off
$ErrorActionPreference = "Stop"

# Colors for output
function Write-Info { Write-Host "$args" -ForegroundColor Cyan }
function Write-Success { Write-Host "$args" -ForegroundColor Green }
function Write-Warning { Write-Host "$args" -ForegroundColor Yellow }
function Write-Error { Write-Host "$args" -ForegroundColor Red }

# Helper function to execute AWS CLI commands with optional profile
# Runs via cmd /c so PowerShell never sees AWS stderr (avoids NativeCommandError).
# Callers should check $LASTEXITCODE after the call to detect failures.
function Invoke-AwsCli {
    param(
        [Parameter(ValueFromRemainingArguments=$true)]
        [string[]]$Arguments
    )
    # Build argument list
    $allArgs = [System.Collections.ArrayList]::new()
    if (-not [string]::IsNullOrEmpty($Profile)) {
        [void]$allArgs.Add("--profile")
        [void]$allArgs.Add($Profile)
    }
    if ($Arguments -and $Arguments.Count -gt 0) {
        foreach ($arg in $Arguments) {
            if ($null -ne $arg) { [void]$allArgs.Add($arg) }
        }
    }
    # Escape each arg for cmd: wrap in quotes and escape internal " as ""
    $cmdArgStrings = foreach ($a in $allArgs) {
        $s = [string]$a
        $s = $s -replace '"', '""'
        "`"$s`""
    }
    $cmdLine = "aws " + ($cmdArgStrings -join " ") + " 2>nul"
    cmd /c $cmdLine
}

# Run AWS CLI and show stderr on failure (for error messages). Use same args as Invoke-AwsCli.
function Invoke-AwsCliShowError {
    param(
        [Parameter(ValueFromRemainingArguments=$true)]
        [string[]]$Arguments
    )
    $allArgs = [System.Collections.ArrayList]::new()
    if (-not [string]::IsNullOrEmpty($Profile)) {
        [void]$allArgs.Add("--profile")
        [void]$allArgs.Add($Profile)
    }
    if ($Arguments -and $Arguments.Count -gt 0) {
        foreach ($arg in $Arguments) {
            if ($null -ne $arg) { [void]$allArgs.Add($arg) }
        }
    }
    $cmdArgStrings = foreach ($a in $allArgs) {
        $s = [string]$a
        $s = $s -replace '"', '""'
        "`"$s`""
    }
    $cmdLine = "aws " + ($cmdArgStrings -join " ")
    Write-Warning "Running (showing AWS error output): aws $($Arguments -join ' ')"
    cmd /c $cmdLine
}

# Generate random password. For RDS, use -RdsSafe to exclude '/', '@', '"', ' ' (AWS requirement).
function New-RandomPassword {
    param(
        [int]$Length = 32,
        [switch]$RdsSafe
    )
    if ($RdsSafe) {
        $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%^&*()_+-=[]{}|;:,.<>?~"
    } else {
        $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    }
    $password = ""
    for ($i = 0; $i -lt $Length; $i++) {
        $password += $chars[(Get-Random -Maximum $chars.Length)]
    }
    return $password
}

# Check AWS CLI
Write-Info "Checking AWS CLI installation..."
try {
    $awsVersion = aws --version
    Write-Success "AWS CLI found: $awsVersion"
} catch {
    Write-Error "AWS CLI not found. Please install AWS CLI: https://aws.amazon.com/cli/"
    exit 1
}

# Check AWS credentials (call AWS CLI directly so we reliably get Account ID and see errors)
Write-Info "Checking AWS credentials..."
if (-not [string]::IsNullOrEmpty($Profile)) {
    Write-Info "Using AWS profile: $Profile"
    Write-Info "If session expired, run: aws sso login --profile $Profile"
}

$accountId = $null
try {
    if ([string]::IsNullOrEmpty($Profile)) {
        $accountId = (aws sts get-caller-identity --query Account --output text --region $Region 2>&1)
    } else {
        $accountId = (aws sts get-caller-identity --profile $Profile --query Account --output text --region $Region 2>&1)
    }
    $accountId = "$accountId".Trim()
    if ([string]::IsNullOrEmpty($accountId) -or $accountId -match "error|exception|denied") {
        $accountId = $null
    }
} catch {
    $accountId = $null
}

if ([string]::IsNullOrEmpty($accountId)) {
    Write-Error "Could not get AWS Account ID. Credentials may be missing or expired."
    if (-not [string]::IsNullOrEmpty($Profile)) {
        Write-Error "For IAM Identity Center, refresh your session: aws sso login --profile $Profile"
    } else {
        Write-Error "Run 'aws configure' or use -Profile and run: aws sso login --profile <name>"
    }
    exit 1
}

Write-Success "AWS Account ID: $accountId"

# Optional: detect AWS Organizations
try {
    if ([string]::IsNullOrEmpty($Profile)) {
        $null = aws organizations describe-account --account-id $accountId 2>$null
    } else {
        $null = aws organizations describe-account --account-id $accountId --profile $Profile 2>$null
    }
    if ($LASTEXITCODE -eq 0) {
        Write-Info "Detected AWS Organizations account."
    }
} catch { }

# Generate passwords if not provided
if ([string]::IsNullOrEmpty($DBPassword)) {
    $DBPassword = New-RandomPassword -Length 24 -RdsSafe
    Write-Info "Generated database password (saved to Secrets Manager)"
}
if ([string]::IsNullOrEmpty($SecretKey)) {
    $SecretKey = New-RandomPassword -Length 64
    Write-Info "Generated SECRET_KEY (saved to Secrets Manager)"
}

# Set variables
$VpcName = "$AppName-vpc"
$ClusterName = "$AppName-$Environment"
$ServiceName = "$AppName-$Environment"
$TaskFamily = "$AppName-$Environment"
$ECRRepoName = $AppName
$DBName = "loan_engine"
$DBInstanceClass = "db.t3.micro"  # Free tier eligible
$DBInstanceIdentifier = "$AppName-$Environment-db"
$LogGroupName = "/ecs/$AppName-$Environment"
$ALBName = "$AppName-$Environment-alb"

Write-Info "========================================="
Write-Info "AWS Deployment Configuration"
Write-Info "========================================="
Write-Info "Region: $Region"
Write-Info "App Name: $AppName"
Write-Info "Environment: $Environment"
Write-Info "Account ID: $accountId"
Write-Info "========================================="
Write-Host ""

# ============================================
# 1. Create VPC and Networking
# ============================================
Write-Info "[1/10] Creating VPC and networking resources..."

# Check if VPC already exists
$existingVpc = (Invoke-AwsCli ec2 describe-vpcs --filters "Name=tag:Name,Values=$VpcName" --query "Vpcs[0].VpcId" --output text --region $Region 2>$null) -replace '\s+$','' -replace '^\s+',''
if ($existingVpc -and $existingVpc -ne "None") {
    Write-Warning "VPC already exists: $existingVpc"
    $VpcId = $existingVpc
} else {
    # Create VPC
    $VpcId = (Invoke-AwsCli ec2 create-vpc --cidr-block 10.0.0.0/16 --region $Region --query "Vpc.VpcId" --output text) -replace '\s+$','' -replace '^\s+',''
    if ([string]::IsNullOrEmpty($VpcId)) {
        Write-Error "Failed to create VPC (no output). Check credentials."
        if (-not [string]::IsNullOrEmpty($Profile)) { Write-Error "Refresh SSO: aws sso login --profile $Profile" }
        exit 1
    }
    Invoke-AwsCli ec2 create-tags --resources $VpcId --tags "Key=Name,Value=$VpcName" --region $Region | Out-Null
    Write-Success "Created VPC: $VpcId"
    
    # Enable DNS hostnames
    Invoke-AwsCli ec2 modify-vpc-attribute --vpc-id $VpcId --enable-dns-hostnames --region $Region | Out-Null
    
    # Create Internet Gateway
    $IgwId = Invoke-AwsCli ec2 create-internet-gateway --region $Region --query "InternetGateway.InternetGatewayId" --output text
    Invoke-AwsCli ec2 attach-internet-gateway --internet-gateway-id $IgwId --vpc-id $VpcId --region $Region | Out-Null
    Invoke-AwsCli ec2 create-tags --resources $IgwId --tags "Key=Name,Value=$VpcName-igw" --region $Region | Out-Null
    Write-Success "Created Internet Gateway: $IgwId"
    
    # Get availability zones
    $azs = Invoke-AwsCli ec2 describe-availability-zones --region $Region --query "AvailabilityZones[0:2].ZoneName" --output text
    $azArray = $azs -split "`t"
    
    # Create public subnets
    $PublicSubnet1Id = Invoke-AwsCli ec2 create-subnet --vpc-id $VpcId --cidr-block 10.0.1.0/24 --availability-zone $azArray[0] --region $Region --query "Subnet.SubnetId" --output text
    $PublicSubnet2Id = Invoke-AwsCli ec2 create-subnet --vpc-id $VpcId --cidr-block 10.0.2.0/24 --availability-zone $azArray[1] --region $Region --query "Subnet.SubnetId" --output text
    Invoke-AwsCli ec2 create-tags --resources $PublicSubnet1Id --tags "Key=Name,Value=$VpcName-public-1" --region $Region | Out-Null
    Invoke-AwsCli ec2 create-tags --resources $PublicSubnet2Id --tags "Key=Name,Value=$VpcName-public-2" --region $Region | Out-Null
    Write-Success "Created public subnets: $PublicSubnet1Id, $PublicSubnet2Id"
    
    # Create private subnets
    $PrivateSubnet1Id = Invoke-AwsCli ec2 create-subnet --vpc-id $VpcId --cidr-block 10.0.11.0/24 --availability-zone $azArray[0] --region $Region --query "Subnet.SubnetId" --output text
    $PrivateSubnet2Id = Invoke-AwsCli ec2 create-subnet --vpc-id $VpcId --cidr-block 10.0.12.0/24 --availability-zone $azArray[1] --region $Region --query "Subnet.SubnetId" --output text
    Invoke-AwsCli ec2 create-tags --resources $PrivateSubnet1Id --tags "Key=Name,Value=$VpcName-private-1" --region $Region | Out-Null
    Invoke-AwsCli ec2 create-tags --resources $PrivateSubnet2Id --tags "Key=Name,Value=$VpcName-private-2" --region $Region | Out-Null
    Write-Success "Created private subnets: $PrivateSubnet1Id, $PrivateSubnet2Id"
    
    # Create route table for public subnets
    $PublicRouteTableId = Invoke-AwsCli ec2 create-route-table --vpc-id $VpcId --region $Region --query "RouteTable.RouteTableId" --output text
    Invoke-AwsCli ec2 create-route --route-table-id $PublicRouteTableId --destination-cidr-block 0.0.0.0/0 --gateway-id $IgwId --region $Region | Out-Null
    Invoke-AwsCli ec2 associate-route-table --subnet-id $PublicSubnet1Id --route-table-id $PublicRouteTableId --region $Region | Out-Null
    Invoke-AwsCli ec2 associate-route-table --subnet-id $PublicSubnet2Id --route-table-id $PublicRouteTableId --region $Region | Out-Null
    Write-Success "Created public route table"
}

# Get subnet IDs if VPC already existed
if (-not $PublicSubnet1Id) {
    $PublicSubnet1Id = Invoke-AwsCli ec2 describe-subnets --filters "Name=vpc-id,Values=$VpcId" "Name=tag:Name,Values=$VpcName-public-1" --query "Subnets[0].SubnetId" --output text --region $Region
    $PublicSubnet2Id = Invoke-AwsCli ec2 describe-subnets --filters "Name=vpc-id,Values=$VpcId" "Name=tag:Name,Values=$VpcName-public-2" --query "Subnets[0].SubnetId" --output text --region $Region
    $PrivateSubnet1Id = Invoke-AwsCli ec2 describe-subnets --filters "Name=vpc-id,Values=$VpcId" "Name=tag:Name,Values=$VpcName-private-1" --query "Subnets[0].SubnetId" --output text --region $Region
    $PrivateSubnet2Id = Invoke-AwsCli ec2 describe-subnets --filters "Name=vpc-id,Values=$VpcId" "Name=tag:Name,Values=$VpcName-private-2" --query "Subnets[0].SubnetId" --output text --region $Region
}

$SubnetIds = "$PublicSubnet1Id,$PublicSubnet2Id"
$PrivateSubnetIds = "$PrivateSubnet1Id,$PrivateSubnet2Id"

# ============================================
# 2. Create Security Groups
# ============================================
Write-Info "[2/10] Creating security groups..."

# ALB Security Group
$AlbSgName = "$AppName-$Environment-alb-sg"
$existingAlbSg = Invoke-AwsCli ec2 describe-security-groups --filters "Name=group-name,Values=$AlbSgName" "Name=vpc-id,Values=$VpcId" --query "SecurityGroups[0].GroupId" --output text --region $Region 2>$null
if ($existingAlbSg -and $existingAlbSg -ne "None") {
    $AlbSecurityGroupId = $existingAlbSg
    Write-Warning "ALB Security Group already exists: $AlbSecurityGroupId"
} else {
    $AlbSecurityGroupId = Invoke-AwsCli ec2 create-security-group --group-name $AlbSgName --description "Security group for $AppName ALB" --vpc-id $VpcId --region $Region --query "GroupId" --output text
    Invoke-AwsCli ec2 authorize-security-group-ingress --group-id $AlbSecurityGroupId --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $Region | Out-Null
    Invoke-AwsCli ec2 authorize-security-group-ingress --group-id $AlbSecurityGroupId --protocol tcp --port 443 --cidr 0.0.0.0/0 --region $Region | Out-Null
    Write-Success "Created ALB Security Group: $AlbSecurityGroupId"
}

# ECS Security Group
$EcsSgName = "$AppName-$Environment-ecs-sg"
$existingEcsSg = Invoke-AwsCli ec2 describe-security-groups --filters "Name=group-name,Values=$EcsSgName" "Name=vpc-id,Values=$VpcId" --query "SecurityGroups[0].GroupId" --output text --region $Region 2>$null
if ($existingEcsSg -and $existingEcsSg -ne "None") {
    $EcsSecurityGroupId = $existingEcsSg
    Write-Warning "ECS Security Group already exists: $EcsSecurityGroupId"
} else {
    $EcsSecurityGroupId = Invoke-AwsCli ec2 create-security-group --group-name $EcsSgName --description "Security group for $AppName ECS tasks" --vpc-id $VpcId --region $Region --query "GroupId" --output text
    Invoke-AwsCli ec2 authorize-security-group-ingress --group-id $EcsSecurityGroupId --protocol tcp --port 8000 --source-group $AlbSecurityGroupId --region $Region | Out-Null
    Write-Success "Created ECS Security Group: $EcsSecurityGroupId"
}

# RDS Security Group
$RdsSgName = "$AppName-$Environment-rds-sg"
$existingRdsSg = Invoke-AwsCli ec2 describe-security-groups --filters "Name=group-name,Values=$RdsSgName" "Name=vpc-id,Values=$VpcId" --query "SecurityGroups[0].GroupId" --output text --region $Region 2>$null
if ($existingRdsSg -and $existingRdsSg -ne "None") {
    $RdsSecurityGroupId = $existingRdsSg
    Write-Warning "RDS Security Group already exists: $RdsSecurityGroupId"
} else {
    $RdsSecurityGroupId = Invoke-AwsCli ec2 create-security-group --group-name $RdsSgName --description "Security group for $AppName RDS" --vpc-id $VpcId --region $Region --query "GroupId" --output text
    Invoke-AwsCli ec2 authorize-security-group-ingress --group-id $RdsSecurityGroupId --protocol tcp --port 5432 --source-group $EcsSecurityGroupId --region $Region | Out-Null
    Write-Success "Created RDS Security Group: $RdsSecurityGroupId"
}

# ============================================
# 3. Create CloudWatch Log Group
# ============================================
Write-Info "[3/10] Creating CloudWatch log group..."
try {
    Invoke-AwsCli logs create-log-group --log-group-name $LogGroupName --region $Region 2>$null
    Write-Success "Created log group: $LogGroupName"
} catch {
    Write-Warning "Log group may already exist"
}

# ============================================
# 4. Create IAM Roles
# ============================================
Write-Info "[4/10] Creating IAM roles..."
Write-Info "Note: IAM is global (not region-specific). Checking for existing roles..."

# ECS Task Execution Role
$TaskExecutionRoleName = "ecsTaskExecutionRole-$AppName"
$existingTaskRole = $null
try {
    $existingTaskRole = Invoke-AwsCli iam get-role --role-name $TaskExecutionRoleName 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0 -and $existingTaskRole -notmatch "NoSuchEntity") {
        $TaskExecutionRoleArn = (Invoke-AwsCli iam get-role --role-name $TaskExecutionRoleName --query "Role.Arn" --output text)
        Write-Warning "Task Execution Role already exists: $TaskExecutionRoleArn"
    } else {
        $existingTaskRole = $null
    }
} catch {
    $existingTaskRole = $null
}

if (-not $existingTaskRole) {
    # Create trust policy (compact JSON, no BOM)
    $trustPolicy = @{
        Version = "2012-10-17"
        Statement = @(
            @{
                Effect = "Allow"
                Principal = @{
                    Service = "ecs-tasks.amazonaws.com"
                }
                Action = "sts:AssumeRole"
            }
        )
    } | ConvertTo-Json -Depth 10 -Compress
    
    $trustPolicyFile = "$env:TEMP\ecs-trust-policy.json"
    # Write UTF-8 without BOM (AWS requires this)
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($trustPolicyFile, $trustPolicy, $utf8NoBom)
    
    Write-Info "Creating Task Execution Role: $TaskExecutionRoleName"
    try {
        $TaskExecutionRoleArn = (Invoke-AwsCli iam create-role --role-name $TaskExecutionRoleName --assume-role-policy-document "file://$trustPolicyFile" --query "Role.Arn" --output text)
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create role"
        }
        
        # Attach managed policy
        Write-Info "Attaching managed policy to Task Execution Role..."
        Invoke-AwsCli iam attach-role-policy --role-name $TaskExecutionRoleName --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy" | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Failed to attach managed policy. You may need to attach it manually."
        }
        
        # Attach CloudWatch Logs policy
        $logsPolicy = @{
            Version = "2012-10-17"
            Statement = @(
                @{
                    Effect = "Allow"
                    Action = @(
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    )
                    Resource = "arn:aws:logs:$Region`:$accountId`:log-group:$LogGroupName`:*"
                }
            )
        } | ConvertTo-Json -Depth 10 -Compress
        
        $logsPolicyFile = "$env:TEMP\ecs-logs-policy.json"
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($logsPolicyFile, $logsPolicy, $utf8NoBom)
        Invoke-AwsCli iam put-role-policy --role-name $TaskExecutionRoleName --policy-name CloudWatchLogsPolicy --policy-document "file://$logsPolicyFile" | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Failed to attach CloudWatch Logs policy. You may need to attach it manually."
        }
        
        Write-Success "Created Task Execution Role: $TaskExecutionRoleArn"
    } catch {
        Write-Error "Failed to create Task Execution Role: $_"
        Write-Error "AWS error output:"
        Invoke-AwsCliShowError iam create-role --role-name $TaskExecutionRoleName --assume-role-policy-document "file://$trustPolicyFile" --query "Role.Arn" --output text | Out-Host
        Write-Error "In AWS Organizations, you may need permissions or SCPs that allow role creation."
        exit 1
    }
}

# Task Execution Role must pull secrets at container startup (ECS agent uses this role)
$execSecretsPolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Action = @(
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            )
            Resource = "arn:aws:secretsmanager:$Region`:$accountId`:secret:$AppName/$Environment/*"
        }
    )
} | ConvertTo-Json -Depth 10 -Compress
$execSecretsPolicyFile = "$env:TEMP\ecs-execution-secrets-policy.json"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($execSecretsPolicyFile, $execSecretsPolicy, $utf8NoBom)
Invoke-AwsCli iam put-role-policy --role-name $TaskExecutionRoleName --policy-name SecretsManagerAccess --policy-document "file://$execSecretsPolicyFile" | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Success "Task Execution Role has Secrets Manager access (SecretsManagerAccess)"
} else {
    Write-Warning "Failed to attach Secrets Manager policy to Task Execution Role. Tasks may fail with AccessDeniedException when pulling secrets."
}

# Task Role (for app to access AWS services)
$TaskRoleName = "ecsTaskRole-$AppName"
$existingTaskAppRole = $null
try {
    $existingTaskAppRole = Invoke-AwsCli iam get-role --role-name $TaskRoleName 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0 -and $existingTaskAppRole -notmatch "NoSuchEntity") {
        $TaskRoleArn = (Invoke-AwsCli iam get-role --role-name $TaskRoleName --query "Role.Arn" --output text)
        Write-Warning "Task Role already exists: $TaskRoleArn"
    } else {
        $existingTaskAppRole = $null
    }
} catch {
    $existingTaskAppRole = $null
}

if (-not $existingTaskAppRole) {
    Write-Info "Creating Task Role: $TaskRoleName"
    try {
        $TaskRoleArn = (Invoke-AwsCli iam create-role --role-name $TaskRoleName --assume-role-policy-document "file://$trustPolicyFile" --query "Role.Arn" --output text)
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create role"
        }
        
        # Policy for Secrets Manager access
        $secretsPolicy = @{
            Version = "2012-10-17"
            Statement = @(
                @{
                    Effect = "Allow"
                    Action = @(
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:DescribeSecret"
                    )
                    Resource = "arn:aws:secretsmanager:$Region`:$accountId`:secret:$AppName/$Environment/*"
                }
            )
        } | ConvertTo-Json -Depth 10 -Compress
        
        $secretsPolicyFile = "$env:TEMP\ecs-secrets-policy.json"
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($secretsPolicyFile, $secretsPolicy, $utf8NoBom)
        Invoke-AwsCli iam put-role-policy --role-name $TaskRoleName --policy-name SecretsManagerPolicy --policy-document "file://$secretsPolicyFile" | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Failed to attach Secrets Manager policy. You may need to attach it manually."
        }
        
        Write-Success "Created Task Role: $TaskRoleArn"
    } catch {
        Write-Error "Failed to create Task Role: $_"
        Write-Error "In AWS Organizations, you may need permissions or SCPs that allow role creation."
        Write-Error "You can create the role manually or ask your AWS admin to create it."
        exit 1
    }
}

# ============================================
# 5. Create RDS Database
# ============================================
Write-Info "[5/10] Creating RDS PostgreSQL database..."

# RDS in a VPC requires a DB subnet group
$DbSubnetGroupName = "$AppName-$Environment-db-subnet"
$existingSubnetGroup = Invoke-AwsCli rds describe-db-subnet-groups --db-subnet-group-name $DbSubnetGroupName --region $Region 2>$null
if (-not $existingSubnetGroup) {
    Write-Info "Creating DB subnet group: $DbSubnetGroupName"
    $subnetGroupArgs = @(
        "rds", "create-db-subnet-group",
        "--db-subnet-group-name", $DbSubnetGroupName,
        "--db-subnet-group-description", "Subnet group for $AppName RDS",
        "--subnet-ids", $PublicSubnet1Id, $PublicSubnet2Id,
        "--region", $Region
    )
    Invoke-AwsCli @subnetGroupArgs | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create DB subnet group."
        Invoke-AwsCliShowError @subnetGroupArgs | Out-Host
        exit 1
    }
    Write-Success "Created DB subnet group: $DbSubnetGroupName"
}

# Prefer PostgreSQL 17.4; if 17.x not available use 16.8
$pgVersion = "16.8"
try {
    $pgVersionOutput = Invoke-AwsCli rds describe-db-engine-versions --engine postgres --region $Region --query "DBEngineVersions[*].EngineVersion" --output text 2>$null
    if ($pgVersionOutput) {
        $allVers = @($pgVersionOutput -split "`t" | ForEach-Object { $_.Trim() } | Where-Object { $_ })
        $v17 = @($allVers | Where-Object { $_ -match '^17\.' })
        $v16 = @($allVers | Where-Object { $_ -match '^16\.' })
        if ($v17.Count -gt 0 -and "17.4" -in $v17) {
            $pgVersion = "17.4"
        } elseif ($v17.Count -gt 0) {
            $pgVersion = $v17[0]
        } elseif ($v16.Count -gt 0 -and "16.8" -in $v16) {
            $pgVersion = "16.8"
        } elseif ($v16.Count -gt 0) {
            $pgVersion = $v16[0]
        }
    }
} catch {
    # Use default 16.8 if discovery fails
}
Write-Info "Using PostgreSQL engine version: $pgVersion"

$existingDb = Invoke-AwsCli rds describe-db-instances --db-instance-identifier $DBInstanceIdentifier --region $Region 2>$null
if ($existingDb) {
    Write-Warning "RDS instance already exists: $DBInstanceIdentifier"
    $DBEndpoint = (Invoke-AwsCli rds describe-db-instances --db-instance-identifier $DBInstanceIdentifier --query "DBInstances[0].Endpoint.Address" --output text --region $Region)
} else {
    Write-Info "Creating RDS instance (this may take 5-10 minutes)..."
    $rdsArgs = @(
        "rds", "create-db-instance",
        "--db-instance-identifier", $DBInstanceIdentifier,
        "--db-instance-class", $DBInstanceClass,
        "--engine", "postgres",
        "--engine-version", $pgVersion,
        "--master-username", $DBUsername,
        "--master-user-password", $DBPassword,
        "--allocated-storage", "20",
        "--storage-type", "gp2",
        "--db-name", $DBName,
        "--vpc-security-group-ids", $RdsSecurityGroupId,
        "--db-subnet-group-name", $DbSubnetGroupName,
        "--backup-retention-period", "7",
        "--publicly-accessible",
        "--region", $Region
    )
    Invoke-AwsCli @rdsArgs | Out-Null
    $rdsExitCode = $LASTEXITCODE
    if ($rdsExitCode -ne 0) {
        Write-Error "RDS create-db-instance failed (exit code $rdsExitCode). AWS error output below:"
        Invoke-AwsCliShowError @rdsArgs | Out-Host
        exit 1
    }
    
    Write-Info "Waiting for RDS instance to be available..."
    Invoke-AwsCli rds wait db-instance-available --db-instance-identifier $DBInstanceIdentifier --region $Region
    if ($LASTEXITCODE -ne 0) {
        Write-Error "RDS wait failed. Check the instance in the AWS console."
        exit 1
    }
    
    $DBEndpoint = (Invoke-AwsCli rds describe-db-instances --db-instance-identifier $DBInstanceIdentifier --query "DBInstances[0].Endpoint.Address" --output text --region $Region)
    Write-Success "RDS instance created: $DBEndpoint"
}

$DatabaseUrl = "postgresql://${DBUsername}:${DBPassword}@${DBEndpoint}:5432/${DBName}?sslmode=require"

# ============================================
# 6. Create Secrets Manager Secrets
# ============================================
Write-Info "[6/10] Creating Secrets Manager secrets..."

# Database URL Secret
$DbSecretName = "$AppName/$Environment/DATABASE_URL"
try {
    $existingDbSecret = Invoke-AwsCli secretsmanager describe-secret --secret-id $DbSecretName --region $Region 2>$null
    Write-Warning "Secret already exists: $DbSecretName"
    Invoke-AwsCli secretsmanager update-secret --secret-id $DbSecretName --secret-string $DatabaseUrl --region $Region | Out-Null
} catch {
    Invoke-AwsCli secretsmanager create-secret --name $DbSecretName --secret-string $DatabaseUrl --region $Region | Out-Null
    Write-Success "Created secret: $DbSecretName"
}

# SECRET_KEY Secret
$SecretKeyName = "$AppName/$Environment/SECRET_KEY"
try {
    $existingKeySecret = Invoke-AwsCli secretsmanager describe-secret --secret-id $SecretKeyName --region $Region 2>$null
    Write-Warning "Secret already exists: $SecretKeyName"
    Invoke-AwsCli secretsmanager update-secret --secret-id $SecretKeyName --secret-string $SecretKey --region $Region | Out-Null
} catch {
    Invoke-AwsCli secretsmanager create-secret --name $SecretKeyName --secret-string $SecretKey --region $Region | Out-Null
    Write-Success "Created secret: $SecretKeyName"
}

# ============================================
# 7. Create ECR Repository
# ============================================
Write-Info "[7/10] Creating ECR repository..."
$existingRepo = Invoke-AwsCli ecr describe-repositories --repository-names $ECRRepoName --region $Region 2>$null
$ecrCreateExit = $LASTEXITCODE
if ($ecrCreateExit -ne 0 -or -not $existingRepo) {
    Invoke-AwsCli ecr create-repository --repository-name $ECRRepoName --region $Region --image-scanning-configuration scanOnPush=true | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Created ECR repository: $ECRRepoName"
    } else {
        Write-Error "Failed to create ECR repository: $ECRRepoName"
        exit 1
    }
} else {
    Write-Warning "ECR repository already exists: $ECRRepoName"
}

$ECRRepoUri = "$accountId.dkr.ecr.$Region.amazonaws.com/$ECRRepoName"

# ============================================
# 8. Build and Push Docker Image
# ============================================
if (-not $SkipBuild) {
    Write-Info "[8/10] Building and pushing Docker image..."
    
    # Check Docker is running before trying to use it
    $null = cmd /c "docker info 2>nul"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker is not running or not installed."
        Write-Error "  - Start Docker Desktop (or your Docker daemon), then re-run this script."
        Write-Error "  - Or re-run with -SkipBuild to skip build/push (build the image later or from CI)."
        exit 1
    }
    
    # Login to ECR
    Write-Info "Logging into ECR..."
    $ecrLogin = Invoke-AwsCli ecr get-login-password --region $Region | docker login --username AWS --password-stdin $ECRRepoUri
    if ($LASTEXITCODE -ne 0) {
        Write-Error "ECR login failed. Make sure Docker is running."
        exit 1
    }
    
    # Build image
    Write-Info "Building Docker image..."
    $imageTag = "$ECRRepoUri`:latest"
    docker build -f deploy/Dockerfile -t $imageTag .
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker build failed."
        Write-Error "If the error was 'cannot find the file specified' or 'pipe/dockerDesktopLinuxEngine', start Docker Desktop and re-run."
        exit 1
    }
    
    # Ensure ECR repository exists before push (in case step 7 was skipped or failed)
    $repoCheck = Invoke-AwsCli ecr describe-repositories --repository-names $ECRRepoName --region $Region 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Info "Creating ECR repository $ECRRepoName before push..."
        Invoke-AwsCli ecr create-repository --repository-name $ECRRepoName --region $Region --image-scanning-configuration scanOnPush=true | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to create ECR repository. Cannot push image."
            exit 1
        }
    }
    
    # Push image
    Write-Info "Pushing Docker image to ECR..."
    docker push $imageTag
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker push failed."
        exit 1
    }
    
    Write-Success "Image pushed: $imageTag"
} else {
    Write-Warning "[8/10] Skipping Docker build (use -SkipBuild to skip)"
}

# ============================================
# 9. Create Application Load Balancer
# ============================================
Write-Info "[9/10] Creating Application Load Balancer..."

$existingAlb = Invoke-AwsCli elbv2 describe-load-balancers --names $ALBName --region $Region 2>$null
if ($existingAlb) {
    $AlbArn = (Invoke-AwsCli elbv2 describe-load-balancers --names $ALBName --query "LoadBalancers[0].LoadBalancerArn" --output text --region $Region)
    $AlbDnsName = (Invoke-AwsCli elbv2 describe-load-balancers --names $ALBName --query "LoadBalancers[0].DNSName" --output text --region $Region)
    Write-Warning "ALB already exists: $AlbArn"
} else {
    $AlbArn = (Invoke-AwsCli elbv2 create-load-balancer `
        --name $ALBName `
        --subnets $PublicSubnet1Id $PublicSubnet2Id `
        --security-groups $AlbSecurityGroupId `
        --scheme internet-facing `
        --type application `
        --region $Region `
        --query "LoadBalancers[0].LoadBalancerArn" --output text)
    
    $AlbDnsName = (Invoke-AwsCli elbv2 describe-load-balancers --load-balancer-arns $AlbArn --query "LoadBalancers[0].DNSName" --output text --region $Region)
    Write-Success "Created ALB: $AlbDnsName"
}

# Create Target Group
$TargetGroupName = "$AppName-$Environment-tg"
$existingTg = Invoke-AwsCli elbv2 describe-target-groups --names $TargetGroupName --region $Region 2>$null
if ($existingTg) {
    $TargetGroupArn = (Invoke-AwsCli elbv2 describe-target-groups --names $TargetGroupName --query "TargetGroups[0].TargetGroupArn" --output text --region $Region)
    Write-Warning "Target Group already exists: $TargetGroupArn"
} else {
    $TargetGroupArn = (Invoke-AwsCli elbv2 create-target-group `
        --name $TargetGroupName `
        --protocol HTTP `
        --port 8000 `
        --vpc-id $VpcId `
        --target-type ip `
        --health-check-path "/health/ready" `
        --health-check-protocol HTTP `
        --health-check-interval-seconds 30 `
        --health-check-timeout-seconds 5 `
        --healthy-threshold-count 2 `
        --unhealthy-threshold-count 3 `
        --region $Region `
        --query "TargetGroups[0].TargetGroupArn" --output text)
    
    Write-Success "Created Target Group: $TargetGroupArn"
}

# Create Listener
$existingListener = Invoke-AwsCli elbv2 describe-listeners --load-balancer-arn $AlbArn --region $Region --query "Listeners[?Port==`80`].ListenerArn" --output text 2>$null
if ($existingListener -and $existingListener -ne "None") {
    Write-Warning "HTTP listener already exists"
} else {
    $listenerArgs = @(
        "elbv2", "create-listener",
        "--load-balancer-arn", $AlbArn,
        "--protocol", "HTTP",
        "--port", "80",
        "--default-actions", "Type=forward,TargetGroupArn=$TargetGroupArn",
        "--region", $Region
    )
    Invoke-AwsCli @listenerArgs | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Created HTTP listener"
    } else {
        Write-Warning "Failed to create listener (may already exist or ALB not ready)"
    }
}

# ============================================
# 10. Create ECS Cluster and Service
# ============================================
Write-Info "[10/10] Creating ECS cluster and service..."

# Create Cluster
try {
    Invoke-AwsCli ecs create-cluster --cluster-name $ClusterName --region $Region | Out-Null
    Write-Success "Created ECS cluster: $ClusterName"
} catch {
    Write-Warning "ECS cluster may already exist"
}

# Create Task Definition
$TaskDefFile = "$env:TEMP\task-definition.json"
$taskDefinition = @{
    family = $TaskFamily
    networkMode = "awsvpc"
    requiresCompatibilities = @("FARGATE")
    cpu = "512"
    memory = "1024"
    executionRoleArn = $TaskExecutionRoleArn
    taskRoleArn = $TaskRoleArn
    containerDefinitions = @(
        @{
            name = "app"
            image = "$ECRRepoUri`:latest"
            essential = $true
            portMappings = @(
                @{
                    containerPort = 8000
                    protocol = "tcp"
                }
            )
            environment = @(
                @{
                    name = "CORS_ORIGINS"
                    value = '["http://' + $AlbDnsName + '"]'
                }
                @{
                    name = "ENABLE_SCHEDULER"
                    value = "true"
                }
                @{
                    name = "NODE_ENV"
                    value = "production"
                }
            )
            secrets = @(
                @{
                    name = "DATABASE_URL"
                    valueFrom = "arn:aws:secretsmanager:$Region`:$accountId`:secret:$DbSecretName"
                }
                @{
                    name = "SECRET_KEY"
                    valueFrom = "arn:aws:secretsmanager:$Region`:$accountId`:secret:$SecretKeyName"
                }
            )
            logConfiguration = @{
                logDriver = "awslogs"
                options = @{
                    "awslogs-group" = $LogGroupName
                    "awslogs-region" = $Region
                    "awslogs-stream-prefix" = "ecs"
                }
            }
            healthCheck = @{
                command = @("CMD-SHELL", "curl -f http://localhost:8000/health/ready || exit 1")
                interval = 30
                timeout = 5
                retries = 3
                startPeriod = 60
            }
        }
    )
} | ConvertTo-Json -Depth 10 -Compress

# Write UTF-8 without BOM for ECS task definition
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($TaskDefFile, $taskDefinition, $utf8NoBom)

Write-Info "Registering task definition..."
$TaskDefArn = (Invoke-AwsCli ecs register-task-definition --cli-input-json "file://$TaskDefFile" --region $Region --query "taskDefinition.taskDefinitionArn" --output text)
Write-Success "Registered task definition: $TaskDefArn"

# Create or Update Service
$existingService = Invoke-AwsCli ecs describe-services --cluster $ClusterName --services $ServiceName --region $Region --query "services[0].serviceName" --output text 2>$null
if ($existingService -and $existingService -ne "None" -and $existingService.Trim() -ne "") {
    Write-Info "Updating existing ECS service (using public subnets so tasks can reach Secrets Manager)..."
    $updateServiceArgs = @(
        "ecs", "update-service",
        "--cluster", $ClusterName,
        "--service", $ServiceName,
        "--task-definition", $TaskDefArn,
        "--network-configuration", "awsvpcConfiguration={subnets=[$SubnetIds],securityGroups=[$EcsSecurityGroupId],assignPublicIp=ENABLED}",
        "--force-new-deployment",
        "--region", $Region
    )
    Invoke-AwsCli @updateServiceArgs | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Updated ECS service: $ServiceName"
    } else {
        Write-Error "Failed to update ECS service."
        exit 1
    }
} else {
    Write-Info "Creating ECS service..."
    $createServiceArgs = @(
        "ecs", "create-service",
        "--cluster", $ClusterName,
        "--service-name", $ServiceName,
        "--task-definition", $TaskDefArn,
        "--desired-count", "1",
        "--launch-type", "FARGATE",
        "--network-configuration", "awsvpcConfiguration={subnets=[$SubnetIds],securityGroups=[$EcsSecurityGroupId],assignPublicIp=ENABLED}",
        "--load-balancers", "targetGroupArn=$TargetGroupArn,containerName=app,containerPort=8000",
        "--region", $Region
    )
    Invoke-AwsCli @createServiceArgs | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Created ECS service: $ServiceName"
    } else {
        Write-Error "Failed to create ECS service."
        Write-Error "Run the command manually to see the error:"
        Write-Error "aws ecs create-service --cluster $ClusterName --service-name $ServiceName --task-definition $TaskDefArn --desired-count 1 --launch-type FARGATE --network-configuration `"awsvpcConfiguration={subnets=[$SubnetIds],securityGroups=[$EcsSecurityGroupId],assignPublicIp=ENABLED}`" --load-balancers `"targetGroupArn=$TargetGroupArn,containerName=app,containerPort=8000`" --region $Region"
        exit 1
    }
}

# ============================================
# Summary
# ============================================
Write-Host ""
Write-Success "========================================="
Write-Success "Deployment Complete!"
Write-Success "========================================="
Write-Host ""
Write-Info "Application URL: http://$AlbDnsName"
Write-Info "ALB DNS: $AlbDnsName"
Write-Info "Database Endpoint: $DBEndpoint"
Write-Info "ECR Repository: $ECRRepoUri"
Write-Info "ECS Cluster: $ClusterName"
Write-Info "ECS Service: $ServiceName"
Write-Host ""
Write-Warning "Note: It may take 2-5 minutes for the ECS service to become healthy."
Write-Warning "Check service status: Invoke-AwsCli ecs describe-services --cluster $ClusterName --services $ServiceName --region $Region"
Write-Host ""
Write-Info "Next steps:"
Write-Info "1. Wait for ECS service to become healthy"
Write-Info "2. Initialize database: Run migrations from your local machine or via ECS exec"
Write-Info "3. Create admin user: Use backend/scripts/seed_admin.py"
Write-Host ""
