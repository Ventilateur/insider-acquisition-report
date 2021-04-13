locals {
  rds_env_vars = {
    RDS_HOST     = var.db.host
    RDS_DB_NAME  = var.db.name
    RDS_USERNAME = var.db_username
    RDS_PASSWORD = var.db_password
  }

  lambda_functions = {
    pre_fetch = {
      timeout = 30
      memory = 128
      env_vars = local.rds_env_vars
      needs_vpc = true
    }
    fetch_metadata = {
      timeout = 30
      memory = 128
      env_vars = {}
      needs_vpc = false
    }
    fetch_data = {
      timeout = 300
      memory = 256
      env_vars = {}
      needs_vpc = false
    }
    save_data = {
      timeout = 300
      memory = 512
      env_vars = local.rds_env_vars
      needs_vpc = true
    }
    save_state = {
      timeout = 30
      memory = 128
      env_vars = local.rds_env_vars
      needs_vpc = true
    }
  }
}


resource "aws_lambda_function" "daywalker" {
  for_each = local.lambda_functions

  filename         = var.deployment_pkg
  function_name    = "${var.tag_project_name}_${each.key}"
  role             = aws_iam_role.lambda.arn
  handler          = "${var.lambda_module}.${each.key}"
  source_code_hash = filebase64sha256(var.deployment_pkg)
  runtime          = "python3.8"
  memory_size      = each.value.memory
  timeout          = each.value.timeout

  dynamic "environment" {
    for_each = length(each.value.env_vars) > 0 ? [1] : []
    content {
      variables = each.value.env_vars
    }
  }

  dynamic "vpc_config" {
    for_each = each.value.needs_vpc ? [1] : []
    content {
      security_group_ids = [var.network.security_group_id]
      subnet_ids = var.network.subnet_ids
    }
  }

  tags = {
    Name    = "${var.tag_project_name}_${each.key}"
    project = var.tag_project_name
  }
}
