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
      version = "6.56.0"
    }
  }

  required_version = "1.12.5"
}

provider "aws" {
  region = "eu-central-1"

  default_tags {
    tags = {
      Project = "sbobot"
    }
  }
}
