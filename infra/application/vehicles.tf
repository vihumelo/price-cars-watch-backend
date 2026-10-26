variable "vehicles_image_uri" {
  description = "Full URI of the Vehicles image to deploy."
  type        = string
}

variable "vehicle_provider" {
  description = "Vehicle provider selected by the Vehicles Lambda."
  type        = string
}

module "vehicles_lambda" {
  source = "../modules/lambda"

  function_name = "prices-car-watch-vehicles"
  image_uri     = var.vehicles_image_uri

  environment_variables = {
    POWERTOOLS_METRICS_NAMESPACE = "PricesCarWatch"
    POWERTOOLS_SERVICE_NAME      = "vehicles"
    VEHICLE_PROVIDER             = var.vehicle_provider
  }
}

resource "aws_apigatewayv2_integration" "vehicles" {
  api_id                 = aws_apigatewayv2_api.prices_car_watch.id
  integration_type       = "AWS_PROXY"
  integration_uri        = module.vehicles_lambda.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "vehicles_public" {
  for_each = toset([
    "GET /vehicles/makes",
    "GET /vehicles/makes/{makeId}/models",
    "GET /vehicles/makes/{makeId}/models/{modelId}/versions",
    "GET /vehicles/makes/{makeId}/models/{modelId}/versions/{versionId}/years",
    "GET /vehicles/makes/{makeId}/models/{modelId}/versions/{versionId}/years/{yearId}",
  ])

  api_id    = aws_apigatewayv2_api.prices_car_watch.id
  route_key = each.value
  target    = "integrations/${aws_apigatewayv2_integration.vehicles.id}"
}

resource "aws_apigatewayv2_route" "vehicles_internal" {
  api_id             = aws_apigatewayv2_api.prices_car_watch.id
  route_key          = "POST /internal/vehicles/listings"
  target             = "integrations/${aws_apigatewayv2_integration.vehicles.id}"
  authorization_type = "AWS_IAM"
}

resource "aws_lambda_permission" "vehicles_api_gateway" {
  statement_id  = "AllowExecutionFromApiGateway"
  action        = "lambda:InvokeFunction"
  function_name = module.vehicles_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.prices_car_watch.execution_arn}/*/*"
}
