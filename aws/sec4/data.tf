data "aws_lambda_function" "pre_fetch" {
  function_name = "pre_fetch"
}

data "aws_lambda_function" "fetch_metadata" {
  function_name = "fetch_metadata"
}

data "aws_lambda_function" "fetch_data" {
  function_name = "fetch_data"
}

data "aws_lambda_function" "save_data" {
  function_name = "save_data"
}

data "aws_lambda_function" "save_state" {
  function_name = "save_state"
}