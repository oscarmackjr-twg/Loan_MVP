
$Region = "us-east-1"
$AccountId = aws sts get-caller-identity --query Account --output text
$ECRUri = "$AccountId.dkr.ecr.$Region.amazonaws.com/loan-engine"
$Tag = "${ECRUri}:latest"