locals {
  project_name = "sbobot"
}

resource "aws_ecr_repository" "sbo_bot" {
  name                 = "${local.project_name}/bot"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "sbo_bot" {
  repository = aws_ecr_repository.sbo_bot.name

  policy = <<EOF
{
    "rules": [
        {
            "rulePriority": 1,
            "description": "Delete untagged images.",
            "selection": {
                "tagStatus": "untagged",
                "countType": "imageCountMoreThan",
                "countNumber": 1
            },
            "action": {
                "type": "expire"
            }
        },
        {
            "rulePriority": 2,
            "description": "Keep that last 2 git sha tagged images (last 2 merges to master).",
            "selection": {
                "tagStatus": "tagged",
                "tagPrefixList": ["github-app-git"],
                "countType": "imageCountMoreThan",
                "countNumber": 2
            },
            "action": {
                "type": "expire"
            }
        }
    ]
}
EOF
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_policy" "lambda_ssm_policy" {
  name        = "${local.project_name}-lambda-ssm-policy"
  description = "Policy to attach to ${local.project_name} lambdas for access to ssm."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
        ]
        Resource = [
          "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/${local.project_name}*"
        ]
      },
    ]
  })
}

resource "aws_iam_role" "iam_for_sbo_bot_lambda" {
  name               = "sbobot-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role_policy_attachment" "sbo_bot_lambda_basic_execution_role" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.iam_for_sbo_bot_lambda.id
}

resource "aws_iam_role_policy_attachment" "sbo_bot_lambda_insights_execution_role" {
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLambdaInsightsExecutionRolePolicy"
  role       = aws_iam_role.iam_for_sbo_bot_lambda.id
}

resource "aws_iam_role_policy_attachment" "sbo_bot_ssm" {
  policy_arn = aws_iam_policy.lambda_ssm_policy.arn
  role       = aws_iam_role.iam_for_sbo_bot_lambda.id
}

resource "aws_cloudwatch_log_group" "sbo_bot_lambda" {
  name              = "/aws/lambda/${local.project_name}"
  retention_in_days = 14
}
