import pytest
from adoption_factory import (
    Factory,
    World,
    load,
    load_animal,
    persist_application,
)

from patas_backend.models.adoption import ApplicationStatus
from patas_backend.models.animal import AdoptionStatus

S = ApplicationStatus
# The animal's status that goes with an application in each status.
ANIMAL_STATUS = {
    S.OPEN: AdoptionStatus.AVAILABLE,
    S.ACCEPTED: AdoptionStatus.RESERVED,
    S.DECLINED: AdoptionStatus.AVAILABLE,
    S.WITHDRAWN: AdoptionStatus.AVAILABLE,
    S.CLOSED: AdoptionStatus.AVAILABLE,
    S.ADOPTED: AdoptionStatus.ADOPTED,
}


def test_the_table_covers_every_status() -> None:
    assert set(ANIMAL_STATUS) == set(S)


@pytest.mark.parametrize("status", list(S))
async def test_an_application_persists_with_the_animal_status_that_goes_with_it(
    session_factory: Factory, world: World, status: S
) -> None:
    application = await persist_application(
        session_factory, world, applicant=world.bruno, status=status
    )

    assert (await load(session_factory, application.id)).status is status
    animal = await load_animal(session_factory, world.rex)
    assert animal.adoption_status is ANIMAL_STATUS[status]


async def test_an_adopted_application_has_both_confirmations(
    session_factory: Factory, world: World
) -> None:
    application = await persist_application(
        session_factory, world, applicant=world.bruno, status=S.ADOPTED
    )

    stored = await load(session_factory, application.id)
    assert stored.owner_confirmed_at is not None
    assert stored.applicant_confirmed_at is not None
