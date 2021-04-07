terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }

    null = {
      source  = "hashicorp/null"
      version = "~> 3.1"
    }
  }

  backend "s3" {
    key            = "sec4"
    dynamodb_table = "tf-backend-statelock-sec4"
  }
}

provider "aws" {}

provider "null" {}
