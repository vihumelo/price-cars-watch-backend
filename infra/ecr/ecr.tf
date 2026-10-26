resource "aws_ecr_repository" "vehicles" {
  name = "prices-car-watch-vehicles"
}

resource "aws_ecr_repository" "subscriptions" {
  name = "prices-car-watch-subscriptions"
}

resource "aws_ecr_repository" "notifications" {
  name = "prices-car-watch-notifications"
}

resource "aws_ecr_repository" "monitoring" {
  name = "prices-car-watch-monitoring"
}
