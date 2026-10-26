module "confirmation_email_queue" {
  source = "../modules/sqs"

  queue_name = "prices-car-watch-confirmation-email.fifo"
  fifo_queue = true
}

module "new_listings_dlq" {
  source = "../modules/sqs"

  queue_name = "prices-car-watch-new-listings-dlq"
}

module "new_listings_queue" {
  source = "../modules/sqs"

  queue_name                 = "prices-car-watch-new-listings"
  dead_letter_target_arn     = module.new_listings_dlq.queue_arn
  visibility_timeout_seconds = 180
}
