class MonitoringError(Exception):
    """Base exception for monitoring errors."""


class SubscriptionsServiceUnavailableError(MonitoringError):
    """Raised when subscriptions cannot be read or updated."""


class VehiclesServiceUnavailableError(MonitoringError):
    """Raised when current Webmotors listings cannot be retrieved."""
