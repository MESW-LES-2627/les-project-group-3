class InvalidApplication(ValueError):
    """An AdoptionApplication invariant was violated."""


class OwnerCannotApply(InvalidApplication):
    """The applicant owns the animal. A distinct error so that the router can answer
    403 here and 422 for a bad note."""


class AlreadyRequested(Exception):
    """The applicant already has an open or accepted request for this animal."""


class MatchmakerProfileRequired(Exception):
    """A request carries the applicant's Matchmaker profile, so they need one."""


class ApplicationUnauthorized(PermissionError):
    """The caller may not do this to the application."""


class InvalidTransition(Exception):
    """The application's status does not allow this change."""
