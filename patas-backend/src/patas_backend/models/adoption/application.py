from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from patas_backend.models.adoption.errors import (
    ApplicationUnauthorized,
    InvalidApplication,
    OwnerCannotApply,
)
from patas_backend.models.adoption.handover_item import HandoverItem
from patas_backend.models.adoption.profile_snapshot import ProfileSnapshot
from patas_backend.models.adoption.state import STATES, ApplicationState
from patas_backend.models.adoption.status import ApplicationStatus
from patas_backend.models.events import DomainEvent

MAX_NOTE_LENGTH = 1000


def _check_length(note: str) -> None:
    if len(note) > MAX_NOTE_LENGTH:
        raise InvalidApplication(
            f"the note must have at most {MAX_NOTE_LENGTH} characters"
        )


def _validated_note(note: str) -> str:
    """The applicant's note: required, trimmed, and at most MAX_NOTE_LENGTH long."""
    cleaned = note.strip()
    if not cleaned:
        raise InvalidApplication("the note must not be blank")
    _check_length(cleaned)
    return cleaned


def _clean_note(note: str | None) -> str | None:
    """The owner's note: optional, trimmed (blank is none), at most MAX_NOTE_LENGTH."""
    if note is None:
        return None
    cleaned = note.strip()
    _check_length(cleaned)
    return cleaned or None


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
    # The checklist items either side has ticked. It never blocks the handover.
    handover_checked: frozenset[HandoverItem] = frozenset()
    # When the owner accepted. A request accepted at some point has a conversation,
    # even after it ends (US-21).
    accepted_at: datetime | None = None
    created_at: datetime | None = None  # set by the database

    def __post_init__(self) -> None:
        if self.applicant_id == self.owner_id:
            raise OwnerCannotApply("an owner cannot apply for their own animal")
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
            applicant_note=_validated_note(applicant_note),
            applicant_profile=applicant_profile,
        )

    @property
    def _state(self) -> ApplicationState:
        return STATES[self.status]

    def accept(
        self, by_user_id: UUID, note: str | None = None, *, at: datetime | None = None
    ) -> None:
        self._require(by_user_id, self.owner_id, "Only the owner can accept")
        self._state.accept(self, _clean_note(note), at or datetime.now(UTC))

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

    def set_handover_item(
        self, by_user_id: UUID, item: HandoverItem, checked: bool
    ) -> None:
        if not self.is_participant(by_user_id):
            raise ApplicationUnauthorized(
                "Only the owner or the applicant can change the handover checklist"
            )
        self._state.set_handover_item(self, item, checked)

    def is_participant(self, user_id: UUID) -> bool:
        """The owner and the applicant are the only two sides of a request."""
        return user_id in (self.owner_id, self.applicant_id)

    @property
    def has_conversation(self) -> bool:
        """The conversation opens when the request is accepted and stays readable."""
        return self.accepted_at is not None

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
