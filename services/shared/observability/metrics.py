"""Provide helpers for recording metrics with AWS Lambda Powertools."""

import os

from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit


metrics = Metrics(
    namespace=os.getenv("POWERTOOLS_METRICS_NAMESPACE", "PricesCarWatch"),
    service=os.getenv("POWERTOOLS_SERVICE_NAME", "unknown"),
)


def emit_metric(
    name: str,
    value: int | float = 1,
    unit: MetricUnit = MetricUnit.Count,
) -> None:
    """Add a metric to the shared Powertools metrics collection."""
    metrics.add_metric(name=name, unit=unit, value=value)
