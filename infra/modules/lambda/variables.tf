variable "function_name" {
  description = "Name of the Lambda function."
  type        = string
}

variable "image_uri" {
  description = "ECR image URI used by the Lambda function."
  type        = string
}

variable "environment_variables" {
  description = "Environment variables passed to the Lambda function."
  type        = map(string)
  default     = {}
}

variable "memory_size" {
  description = "Amount of memory available to the Lambda function in MB."
  type        = number
  default     = 128
}

variable "timeout" {
  description = "Maximum execution time of the Lambda function in seconds."
  type        = number
  default     = 30
}

variable "log_retention_in_days" {
  description = "Number of days CloudWatch logs are retained."
  type        = number
  default     = 7
}

variable "image_command" {
  description = "Optional command that overrides the image CMD."
  type        = list(string)
  default     = null
}
