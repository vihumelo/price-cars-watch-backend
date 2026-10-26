class SubscriptionError(Exception):
    """Base exception for subscription errors."""


class InvalidConfirmationLinkError(SubscriptionError):
    """Raised when a confirmation link is invalid or expired."""


class SubscriptionAccessDeniedError(SubscriptionError):
    """Raised when a management token cannot access a subscription."""


class VehicleListingsNotFoundError(SubscriptionError):
    """Raised when the selected vehicle cannot be resolved by Vehicles."""


class VehicleListingsServiceUnavailableError(SubscriptionError):
    """Raised when Vehicles cannot establish a listings baseline."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        provider_request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.provider_request_id = provider_request_id
