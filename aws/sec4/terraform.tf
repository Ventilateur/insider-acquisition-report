terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.36"
    }
  }

  backend "s3" {
    key            = "sec/sec4"
    dynamodb_table = "tf-backend-statelock-sec4"
  }
}

provider "aws" {}
