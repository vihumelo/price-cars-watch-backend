class VehicleError(Exception):
    """Base exception for vehicle service errors."""


class VehicleNotFoundError(VehicleError):
    """Raised when the requested vehicle resource does not exist."""


class VehicleProviderError(VehicleError):
    """Raised when a vehicle provider returns an unsuccessful response."""

    def __init__(
        self,
        message: str,
        *,
        provider: str = "unknown",
        operation: str = "unknown",
        status_code: int | None = None,
        provider_code: str | None = None,
        provider_message: str | None = None,
        retryable: bool = True,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.operation = operation
        self.status_code = status_code
        self.provider_code = provider_code
        self.provider_message = provider_message
        self.retryable = retryable


class VehicleProviderUnavailableError(VehicleProviderError):
    """Raised when the vehicle provider cannot return a valid response."""
