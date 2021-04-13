variable "db_username" {
  type = string
}

variable "db_password" {
  type = string
}

variable "db" {
  type = object({
    host=string,
    name=string,
    event_names=object({
      db_started=string
    })
  })
}

variable "network" {
  type = object({
    security_group_id=string,
    subnet_ids=list(string)
  })
}

variable "tag_project_name" {
  type    = string
  default = "sec4"
}

variable "deployment_pkg" {
  type    = string
  default = "sec4-pkg.zip"
}

variable "lambda_module" {
  type    = string
  default = "lambdas"
}

variable "rds_identifier" {
  type = string
  default = "sec-db"
}