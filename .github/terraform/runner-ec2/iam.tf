data "aws_iam_policy" "github_actions_runner" {
  name = "GitHubActionsRunner managed policy"
}

resource "aws_iam_role" "runner" {
  name = "github-runner-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_instance_profile" "runner" {
  name = "github-runner-profile"
  role = aws_iam_role.runner.name
}

resource "aws_iam_role_policy_attachment" "runner" {
  role       = aws_iam_role.runner.name
  policy_arn = data.aws_iam_policy.github_actions_runner.arn
}
