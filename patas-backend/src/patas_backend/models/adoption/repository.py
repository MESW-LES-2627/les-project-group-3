import json
from typing import Any
from uuid import UUID

from sqlalchemy import Row, text
from sqlalchemy.ext.asyncio import AsyncSession

from patas_backend.models.adoption.application import AdoptionApplication
from patas_backend.models.adoption.profile_snapshot import ProfileSnapshot
from patas_backend.models.adoption.status import ApplicationStatus

_COLUMNS = """
    id, animal_id, owner_id, applicant_id, applicant_note, applicant_profile,
    status, owner_note, owner_confirmed_at, applicant_confirmed_at, created_at
"""

_INSERT = text(
    """
    INSERT INTO patas.adoption_applications
        (id, animal_id, owner_id, applicant_id, applicant_note, applicant_profile,
         status, owner_note, owner_confirmed_at, applicant_confirmed_at)
    VALUES (
        :id, :animal_id, :owner_id, :applicant_id, :applicant_note,
        CAST(:applicant_profile AS jsonb),
        CAST(:status AS patas.application_status),
        :owner_note, :owner_confirmed_at, :applicant_confirmed_at
    )
    """
)
# Only what a transition can change. The request itself (animal, owner, applicant,
# note and profile snapshot) is fixed when it is made.
_UPDATE = text(
    """
    UPDATE patas.adoption_applications
    SET
        status = CAST(:status AS patas.application_status),
        owner_note = :owner_note,
        owner_confirmed_at = :owner_confirmed_at,
        applicant_confirmed_at = :applicant_confirmed_at
    WHERE id = :id
    """
)
_SELECT_BY_ID = text(
    f"SELECT {_COLUMNS} FROM patas.adoption_applications WHERE id = :id"
)
_SELECT_BY_ID_FOR_UPDATE = text(_SELECT_BY_ID.text + " FOR UPDATE")
_SELECT_ANIMAL_ID = text(
    "SELECT animal_id FROM patas.adoption_applications WHERE id = :id"
)
_SELECT_ACTIVE_FOR_APPLICANT = text(
    f"""
    SELECT {_COLUMNS}
    FROM patas.adoption_applications
    WHERE animal_id = :animal_id AND applicant_id = :applicant_id
      AND status IN ('open', 'accepted')
    """
)
# created_at ties inside one transaction (now() is fixed per transaction), so id
# keeps the order deterministic there.
_SELECT_OPEN_FOR_ANIMAL_FOR_UPDATE = text(
    f"""
    SELECT {_COLUMNS}
    FROM patas.adoption_applications
    WHERE animal_id = :animal_id AND status = 'open'
    ORDER BY created_at, id
    FOR UPDATE
    """
)


def _to_params(application: AdoptionApplication) -> dict[str, Any]:
    return {
        "id": application.id,
        "animal_id": application.animal_id,
        "owner_id": application.owner_id,
        "applicant_id": application.applicant_id,
        "applicant_note": application.applicant_note,
        "applicant_profile": json.dumps(application.applicant_profile.to_json()),
        "status": application.status.value,
        "owner_note": application.owner_note,
        "owner_confirmed_at": application.owner_confirmed_at,
        "applicant_confirmed_at": application.applicant_confirmed_at,
    }


def _from_row(row: Row[Any]) -> AdoptionApplication:
    return AdoptionApplication(
        id=row.id,
        animal_id=row.animal_id,
        owner_id=row.owner_id,
        applicant_id=row.applicant_id,
        applicant_note=row.applicant_note,
        # The driver hands jsonb back already parsed.
        applicant_profile=ProfileSnapshot.from_json(row.applicant_profile),
        status=ApplicationStatus(row.status),
        owner_note=row.owner_note,
        owner_confirmed_at=row.owner_confirmed_at,
        applicant_confirmed_at=row.applicant_confirmed_at,
        created_at=row.created_at,
    )


class AdoptionApplicationRepository:
    """Persistence for AdoptionApplication. The caller owns the transaction.

    This never commits. Lock order across the adoption use cases is always the
    animal first, then its applications.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, application: AdoptionApplication) -> None:
        await self._session.execute(_INSERT, _to_params(application))

    async def update(self, application: AdoptionApplication) -> None:
        """Save a transition. Load the application with get_for_update first, so
        that two changes at once cannot overwrite each other (ADR 0014)."""
        await self._session.execute(_UPDATE, _to_params(application))

    async def get_by_id(self, application_id: UUID) -> AdoptionApplication | None:
        """A plain read, with no lock."""
        result = await self._session.execute(_SELECT_BY_ID, {"id": application_id})
        row = result.first()
        return _from_row(row) if row is not None else None

    async def get_for_update(self, application_id: UUID) -> AdoptionApplication | None:
        """Like get_by_id, but locks the row until the transaction ends."""
        result = await self._session.execute(
            _SELECT_BY_ID_FOR_UPDATE, {"id": application_id}
        )
        row = result.first()
        return _from_row(row) if row is not None else None

    async def get_active(
        self, animal_id: UUID, applicant_id: UUID
    ) -> AdoptionApplication | None:
        """The applicant's open or accepted request for this animal, if any.

        The database allows at most one such request per applicant and animal.
        """
        result = await self._session.execute(
            _SELECT_ACTIVE_FOR_APPLICANT,
            {"animal_id": animal_id, "applicant_id": applicant_id},
        )
        row = result.first()
        return _from_row(row) if row is not None else None

    async def get_animal_id(self, application_id: UUID) -> UUID | None:
        """Which animal an application is for, without locking anything.

        Use cases read this first, so they can lock the animal before the
        application.
        """
        result = await self._session.execute(_SELECT_ANIMAL_ID, {"id": application_id})
        return result.scalar_one_or_none()

    async def list_open_for_animal_for_update(
        self, animal_id: UUID
    ) -> list[AdoptionApplication]:
        """The animal's open applications, oldest first, locked until the end of
        the transaction."""
        result = await self._session.execute(
            _SELECT_OPEN_FOR_ANIMAL_FOR_UPDATE, {"animal_id": animal_id}
        )
        return [_from_row(row) for row in result]
