class EmailDeliveryError(Exception):
    """Raised when the email provider cannot deliver a message."""

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        operation: str,
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
