variable "frontend_base_url" {
  description = "Public base URL of the frontend used in email links."
  type        = string
}

locals {
  frontend_allowed_origins = [
    var.frontend_base_url,
    "http://localhost:5173",
  ]
}

resource "aws_apigatewayv2_api" "prices_car_watch" {
  name          = "prices-car-watch-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = local.frontend_allowed_origins
    allow_methods = ["GET", "POST", "DELETE", "OPTIONS"]
    allow_headers = ["content-type"]
  }
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/prices-car-watch-api"
  retention_in_days = 7
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.prices_car_watch.id
  name        = "$default"
  auto_deploy = true

  # Portfolio deployment: protect the unauthenticated browser-facing routes
  # without throttling the IAM-protected calls made between services.
  dynamic "route_settings" {
    for_each = toset([
      "POST /subscriptions",
      "GET /subscriptions/{subscriptionId}/confirm",
      "GET /subscriptions/{subscriptionId}",
      "DELETE /subscriptions/{subscriptionId}",
      "GET /vehicles/makes",
      "GET /vehicles/makes/{makeId}/models",
      "GET /vehicles/makes/{makeId}/models/{modelId}/versions",
      "GET /vehicles/makes/{makeId}/models/{modelId}/versions/{versionId}/years",
      "GET /vehicles/makes/{makeId}/models/{modelId}/versions/{versionId}/years/{yearId}",
    ])

    content {
      route_key              = route_settings.value
      throttling_burst_limit = 2
      throttling_rate_limit  = 1
    }
  }

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId        = "$context.requestId"
      routeKey         = "$context.routeKey"
      status           = "$context.status"
      requestTime      = "$context.requestTime"
      httpMethod       = "$context.httpMethod"
      path             = "$context.path"
      protocol         = "$context.protocol"
      responseLength   = "$context.responseLength"
      integrationError = "$context.integrationErrorMessage"
    })
  }
}
