variable "db_username" {
  type = string
}

variable "db_password" {
  type = string
}

variable "db_from_snapshot" {
  type    = string
  default = null
}

variable "tag_project_name" {
  type    = string
  default = "sec"
}

variable "deployment_pkg" {
  type    = string
  default = "deployment-pkg.zip"
}

locals {
  rds_db_identifier   = "sec-db"
  sec4_dynamodb_table = "SEC4States"
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}