terraform {
  backend "s3" {
    key     = "application/terraform.tfstate"
    region  = "sa-east-1"
    encrypt = true
  }
}
