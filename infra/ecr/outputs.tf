output "repository_urls" {
  description = "ECR repository URLs used by the application deployment."
  value = {
    vehicles      = aws_ecr_repository.vehicles.repository_url
    subscriptions = aws_ecr_repository.subscriptions.repository_url
    notifications = aws_ecr_repository.notifications.repository_url
    monitoring    = aws_ecr_repository.monitoring.repository_url
  }
}
