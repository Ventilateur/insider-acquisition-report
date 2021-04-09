locals {
  lambda_module = "scrape.lambda"
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
    variables = {
      RDS_HOST     = aws_db_instance.sec_db_instance.address
      RDS_USERNAME = var.db_username
      RDS_PASSWORD = var.db_password
      RDS_DB_NAME  = var.tag_project_name
    }
  }

  vpc_config {
    security_group_ids = [
    aws_security_group.sec_sg.id]
    subnet_ids = [
      aws_subnet.sec_sn_a.id,
      aws_subnet.sec_sn_b.id,
      aws_subnet.sec_sn_c.id
    ]
  }

  tags = {
    Name    = "sec4_save_data"
    project = var.tag_project_name
  }
}

resource "aws_sfn_state_machine" "sec4_daywalker" {
  definition = jsonencode({
    StartAt = "FetchMetadata"
    States = {
      FetchMetadata = {
        Type     = "Task"
        Resource = aws_lambda_function.sec4_fetch_metadata.arn
        Next     = "HasMetadata"
      },
      HasMetadata = {
        Type = "Choice",
        Choices = [
          {
            Variable  = "$.urls",
            IsPresent = true,
            Next      = "FetchAndSave"
          }
        ],
        Default = "Stop"
      },
      FetchAndSave = {
        Type      = "Map",
        ItemsPath = "$.urls",
        Parameters = {
          "urls.$" : "$$.Map.Item.Value",
          "date.$" : "$.date"
        },
        MaxConcurrency = 1,
        Iterator = {
          StartAt = "FetchData",
          States = {
            FetchData = {
              Type     = "Task",
              Resource = aws_lambda_function.sec4_fetch_data.arn,
              Next     = "SaveData"
            },
            SaveData = {
              Type     = "Task",
              Resource = aws_lambda_function.sec4_save_data.arn,
              End      = true
            }
          }
        },
        Next = "Stop"
      },
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
