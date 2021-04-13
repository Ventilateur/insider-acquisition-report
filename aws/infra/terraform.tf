terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.36"
    }

    null = {
      source  = "hashicorp/null"
      version = "~> 3.1"
    }
  }

  backend "s3" {
    key            = "sec/infra"
    dynamodb_table = "tf-backend-statelock-sec-infra"
  }
}

provider "aws" {}

provider "null" {}
