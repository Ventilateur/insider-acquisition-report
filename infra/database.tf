resource "aws_db_instance" "sec_db_instance" {
  allocated_storage         = 20
  apply_immediately         = true
  engine                    = "mysql"
  engine_version            = "8.0"
  instance_class            = "db.t2.micro"
  multi_az                  = false
  identifier                = local.rds_db_identifier
  name                      = var.tag_project_name
  username                  = var.db_username
  password                  = var.db_password
  snapshot_identifier       = var.db_from_snapshot
  final_snapshot_identifier = "${local.rds_db_identifier}_final_snapshot"
  publicly_accessible       = true
  db_subnet_group_name      = aws_db_subnet_group.sec_db_sng.name
  vpc_security_group_ids    = [aws_security_group.sec_sg.id]

  tags = {
    Name    = "${var.tag_project_name} database"
    project = var.tag_project_name
  }
}


resource "null_resource" "db_setup" {
  depends_on = [
    aws_db_instance.sec_db_instance,
    aws_db_subnet_group.sec_db_sng
  ]

  provisioner "local-exec" {
    command = "docker run --rm -i mysql mysql -u${var.db_username} -p${var.db_password} -h ${aws_db_instance.sec_db_instance.address} ${aws_db_instance.sec_db_instance.name} < sql/initialize.sql"
  }
}


resource "aws_dynamodb_table" "sec4_states" {
  hash_key       = "State"
  name           = local.sec4_dynamodb_table
  read_capacity  = 1
  write_capacity = 1

  attribute {
    name = "State"
    type = "S"
  }

  tags = {
    Name    = "${var.tag_project_name} states"
    project = var.tag_project_name
  }
}


locals {
  db_start_stop = [
    {
      name = "start_db"
      schedule_expr =  "cron(0 17 * * ? *)"
    },
    {
      name = "stop_db"
      schedule_expr =  "cron(0 20 * * ? *)"
    }
  ]
}


resource "aws_lambda_function" "db_start_stop" {
  count = 2

  filename         = var.deployment_pkg
  function_name    = "sec_${local.db_start_stop[count.index].name}"
  role             = aws_iam_role.sec4_lambda.arn
  handler          = "${local.lambda_module}.${local.db_start_stop[count.index].name}"
  source_code_hash = filebase64sha256(var.deployment_pkg)
  runtime          = "python3.8"
  timeout          = 10
  memory_size      = 128

  tags = {
    Name    = "sec_${local.db_start_stop[count.index]}"
    project = var.tag_project_name
  }
}


resource "aws_cloudwatch_event_rule" "auto_start_stop_db" {
  count = 2

  name = "sec_auto_${local.db_start_stop[count.index].name}"
  schedule_expression = local.db_start_stop[count.index].schedule_expr
}


resource "aws_cloudwatch_event_target" "db_start_stop" {
  count = 2

  arn = aws_lambda_function.db_start_stop[count.index].arn
  rule = aws_cloudwatch_event_rule.auto_start_stop_db[count.index].name
}
