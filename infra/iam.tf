resource "aws_iam_role" "sec4_lambda" {
  name = "sec-lambda-role-test"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })

  tags = {
    Name    = "${var.tag_project_name} lambda role"
    project = var.tag_project_name
  }
}

resource "aws_iam_policy" "sec-lambda-db-policy" {
  name = "sec-lambda-db-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:UpdateItem",
          "rds:StartDBInstance",
          "rds:StopDBInstance"
        ],
        Effect = "Allow"
        Resource = [
          "arn:aws:rds:*:${data.aws_caller_identity.current.account_id}:db:*",
          "arn:aws:dynamodb:*:${data.aws_caller_identity.current.account_id}:table/*"
        ]
      },
    ]
  })
}

locals {
  iam_policies_arns = [
    aws_iam_policy.sec-lambda-db-policy.arn,
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  ]
}

resource "aws_iam_role_policy_attachment" "policy_attachments" {
  count      = 2
  policy_arn = local.iam_policies_arns[count.index]
  role       = aws_iam_role.sec4_lambda.name
}

resource "aws_iam_role" "sec4_sfn" {
  name = "sec4_sfn_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      },
    ]
  })

  tags = {
    Name    = "SEC4 sfn role"
    project = var.tag_project_name
  }
}

resource "aws_iam_policy" "sec4_sfn" {
  name = "sec4_sfn_policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = ["lambda:InvokeFunction"]
        Effect = "Allow"
        Resource = [
          aws_lambda_function.sec4_fetch_metadata.arn,
          aws_lambda_function.sec4_fetch_data.arn,
          aws_lambda_function.sec4_save_data.arn,
        ]
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "sec4_sfn" {
  policy_arn = aws_iam_policy.sec4_sfn.arn
  role       = aws_iam_role.sec4_sfn.name
}
