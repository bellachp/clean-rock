resource "aws_security_group" "app" {
  name        = "${var.project}-app"
  description = "Clean Rock app: home-IP ingress only"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTPS from home"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.home_ip]
  }

  ingress {
    description = "App port from home (uvicorn :8000 during bring-up)"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.home_ip]
  }

  ingress {
    description = "SSH from home"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.home_ip]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-app" }
}
