resource "aws_security_group" "runner_sg" {
  name        = "github-runner-sg"
  description = "Security group for GitHub self-hosted runner"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidr
    description = "SSH from admin network only"
  }

  ingress {
    from_port   = 2376
    to_port     = 2376
    protocol    = "tcp"
    cidr_blocks = var.docker_daemon_allowed_cidr
    description = "Docker daemon TLS from trusted admin network only"
  }

  egress {
    from_port   = 53
    to_port     = 53
    protocol    = "udp"
    cidr_blocks = var.runner_dns_egress_cidr_blocks
    description = "DNS lookups"
  }

  egress {
    from_port   = 53
    to_port     = 53
    protocol    = "tcp"
    cidr_blocks = var.runner_dns_egress_cidr_blocks
    description = "DNS over TCP"
  }

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.runner_https_egress_cidr_blocks
    description = "HTTPS package, registry, and GitHub API traffic"
  }

  dynamic "egress" {
    for_each = var.allow_bootstrap_http_egress ? [1] : []

    content {
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = var.bootstrap_http_egress_cidr_blocks
      description = "Optional HTTP bootstrap traffic for explicit mirrors only"
    }
  }

  tags = {
    Name        = "github-runner-sg-${var.environment}"
    ManagedBy   = "terraform"
    Environment = var.environment
  }
}
