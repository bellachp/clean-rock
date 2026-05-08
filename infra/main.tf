# Sanity check that the provider is wired up correctly.
# Real resources start in subsequent files (vpc.tf, ec2.tf, site.tf, etc.).

data "aws_caller_identity" "current" {}

output "account_id" {
  value = data.aws_caller_identity.current.account_id
}

output "region" {
  value = var.aws_region
}
