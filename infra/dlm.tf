resource "aws_iam_role" "dlm" {
  name = "${var.project}-dlm"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "dlm.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "dlm" {
  role       = aws_iam_role.dlm.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSDataLifecycleManagerServiceRole"
}

resource "aws_dlm_lifecycle_policy" "ebs_daily" {
  description        = "${var.project} daily EBS snapshots 7-day retention"
  execution_role_arn = aws_iam_role.dlm.arn
  state              = "ENABLED"

  policy_details {
    resource_types = ["INSTANCE"]

    target_tags = {
      Snapshot = "true"
    }

    schedule {
      name      = "daily-1pm-eastern"
      copy_tags = true

      create_rule {
        interval      = 24
        interval_unit = "HOURS"
        times         = ["18:00"] # 1pm EST / 2pm EDT
      }

      retain_rule {
        count = 7
      }
    }
  }
}
