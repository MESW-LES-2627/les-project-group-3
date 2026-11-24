from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from patas_backend.models.adoption.handover_item import HandoverItem
from patas_backend.models.adoption.profile_snapshot import ProfileSnapshot
from patas_backend.models.adoption.status import ApplicationStatus


@dataclass(frozen=True)
class ReceivedRequest:
    """One request received by the animal's owner, with its saved profile."""

    id: UUID
    animal_id: UUID
    animal_name: str
    applicant_id: UUID
    applicant_name: str
    applicant_username: str
    status: ApplicationStatus
    applicant_note: str
    applicant_profile: ProfileSnapshot
    owner_note: str | None
    created_at: datetime
    owner_confirmed_at: datetime | None = None
    applicant_confirmed_at: datetime | None = None
    handover_checked: frozenset[HandoverItem] = frozenset()
    compatibility_concerns: tuple[str, ...] = ()
