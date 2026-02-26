# Optional: register EC2 key pair "loan-engine-qa" so you can use loan-engine-qa.pem for SSH
# (e.g. for a bastion host or future EC2). QA app runs on ECS Fargate and does not use EC2 by default.
resource "aws_key_pair" "qa" {
  count = length(var.ec2_key_pair_public_key) > 0 ? 1 : 0

  key_name   = "loan-engine-qa"
  public_key = var.ec2_key_pair_public_key
  tags       = { Name = "loan-engine-qa" }
}
