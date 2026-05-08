terraform {
  required_version = ">= 1.10, < 1.11"

  backend "s3" {
    bucket         = "clean-rock-tfstate-cb13"
    key            = "clean-rock/terraform.tfstate"
    region         = "us-east-2"
    profile        = "clean-rock-admin"
    encrypt        = true
    dynamodb_table = "clean-rock-tflocks"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
  }
}
