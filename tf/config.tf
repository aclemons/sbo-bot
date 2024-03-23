terraform {
  backend "s3" {
    bucket  = "caffe-terraform"
    key     = "sbobot/terraform.tfstate"
    region  = "eu-central-1"
    encrypt = true

    dynamodb_table = "caffe-terraform"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.42.0"
    }
  }

  required_version = "1.7.5"
}

provider "aws" {
  region = "eu-central-1"

  default_tags {
    tags = {
      Project = "sbobot"
    }
  }
}
