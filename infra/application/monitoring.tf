variable "monitoring_image_uri" {
  description = "Full URI of the Monitoring image to deploy."
  type        = string
}

module "monitoring_lambda" {
  source = "../modules/lambda"

  function_name = "prices-car-watch-monitoring"
  image_uri     = var.monitoring_image_uri

  environment_variables = {
    NEW_LISTINGS_QUEUE_URL         = module.new_listings_queue.queue_url
    POWERTOOLS_METRICS_NAMESPACE   = "PricesCarWatch"
    POWERTOOLS_SERVICE_NAME        = "monitoring"
    SUBSCRIPTIONS_SERVICE_BASE_URL = aws_apigatewayv2_api.prices_car_watch.api_endpoint
    VEHICLES_SERVICE_BASE_URL      = aws_apigatewayv2_api.prices_car_watch.api_endpoint
  }
}

resource "aws_iam_role_policy" "monitoring_lambda" {
  name = "monitoring-service-access"
  role = module.monitoring_lambda.execution_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "execute-api:Invoke"
        Resource = [
          "${aws_apigatewayv2_api.prices_car_watch.execution_arn}/*/GET/internal/subscriptions/monitoring",
          "${aws_apigatewayv2_api.prices_car_watch.execution_arn}/*/PATCH/internal/subscriptions/*/listings",
          "${aws_apigatewayv2_api.prices_car_watch.execution_arn}/*/POST/internal/vehicles/listings",
        ]
      },
      {
        Effect   = "Allow"
        Action   = "sqs:SendMessage"
        Resource = module.new_listings_queue.queue_arn
      },
    ]
  })
}

resource "aws_iam_role" "monitoring_scheduler" {
  name = "prices-car-watch-monitoring-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "sts:AssumeRole"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role_policy" "monitoring_scheduler" {
  name = "monitoring-scheduler-invoke"
  role = aws_iam_role.monitoring_scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = module.monitoring_lambda.function_arn
      },
    ]
  })
}

resource "aws_scheduler_schedule" "monitoring" {
  name                = "prices-car-watch-monitoring"
  schedule_expression = "rate(4 hours)"
  state               = "ENABLED"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = module.monitoring_lambda.function_arn
    role_arn = aws_iam_role.monitoring_scheduler.arn
  }

  depends_on = [
    aws_iam_role_policy.monitoring_scheduler,
  ]
}
