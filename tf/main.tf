locals {
  project_name = "sbobot"
  githubapp_function_name        = "${local.project_name}-github-app"
  gitlabwebhook_function_name        = "${local.project_name}-gitlab-webhook"
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
        },
        {
            "rulePriority": 3,
            "description": "Keep that last 2 git sha tagged images (last 2 merges to master).",
            "selection": {
                "tagStatus": "tagged",
                "tagPrefixList": ["gitlab-webhook-git"],
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

resource "aws_ssm_parameter" "accounts_data" {
  name        = "/${local.project_name}/github-app/env"
  description = "Env file for github bot"
  type        = "SecureString"
  tier        = "Intelligent-Tiering"
  value       = "[]"

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [value]
  }
}

resource "aws_ssm_parameter" "gitlab_webhook_env" {
  name        = "/${local.project_name}/gitlab-webhook/env"
  description = "Env file for gitlab webhook"
  type        = "SecureString"
  tier        = "Intelligent-Tiering"
  value       = "[]"

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [value]
  }
}

resource "aws_cloudwatch_log_group" "sbo_bot_github_app_lambda" {
  name              = "/aws/lambda/${local.project_name}-github-app"
  retention_in_days = 14
}

resource "aws_lambda_function" "githubapp_lambda" {
  function_name = local.githubapp_function_name
  description   = "sbo-bot github app"
  role          = aws_iam_role.iam_for_sbo_bot_lambda.arn

  package_type = "Image"
  image_uri    = "${aws_ecr_repository.sbo_bot.repository_url}:github-app-${var.docker_image_version}"

  timeout = 30

  publish = true

  architectures = ["arm64"]

  depends_on = [
    aws_cloudwatch_log_group.sbo_bot_github_app_lambda
  ]
}

resource "aws_lambda_alias" "current" {
  name        = "current"
  description = "Current version of lambda"

  depends_on = [aws_lambda_function.githubapp_lambda]

  function_name    = local.githubapp_function_name
  function_version = aws_lambda_function.githubapp_lambda.version
}

resource "aws_lambda_function_url" "github_app" {
  function_name      = aws_lambda_alias.current.arn
  authorization_type = "NONE"

  depends_on = [
    aws_lambda_function.githubapp_lambda
  ]
}


resource "aws_cloudwatch_log_group" "sbo_bot_gitlab_webhook_lambda" {
  name              = "/aws/lambda/${local.project_name}-gitlab-webhook"
  retention_in_days = 14
}

resource "aws_lambda_function" "gitlabwebhook_lambda" {
  function_name = local.gitlabwebhook_function_name
  description   = "sbo-bot gitlab webhook"
  role          = aws_iam_role.iam_for_sbo_bot_lambda.arn

  package_type = "Image"
  image_uri    = "${aws_ecr_repository.sbo_bot.repository_url}:gitlab-webhook-${var.docker_image_version}"

  timeout = 30

  publish = true

  architectures = ["arm64"]

  depends_on = [
    aws_cloudwatch_log_group.sbo_bot_gitlab_webhook_lambda
  ]
}

resource "aws_lambda_alias" "gitlab_current" {
  name        = "current"
  description = "Current version of lambda"

  depends_on = [aws_lambda_function.gitlabwebhook_lambda]

  function_name    = local.gitlabwebhook_function_name
  function_version = aws_lambda_function.gitlabwebhook_lambda.version
}

resource "aws_lambda_function_url" "gitlab_webhook" {
  function_name      = aws_lambda_alias.gitlab_current.arn
  authorization_type = "NONE"

  depends_on = [
    aws_lambda_function.gitlabwebhook_lambda
  ]
}
