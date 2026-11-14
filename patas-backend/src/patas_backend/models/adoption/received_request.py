from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from patas_backend.models.adoption.profile_snapshot import ProfileSnapshot
from patas_backend.models.adoption.status import ApplicationStatus


@dataclass(frozen=True)
class ReceivedRequest:
    """One request received by the animal's owner, with its saved profile."""

    id: UUID
    animal_id: UUID
    animal_name: str
    applicant_id: UUID
    status: ApplicationStatus
    applicant_note: str
    applicant_profile: ProfileSnapshot
    created_at: datetime
    compatibility_concerns: tuple[str, ...] = ()
