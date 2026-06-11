output "instance_id" {
  description = "ID of the GitHub runner EC2 instance"
  value       = aws_instance.github_runner.id
}

output "public_ip" {
  description = "Public IP address of the runner instance"
  value       = aws_instance.github_runner.public_ip
}

output "private_ip" {
  description = "Private IP address of the runner instance"
  value       = aws_instance.github_runner.private_ip
}

output "security_group_id" {
  description = "Security group ID attached to the runner instance"
  value       = aws_security_group.runner_sg.id
}
