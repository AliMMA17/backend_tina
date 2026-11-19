"""Domain-level exceptions.

Decision: Domain exceptions are pure Python and carry business meaning.
Presentation layer maps them to HTTP status codes. This keeps the
domain free of framework knowledge and makes error handling consistent
across API, CLI, message consumers, etc.
"""


class DomainError(Exception):
    """Base class for all domain errors."""

    def __init__(self, message: str = "A domain error occurred") -> None:
        self.message = message
        super().__init__(self.message)


class EntityNotFoundError(DomainError):
    """Raised when a requested entity does not exist."""

    def __init__(self, entity_name: str, entity_id: str | int) -> None:
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} with id '{entity_id}' was not found")


class EntityAlreadyExistsError(DomainError):
    """Raised when attempting to create a duplicate entity."""

    def __init__(self, entity_name: str, field: str, value: str) -> None:
        self.entity_name = entity_name
        self.field = field
        self.value = value
        super().__init__(f"{entity_name} with {field}='{value}' already exists")


class ValidationError(DomainError):
    """Raised when domain invariants are violated."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class AuthenticationError(DomainError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message)


class AuthorizationError(DomainError):
    """Raised when the caller lacks permission."""

    def __init__(self, message: str = "Not authorized") -> None:
        super().__init__(message)
