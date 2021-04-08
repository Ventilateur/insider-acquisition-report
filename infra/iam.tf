resource "aws_iam_role" "sec-lambda-role" {
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
    Name = "${var.tag_project_name} lambda role"
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
          "arn:aws:rds:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:db:${local.rds_db_identifier}",
          "arn:aws:dynamodb:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:table/${local.sec4_dynamodb_table}"
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
  count = 2
  policy_arn = local.iam_policies_arns[count.index]
  role = aws_iam_role.sec-lambda-role.name
}
