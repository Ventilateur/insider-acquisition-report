############################################
# IAM role and policy for lambda functions #
############################################

locals {
  permission_names = {
    lambda = "${var.tag_project_name}_lambda"
    sfn    = "${var.tag_project_name}_sfn"
    event  = "${var.tag_project_name}_event"
  }
}

resource "aws_iam_role" "lambda" {
  name = local.permission_names.lambda

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
    Name    = local.permission_names.lambda
    project = var.tag_project_name
  }
}

resource "aws_iam_role_policy_attachment" "lambda" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  role       = aws_iam_role.lambda.name
}


###########################################################
# IAM role and policy for step function to invoke lambdas #
###########################################################

resource "aws_iam_role" "sfn" {
  name = local.permission_names.sfn

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
    Name    = local.permission_names.sfn
    project = var.tag_project_name
  }
}

resource "aws_iam_policy" "sfn" {
  name = local.permission_names.sfn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["lambda:InvokeFunction"]
        Effect   = "Allow"
        Resource = [for name in keys(local.lambda_functions) : aws_lambda_function.daywalker[name].arn]
      },
    ]
  })

  tags = {
    Name    = local.permission_names.sfn
    project = var.tag_project_name
  }
}

resource "aws_iam_role_policy_attachment" "sfn" {
  policy_arn = aws_iam_policy.sfn.arn
  role       = aws_iam_role.sfn.name
}


#####################################################################
# IAM role and policy for cloud watch event to invoke state machine #
#####################################################################

resource "aws_iam_role" "event" {
  name = local.permission_names.event

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      },
    ]
  })

  tags = {
    Name    = local.permission_names.event
    project = var.tag_project_name
  }
}

resource "aws_iam_policy" "event" {
  name = local.permission_names.event

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["states:StartExecution"]
        Effect   = "Allow"
        Resource = [aws_sfn_state_machine.daywalker.arn]
      },
    ]
  })

  tags = {
    Name    = local.permission_names.event
    project = var.tag_project_name
  }
}

resource "aws_iam_role_policy_attachment" "event" {
  policy_arn = aws_iam_policy.event.arn
  role       = aws_iam_role.event.name
}
