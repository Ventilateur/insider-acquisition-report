data "aws_caller_identity" "current" {}


resource "aws_iam_role" "infra_lambda" {
  name = "sec_infra_lambda"

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
    Name    = "${var.tag_project_name} infra lambda role"
    project = var.tag_project_name
  }
}


resource "aws_iam_policy" "db_start_stop" {
  name = "db_start_stop"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "rds:StartDBInstance",
          "rds:StopDBInstance"
        ],
        Effect = "Allow"
        Resource = [
          "arn:aws:rds:*:${data.aws_caller_identity.current.account_id}:db:*",
        ]
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "policy_attachments" {
  count = 2

  role = aws_iam_role.infra_lambda.name
  policy_arn = [
    aws_iam_policy.db_start_stop.arn,
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  ][count.index]
}
