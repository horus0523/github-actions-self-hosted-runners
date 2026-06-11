variable "ami" {
  description = "AMI ID for the runner instance"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "subnet_id" {
  description = "Subnet ID for the runner instance"
  type        = string
}

variable "environment" {
  description = "Environment name (dev/staging/prod)"
  type        = string
  default     = "dev"
}

variable "allowed_ssh_cidr" {
  description = "CIDR blocks allowed for SSH access (use a real admin /32 in your tfvars)"
  type        = list(string)
  default     = ["203.0.113.10/32"]
}

variable "docker_daemon_allowed_cidr" {
  description = "CIDR blocks allowed to reach Docker TLS port 2376"
  type        = list(string)
  default     = ["203.0.113.10/32"]
}

variable "allow_bootstrap_http_egress" {
  description = "Temporarily allow outbound HTTP/80 for package mirrors that cannot use HTTPS during bootstrap"
  type        = bool
  default     = false
}

variable "runner_dns_egress_cidr_blocks" {
  description = "Explicit DNS resolver CIDRs for outbound TCP/UDP 53. Replace the TEST-NET placeholder in your tfvars before apply."
  type        = list(string)
  default     = ["203.0.113.53/32"]

  validation {
    condition = length(var.runner_dns_egress_cidr_blocks) > 0 && alltrue([
      for cidr in var.runner_dns_egress_cidr_blocks : can(cidrhost(cidr, 0))
    ])
    error_message = "runner_dns_egress_cidr_blocks must contain one or more valid CIDR blocks for your DNS resolvers."
  }
}

variable "runner_https_egress_cidr_blocks" {
  description = "Explicit outbound HTTPS CIDRs for GitHub, package registries, and APIs. Replace the TEST-NET placeholder in your tfvars before apply."
  type        = list(string)
  default     = ["203.0.113.0/24"]

  validation {
    condition = length(var.runner_https_egress_cidr_blocks) > 0 && alltrue([
      for cidr in var.runner_https_egress_cidr_blocks : can(cidrhost(cidr, 0))
    ])
    error_message = "runner_https_egress_cidr_blocks must contain one or more valid CIDR blocks for approved HTTPS destinations."
  }
}

variable "bootstrap_http_egress_cidr_blocks" {
  description = "Optional explicit HTTP/80 CIDRs used only when allow_bootstrap_http_egress=true. Replace the TEST-NET placeholder before enabling."
  type        = list(string)
  default     = ["203.0.113.80/32"]

  validation {
    condition = length(var.bootstrap_http_egress_cidr_blocks) > 0 && alltrue([
      for cidr in var.bootstrap_http_egress_cidr_blocks : can(cidrhost(cidr, 0))
    ])
    error_message = "bootstrap_http_egress_cidr_blocks must contain one or more valid CIDR blocks when HTTP bootstrap is enabled."
  }
}

variable "iam_role_name" {
  description = "IAM role name for the runner instance profile"
  type        = string
  default     = "github-runner-role"
}
