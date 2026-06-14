locals {
  project_name              = "sbobot"
  githubapp_function_name   = "${local.project_name}-github-app"
  webhook_api_function_name = "${local.project_name}-webhook-api"

  github_admins = [
    "Ponce",
    "aclemons",
    "cwilling",
    "fourtysixand2",
    "sbo-bot[bot]",
    "willysr",
  ]

  github_contributors = [
    "ArTourter",
    "RezaT4795",
    "Ythogtha",
    "afhpayne",
    "andy5995",
    "antonioleal",
    "atelszewski",
    "bassmadrigal",
    "earies",
    "fsLeg",
    "isaackwy",
    "lecramyajiv",
    "linrs",
    "mac-a-r0ni",
    "maramon",
    "mattegger",
    "newHeiko",
    "perrin4869",
    "pghvlaans",
    "pyllyukko",
    "r1w1s1",
    "rizitis",
    "wkdjgf534",
  ]

  gitlab_admins = [
    "Ponce",
    "chris.willing",
    "clemonsa",
    "willysr",
  ]
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
                "tagPrefixList": ["webhook-api-git"],
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

resource "aws_ssm_parameter" "webhook_api_webhook_env" {
  name        = "/${local.project_name}/webhook-api/env"
  description = "Env file for webhook-api"
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

  environment {
    variables = {
      GITHUB_ADMINS       = join(",", local.github_admins)
      GITHUB_CONTRIBUTORS = join(",", local.github_contributors)
      WEBHOOK_PATH        = "/"
      LOG_LEVEL           = "info"
    }
  }

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


resource "aws_cloudwatch_log_group" "sbo_bot_webhook_api_lambda" {
  name              = "/aws/lambda/${local.project_name}-webhook-api"
  retention_in_days = 14
}

resource "aws_lambda_function" "webhook_api_lambda" {
  function_name = local.webhook_api_function_name
  description   = "sbo-bot webhook-api"
  role          = aws_iam_role.iam_for_sbo_bot_lambda.arn

  package_type = "Image"
  image_uri    = "${aws_ecr_repository.sbo_bot.repository_url}:webhook-api-${var.docker_image_version}"

  timeout = 30

  publish = true

  architectures = ["arm64"]

  environment {
    variables = {
      GITLAB_ADMINS = join(",", local.gitlab_admins)
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.sbo_bot_webhook_api_lambda
  ]
}

resource "aws_lambda_alias" "webhook_api_current" {
  name        = "current"
  description = "Current version of lambda"

  depends_on = [aws_lambda_function.webhook_api_lambda]

  function_name    = local.webhook_api_function_name
  function_version = aws_lambda_function.webhook_api_lambda.version
}

resource "aws_lambda_function_url" "webhook_api" {
  function_name      = aws_lambda_alias.webhook_api_current.arn
  authorization_type = "NONE"

  depends_on = [
    aws_lambda_function.webhook_api_lambda
  ]
}
