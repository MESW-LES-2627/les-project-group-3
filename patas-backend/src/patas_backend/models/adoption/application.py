from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from patas_backend.models.adoption.errors import (
    ApplicationUnauthorized,
    InvalidApplication,
)
from patas_backend.models.adoption.profile_snapshot import ProfileSnapshot
from patas_backend.models.adoption.state import STATES, ApplicationState
from patas_backend.models.adoption.status import ApplicationStatus
from patas_backend.models.events import DomainEvent


def _clean_note(note: str | None) -> str | None:
    if note is None:
        return None
    return note.strip() or None


@dataclass
class AdoptionApplication:
    """One person's request to adopt one animal.

    Loading from the database goes through the constructor, like Animal. The
    aggregate answers who may act; the state of its status answers when.
    """

    id: UUID
    animal_id: UUID
    # Copied from the animal when the request is made; an animal's owner does not
    # change in the MVP, so this never changes.
    owner_id: UUID
    applicant_id: UUID
    applicant_note: str
    applicant_profile: ProfileSnapshot
    status: ApplicationStatus = ApplicationStatus.OPEN
    owner_note: str | None = None
    owner_confirmed_at: datetime | None = None
    applicant_confirmed_at: datetime | None = None
    created_at: datetime | None = None  # set by the database

    def __post_init__(self) -> None:
        if self.applicant_id == self.owner_id:
            raise InvalidApplication("an owner cannot apply for their own animal")
        self._events: list[DomainEvent] = []

    @classmethod
    def request(
        cls,
        *,
        animal_id: UUID,
        owner_id: UUID,
        applicant_id: UUID,
        applicant_note: str,
        applicant_profile: ProfileSnapshot,
    ) -> "AdoptionApplication":
        """A new request. It always starts open."""
        return cls(
            id=uuid4(),
            animal_id=animal_id,
            owner_id=owner_id,
            applicant_id=applicant_id,
            applicant_note=applicant_note,
            applicant_profile=applicant_profile,
        )

    @property
    def _state(self) -> ApplicationState:
        return STATES[self.status]

    def accept(self, by_user_id: UUID, note: str | None = None) -> None:
        self._require(by_user_id, self.owner_id, "Only the owner can accept")
        self._state.accept(self, _clean_note(note))

    def decline(self, by_user_id: UUID, note: str | None = None) -> None:
        self._require(by_user_id, self.owner_id, "Only the owner can decline")
        self._state.decline(self, _clean_note(note))

    def withdraw(self, by_user_id: UUID) -> None:
        self._require(by_user_id, self.applicant_id, "Only the applicant can withdraw")
        self._state.withdraw(self)

    def confirm_handover(self, by_user_id: UUID, at: datetime) -> None:
        if by_user_id == self.owner_id:
            by_owner = True
        elif by_user_id == self.applicant_id:
            by_owner = False
        else:
            raise ApplicationUnauthorized(
                "Only the owner or the applicant can confirm the handover"
            )
        self._state.confirm_handover(self, by_owner, at)

    def close(self) -> None:
        """The system closes an open request: no person does this."""
        self._state.close(self)

    def pull_events(self) -> list[DomainEvent]:
        """The events recorded since the last call; each is returned once."""
        events, self._events = self._events, []
        return events

    def _become(self, status: ApplicationStatus, event: DomainEvent) -> None:
        """Used by the states: set the new status and record what happened."""
        self.status = status
        self._events.append(event)

    @staticmethod
    def _require(user_id: UUID, expected: UUID, message: str) -> None:
        if user_id != expected:
            raise ApplicationUnauthorized(message)
