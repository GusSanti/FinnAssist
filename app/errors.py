"""Domain errors translated into HTTP responses by the API layer."""


class ResourceNotFoundError(ValueError):
    """A requested application resource does not exist."""


class ResourceConflictError(ValueError):
    """An operation conflicts with existing application data."""
