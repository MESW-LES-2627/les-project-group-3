from enum import StrEnum


class ApplicationStatus(StrEnum):
    OPEN = "open"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    WITHDRAWN = "withdrawn"
    CLOSED = "closed"
    ADOPTED = "adopted"
