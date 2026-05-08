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
