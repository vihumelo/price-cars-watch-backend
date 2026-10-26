data "aws_secretsmanager_secret" "mailjet" {
  name = "prices-car-watch/notifications/mailjet"
}

variable "notifications_image_uri" {
  description = "Full URI of the Notifications image to deploy."
  type        = string
}

variable "mailjet_confirmation_template_id" {
  description = "Mailjet template ID used for confirmation emails."
  type        = number
}

variable "mailjet_new_listings_template_id" {
  description = "Mailjet template ID used for new-listing emails."
  type        = number
}

variable "mailjet_sender_email" {
  description = "Verified Mailjet sender email address."
  type        = string
}

variable "mailjet_sender_name" {
  description = "Mailjet sender display name."
  type        = string
}

locals {
  notifications_environment = {
    EMAIL_PROVIDER                   = "mailjet"
    MAILJET_CONFIRMATION_TEMPLATE_ID = tostring(var.mailjet_confirmation_template_id)
    MAILJET_NEW_LISTINGS_TEMPLATE_ID = tostring(var.mailjet_new_listings_template_id)
    MAILJET_SECRET_NAME              = data.aws_secretsmanager_secret.mailjet.name
    MAILJET_SENDER_EMAIL             = var.mailjet_sender_email
    MAILJET_SENDER_NAME              = var.mailjet_sender_name
    POWERTOOLS_METRICS_NAMESPACE     = "PricesCarWatch"
    POWERTOOLS_SERVICE_NAME          = "notifications"
    PUBLIC_FRONTEND_BASE_URL         = var.frontend_base_url
  }
}

module "confirmation_email_lambda" {
  source = "../modules/lambda"

  function_name         = "prices-car-watch-confirmation-email"
  image_uri             = var.notifications_image_uri
  image_command         = ["services.notifications.src.handlers.confirmation_email.handler"]
  environment_variables = local.notifications_environment
}

resource "aws_iam_role_policy" "confirmation_email_lambda" {
  name = "notifications-confirmation-email-access"
  role = module.confirmation_email_lambda.execution_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ReceiveMessage",
        ]
        Resource = module.confirmation_email_queue.queue_arn
      },
      {
        Effect   = "Allow"
        Action   = "secretsmanager:GetSecretValue"
        Resource = data.aws_secretsmanager_secret.mailjet.arn
      },
    ]
  })
}

resource "aws_lambda_event_source_mapping" "confirmation_email" {
  event_source_arn        = module.confirmation_email_queue.queue_arn
  function_name           = module.confirmation_email_lambda.function_arn
  batch_size              = 1
  function_response_types = ["ReportBatchItemFailures"]
  enabled                 = true
  depends_on              = [aws_iam_role_policy.confirmation_email_lambda]
}

module "new_listings_email_lambda" {
  source = "../modules/lambda"

  function_name         = "prices-car-watch-notifications"
  image_uri             = var.notifications_image_uri
  image_command         = ["services.notifications.src.handlers.new_listings_email.handler"]
  environment_variables = local.notifications_environment
}

resource "aws_iam_role_policy" "new_listings_email_lambda" {
  name = "notifications-new-listings-email-access"
  role = module.new_listings_email_lambda.execution_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ReceiveMessage",
        ]
        Resource = module.new_listings_queue.queue_arn
      },
      {
        Effect   = "Allow"
        Action   = "secretsmanager:GetSecretValue"
        Resource = data.aws_secretsmanager_secret.mailjet.arn
      },
    ]
  })
}

resource "aws_lambda_event_source_mapping" "new_listings_email" {
  event_source_arn        = module.new_listings_queue.queue_arn
  function_name           = module.new_listings_email_lambda.function_arn
  batch_size              = 1
  function_response_types = ["ReportBatchItemFailures"]
  enabled                 = true
  depends_on              = [aws_iam_role_policy.new_listings_email_lambda]
}
