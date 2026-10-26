terraform {
  backend "s3" {
    key     = "ecr/terraform.tfstate"
    region  = "sa-east-1"
    encrypt = true
  }
}
