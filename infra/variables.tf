variable "aws_region" {
  description = "AWS region for all workload resources"
  type        = string
  default     = "us-east-2"
}

variable "aws_profile" {
  description = "Local AWS CLI profile name"
  type        = string
  default     = "clean-rock-admin"
}

variable "project" {
  description = "Resource name prefix"
  type        = string
  default     = "clean-rock"
}

variable "name_suffix" {
  description = "Short suffix for globally-unique resource names (S3 buckets, etc.)"
  type        = string
  default     = "cb13"
}

variable "home_ip" {
  description = "Home IP as a /32 CIDR for SG ingress. Set in terraform.tfvars (gitignored)."
  type        = string
}

variable "ssh_public_key" {
  description = "SSH public key contents (e.g. cat ~/.ssh/clean-rock.pub). Set in terraform.tfvars."
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t4g.nano"
}
