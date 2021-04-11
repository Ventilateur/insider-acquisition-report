locals {
  lambda_module = "scrape.lambda"
  lambda_vpc_subnets = [
    aws_subnet.sec_sn_a.id,
    aws_subnet.sec_sn_b.id,
    aws_subnet.sec_sn_c.id
  ]
  rds_env_vars = {
    RDS_HOST     = aws_db_instance.sec_db_instance.address
    RDS_USERNAME = var.db_username
    RDS_PASSWORD = var.db_password
    RDS_DB_NAME  = var.tag_project_name
  }
}


resource "aws_lambda_function" "sec4_pre_fetch" {
  filename         = var.deployment_pkg
  function_name    = "sec4_pre_fetch"
  role             = aws_iam_role.sec4_lambda.arn
  handler          = "${local.lambda_module}.pre_fetch"
  source_code_hash = filebase64sha256(var.deployment_pkg)
  runtime          = "python3.8"
  timeout          = 30

  environment {
    variables = local.rds_env_vars
  }

  vpc_config {
    security_group_ids = [
    aws_security_group.sec_sg.id]
    subnet_ids = local.lambda_vpc_subnets
  }

  tags = {
    Name    = "sec4_pre_fetch"
    project = var.tag_project_name
  }
}


resource "aws_lambda_function" "sec4_fetch_metadata" {
  filename         = var.deployment_pkg
  function_name    = "sec4_fetch_metadata"
  role             = aws_iam_role.sec4_lambda.arn
  handler          = "${local.lambda_module}.fetch_metadata"
  source_code_hash = filebase64sha256(var.deployment_pkg)
  runtime          = "python3.8"
  timeout          = 30

  tags = {
    Name    = "sec4_fetch_metadata"
    project = var.tag_project_name
  }
}


resource "aws_lambda_function" "sec4_fetch_data" {
  filename         = var.deployment_pkg
  function_name    = "sec4_fetch_data"
  role             = aws_iam_role.sec4_lambda.arn
  handler          = "${local.lambda_module}.fetch_data"
  source_code_hash = filebase64sha256(var.deployment_pkg)
  runtime          = "python3.8"
  timeout          = 300
  memory_size      = 512

  tags = {
    Name    = "sec4_fetch_data"
    project = var.tag_project_name
  }
}


resource "aws_lambda_function" "sec4_save_data" {
  filename         = var.deployment_pkg
  function_name    = "sec4_save_data"
  role             = aws_iam_role.sec4_lambda.arn
  handler          = "${local.lambda_module}.save_data"
  source_code_hash = filebase64sha256(var.deployment_pkg)
  runtime          = "python3.8"
  timeout          = 300
  memory_size      = 512

  environment {
    variables = local.rds_env_vars
  }

  vpc_config {
    security_group_ids = [
    aws_security_group.sec_sg.id]
    subnet_ids = local.lambda_vpc_subnets
  }

  tags = {
    Name    = "sec4_save_data"
    project = var.tag_project_name
  }
}


resource "aws_lambda_function" "sec4_save_state" {
  filename         = var.deployment_pkg
  function_name    = "sec4_save_state"
  role             = aws_iam_role.sec4_lambda.arn
  handler          = "${local.lambda_module}.save_state"
  source_code_hash = filebase64sha256(var.deployment_pkg)
  runtime          = "python3.8"
  timeout          = 30

  environment {
    variables = local.rds_env_vars
  }

  vpc_config {
    security_group_ids = [
    aws_security_group.sec_sg.id]
    subnet_ids = local.lambda_vpc_subnets
  }

  tags = {
    Name    = "sec4_save_state"
    project = var.tag_project_name
  }
}


resource "aws_sfn_state_machine" "sec4_daywalker" {
  definition = jsonencode({
    StartAt = "PreFetch"
    States = {
      PreFetch = {
        Type     = "Task"
        Resource = aws_lambda_function.sec4_fetch_metadata.arn
        Next     = "ShouldProceed"
      },
      ShouldProceed = {
        Type = "Choice"
        Choices = [
          {
            Variable      = "$.proceed"
            BooleanEquals = true
            Next          = "FetchMetadata"
          }
        ],
        Default = "Stop"
      },
      FetchMetadata = {
        Type     = "Task"
        Resource = aws_lambda_function.sec4_fetch_metadata.arn
        Next     = "FetchAndSave"
      },
      FetchAndSave = {
        Type      = "Map",
        ItemsPath = "$.urls"
        Parameters = {
          "date.$" : "$.date"
          "urls.$" : "$$.Map.Item.Value"
        },
        MaxConcurrency = 1,
        Iterator = {
          StartAt = "FetchData"
          States = {
            FetchData = {
              Type     = "Task"
              Resource = aws_lambda_function.sec4_fetch_data.arn
              Catch = [
                {
                  ErrorEquals = ["States.ALL"],
                  ResultPath  = "$.error"
                  Next        = "SaveState"
                }
              ]
              Next = "SaveData"
            },
            SaveData = {
              Type     = "Task"
              Resource = aws_lambda_function.sec4_save_data.arn
              Catch = [
                {
                  ErrorEquals = ["States.ALL"],
                  ResultPath  = "$.error"
                  Next        = "SaveState"
                }
              ]
              End = true
            }
          }
        },
        Next = "Stop"
      },
      SaveState = {
        Type     = "Task"
        Resource = aws_lambda_function.sec4_save_state.arn
        Next     = "Stop"
      }
      Stop = {
        Type = "Succeed"
      }
    }
  })

  name     = "sec4_daywalker"
  role_arn = aws_iam_role.sec4_sfn.arn

  tags = {
    Name    = "sec4_daywalker"
    project = var.tag_project_name
  }
}


resource "aws_cloudwatch_event_rule" "daywalker" {
  name = "sec4_daywalker"

  event_pattern = jsonencode({
    source = [
    "aws.rds"]
    detail = {
      EventCategories = [
      "notification"]
      SourceType = [
      "DB_INSTANCE"]
      SourceArn = [
      aws_db_instance.sec_db_instance.arn]
      EventID = [
      "RDS-EVENT-0088"]
    }
  })

  tags = {
    Name    = "sec4_daywalker"
    project = var.tag_project_name
  }
}


resource "aws_cloudwatch_event_target" "daywalker" {
  arn      = aws_sfn_state_machine.sec4_daywalker.arn
  rule     = aws_cloudwatch_event_rule.daywalker.name
  role_arn = aws_iam_role.events_invokes_sfn.arn
}