variable "queue_name" {
  description = "Name of the SQS queue."
  type        = string
}

variable "fifo_queue" {
  description = "Whether the SQS queue uses FIFO ordering."
  type        = bool
  default     = false
}

variable "content_based_deduplication" {
  description = "Whether FIFO messages use content-based deduplication."
  type        = bool
  default     = false
}

variable "dead_letter_target_arn" {
  description = "ARN of the dead-letter queue."
  type        = string
  default     = null
}

variable "max_receive_count" {
  description = "Number of failed receives before a message moves to the dead-letter queue."
  type        = number
  default     = 3
}

variable "visibility_timeout_seconds" {
  description = "Time a received message remains invisible to other consumers."
  type        = number
  default     = 180
}
