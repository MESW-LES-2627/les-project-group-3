from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from patas_backend.models.adoption.status import ApplicationStatus


@dataclass(frozen=True)
class SentRequest:
    """One row of the applicant's list of requests, with the animal's name.

    A read model: it answers what the list shows and holds no rules. Changes go
    through AdoptionApplication, never through this.
    """

    id: UUID
    animal_id: UUID
    animal_name: str
    status: ApplicationStatus
    applicant_note: str
    owner_note: str | None
    created_at: datetime
