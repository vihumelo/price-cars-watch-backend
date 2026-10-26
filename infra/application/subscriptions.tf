variable "subscriptions_image_uri" {
  description = "Full URI of the Subscriptions image to deploy."
  type        = string
}

module "subscriptions_lambda" {
  source = "../modules/lambda"

  function_name = "prices-car-watch-subscriptions"
  image_uri     = var.subscriptions_image_uri

  environment_variables = {
    CONFIRMATION_EMAIL_QUEUE_URL = module.confirmation_email_queue.queue_url
    POWERTOOLS_METRICS_NAMESPACE = "PricesCarWatch"
    POWERTOOLS_SERVICE_NAME      = "subscriptions"
    VEHICLES_SERVICE_BASE_URL    = aws_apigatewayv2_api.prices_car_watch.api_endpoint
  }
}

resource "aws_iam_role_policy" "subscriptions_lambda" {
  name = "subscriptions-data-access"
  role = module.subscriptions_lambda.execution_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:Query",
        ]
        Resource = [
          aws_dynamodb_table.subscriptions.arn,
          "${aws_dynamodb_table.subscriptions.arn}/index/*",
        ]
      },
      {
        Effect   = "Allow"
        Action   = "sqs:SendMessage"
        Resource = module.confirmation_email_queue.queue_arn
      },
      {
        Effect   = "Allow"
        Action   = "execute-api:Invoke"
        Resource = "${aws_apigatewayv2_api.prices_car_watch.execution_arn}/*/POST/internal/vehicles/listings"
      },
    ]
  })
}

resource "aws_apigatewayv2_integration" "subscriptions" {
  api_id                 = aws_apigatewayv2_api.prices_car_watch.id
  integration_type       = "AWS_PROXY"
  integration_uri        = module.subscriptions_lambda.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "subscriptions_public" {
  for_each = toset([
    "POST /subscriptions",
    "GET /subscriptions/{subscriptionId}/confirm",
    "GET /subscriptions/{subscriptionId}",
    "DELETE /subscriptions/{subscriptionId}",
  ])

  api_id    = aws_apigatewayv2_api.prices_car_watch.id
  route_key = each.value
  target    = "integrations/${aws_apigatewayv2_integration.subscriptions.id}"
}

resource "aws_apigatewayv2_route" "subscriptions_internal" {
  for_each = toset([
    "GET /internal/subscriptions/monitoring",
    "PATCH /internal/subscriptions/{subscriptionId}/listings",
  ])

  api_id             = aws_apigatewayv2_api.prices_car_watch.id
  route_key          = each.value
  target             = "integrations/${aws_apigatewayv2_integration.subscriptions.id}"
  authorization_type = "AWS_IAM"
}

resource "aws_lambda_permission" "subscriptions_api_gateway" {
  statement_id  = "AllowExecutionFromApiGateway"
  action        = "lambda:InvokeFunction"
  function_name = module.subscriptions_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.prices_car_watch.execution_arn}/*/*"
}
