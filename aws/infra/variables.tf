variable "self_ip" {
  type = string
}

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
  default = "infra-pkg.zip"
}

variable "lambda_module" {
  type    = string
  default = "lambda"
}

variable "rds_identifier" {
  type    = string
  default = "sec-db"
}