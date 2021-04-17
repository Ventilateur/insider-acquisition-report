##########################
# Provision RDS database #
##########################

resource "aws_db_instance" "sec" {
  allocated_storage         = 20
  apply_immediately         = true
  engine                    = "mysql"
  engine_version            = "8.0"
  instance_class            = "db.t2.micro"
  multi_az                  = false
  identifier                = var.rds_identifier
  name                      = var.tag_project_name
  username                  = var.db_username
  password                  = var.db_password
  snapshot_identifier       = var.db_from_snapshot
  final_snapshot_identifier = "${var.rds_identifier}-final-snapshot"
  publicly_accessible       = true
  db_subnet_group_name      = aws_db_subnet_group.sec.name
  vpc_security_group_ids    = [aws_security_group.sec.id]

  tags = {
    Name    = "${var.tag_project_name}_database"
    project = var.tag_project_name
  }
}


resource "null_resource" "db_setup" {
  depends_on = [
    aws_db_instance.sec,
    aws_db_subnet_group.sec
  ]

  provisioner "local-exec" {
    command = "docker run --rm -i mysql mysql -u${var.db_username} -p${var.db_password} -h ${aws_db_instance.sec.address} ${aws_db_instance.sec.name} < sql/initialize.sql"
  }
}


#############################################################
# Automatically start DB at 12h everyday and stop it at 15h #
#############################################################

locals {
  func_db = {
    start_db = {
      schedule_expr = "cron(0 12 * * ? *)"
    },
    stop_db = {
      schedule_expr = "cron(0 15 * * ? *)"
    }
  }
}

resource "aws_lambda_function" "db_start_stop" {
  for_each = local.func_db

  filename         = var.deployment_pkg
  function_name    = "${var.tag_project_name}_${each.key}"
  role             = aws_iam_role.infra_lambda.arn
  handler          = "${var.lambda_module}.${each.key}"
  source_code_hash = filebase64sha256(var.deployment_pkg)
  runtime          = "python3.8"
  timeout          = 10
  memory_size      = 128

  environment {
    variables = {
      DB_IDENTIFIER = aws_db_instance.sec.identifier
    }
  }

  tags = {
    Name    = "${var.tag_project_name}_${each.key}"
    project = var.tag_project_name
  }
}

resource "aws_cloudwatch_event_rule" "auto_start_stop_db" {
  for_each = local.func_db

  name                = "${var.tag_project_name}_auto_${each.key}"
  schedule_expression = each.value.schedule_expr

  tags = {
    Name    = "${var.tag_project_name}_${each.key}"
    project = var.tag_project_name
  }
}

resource "aws_cloudwatch_event_target" "db_start_stop" {
  for_each = local.func_db

  arn  = aws_lambda_function.db_start_stop[each.key].arn
  rule = aws_cloudwatch_event_rule.auto_start_stop_db[each.key].name
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  for_each = local.func_db

  statement_id  = "StartStopDBFromEvent"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.db_start_stop[each.key].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.auto_start_stop_db[each.key].arn
}


################################
# Emit an event when DB starts #
################################

resource "aws_cloudwatch_event_rule" "db_started" {
  name = "${var.tag_project_name}_db_started"

  event_pattern = jsonencode({
    source = ["aws.rds"]
    detail = {
      EventCategories = ["notification"]
      SourceType      = ["DB_INSTANCE"]
      SourceArn       = [aws_db_instance.sec.arn]
      EventID         = ["RDS-EVENT-0088"]
    }
  })

  tags = {
    Name    = "${var.tag_project_name}_db_started"
    project = var.tag_project_name
  }
}
