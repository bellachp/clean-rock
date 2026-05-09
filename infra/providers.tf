provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  default_tags {
    tags = {
      Project   = "clean-rock"
      ManagedBy = "terraform"
    }
  }
}

# CloudFront requires ACM certs in us-east-1 regardless of where the
# distribution's other resources live.
provider "aws" {
  alias   = "us_east_1"
  region  = "us-east-1"
  profile = var.aws_profile

  default_tags {
    tags = {
      Project   = "clean-rock"
      ManagedBy = "terraform"
    }
  }
}
