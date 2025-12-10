from typing import Optional


class DomainError(Exception):
    """Base class for predictable domain errors."""

    def __init__(self, message: str, status_code: int = 500, code: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.code = code or self.__class__.__name__
        super().__init__(message)


class AuthError(DomainError):
    """Authentication and authorization failures."""

    def __init__(self, message: str = "Unauthorized", status_code: int = 401):
        super().__init__(message, status_code=status_code, code="AuthError")


class NotFoundError(DomainError):
    """Resource not found."""

    def __init__(self, resource: str = "Resource", identifier: object = ""):
        msg = f"{resource} not found: {identifier}" if identifier else f"{resource} not found"
        super().__init__(msg, status_code=404, code="NotFoundError")


class ValidationError(DomainError):
    """Request validation error."""

    def __init__(self, field: str = "payload", message: str = "Validation failed"):
        msg = f"{field}: {message}" if field else message
        super().__init__(msg, status_code=422, code="ValidationError")


class DataSourceError(DomainError):
    """Upstream data source failure or unavailability."""

    def __init__(self, source: str = "data source", message: str = "unavailable"):
        super().__init__(f"{source}: {message}", status_code=502, code="DataSourceError")
