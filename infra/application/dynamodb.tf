resource "aws_dynamodb_table" "subscriptions" {
  name         = "prices-car-watch-subscriptions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "subscriptionId"

  attribute {
    name = "subscriptionId"
    type = "S"
  }

  attribute {
    name = "subscriptionKey"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name            = "subscriptionKey-index"
    projection_type = "ALL"

    key_schema {
      attribute_name = "subscriptionKey"
      key_type       = "HASH"
    }
  }

  global_secondary_index {
    name            = "status-index"
    projection_type = "ALL"

    key_schema {
      attribute_name = "status"
      key_type       = "HASH"
    }
  }
}
