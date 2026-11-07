class InvalidApplication(ValueError):
    """An AdoptionApplication invariant was violated."""


class ApplicationUnauthorized(PermissionError):
    """The caller may not do this to the application."""


class InvalidTransition(Exception):
    """The application's status does not allow this change."""
