resource "aws_sfn_state_machine" "daywalker" {
  definition = jsonencode({
    StartAt = "PreFetch"
    States = {
      PreFetch = {
        Type     = "Task"
        Resource = aws_lambda_function.daywalker["pre_fetch"].arn
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
        Resource = aws_lambda_function.daywalker["fetch_metadata"].arn
        Next     = "FetchAndSave"
      },
      FetchAndSave = {
        Type      = "Map",
        ItemsPath = "$.urls"
        ResultPath = null
        Parameters = {
          "date.$" : "$.date"
          "urls.$" : "$$.Map.Item.Value"
        },
        MaxConcurrency = 1,
        Catch = [
          {
            ErrorEquals = ["States.ALL"],
            ResultPath  = "$.error"
            Next        = "SaveState"
          }
        ]
        Iterator = {
          StartAt = "FetchData"
          States = {
            FetchData = {
              Type     = "Task"
              Resource = aws_lambda_function.daywalker["fetch_data"].arn
              Next     = "SaveData"
            },
            SaveData = {
              Type     = "Task"
              Resource = aws_lambda_function.daywalker["save_data"].arn
              End      = true
            }
          }
        },
        Next = "SaveState"
      },
      SaveState = {
        Type     = "Task"
        Resource = aws_lambda_function.daywalker["save_state"].arn
        Next     = "Stop"
      }
      Stop = {
        Type = "Succeed"
      }
    }
  })

  name     = "${var.tag_project_name}_daywalker"
  role_arn = aws_iam_role.sfn.arn

  tags = {
    Name    = "${var.tag_project_name}_daywalker"
    project = var.tag_project_name
  }
}


# Invoke state machine whenever DB starts
resource "aws_cloudwatch_event_target" "daywalker" {
  arn      = aws_sfn_state_machine.daywalker.arn
  rule     = var.db.event_names.db_started
  role_arn = aws_iam_role.event.arn
}
