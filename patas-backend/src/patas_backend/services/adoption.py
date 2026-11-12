from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from patas_backend.models.adoption import (
    AdoptionApplication,
    AdoptionApplicationRepository,
    AlreadyRequested,
    MatchmakerProfileRequired,
    OwnerCannotApply,
    ProfileSnapshot,
    SentRequest,
)
from patas_backend.models.animal import AnimalRepository
from patas_backend.models.matchmaker_profile import MatchmakerProfileRepository
from patas_backend.models.user import User
from patas_backend.services.events import EventDispatcher
from patas_backend.services.locking import lock_animal_and_application


class AdoptionService:
    """Adoption use cases. Each one owns its transaction."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        dispatcher: EventDispatcher,
    ) -> None:
        self._session_factory = session_factory
        self._dispatcher = dispatcher

    async def request_to_adopt(
        self, applicant: User, animal_id: UUID, note: str
    ) -> AdoptionApplication | None:
        """US-14: the applicant asks to adopt an animal. None if there is no animal.

        Raises OwnerCannotApply, AnimalNotAvailable, AlreadyRequested,
        MatchmakerProfileRequired, or InvalidApplication for a bad note, in that
        order: what is wrong with the animal comes before what is missing from the
        applicant.
        """
        async with self._session_factory.begin() as session:
            # The animal is locked before anything about it is checked (ADR 0017,
            # decision 8): otherwise a request could slip in beside an unpublish and
            # stay open on an animal nobody can see. The lock also puts two requests
            # from the same person in line, so the duplicate check below is safe.
            animal = await AnimalRepository(session).get_for_update(animal_id)
            if animal is None:
                return None
            if animal.is_owned_by(applicant.id):
                raise OwnerCannotApply("an owner cannot apply for their own animal")
            animal.ensure_open_to_requests()

            applications = AdoptionApplicationRepository(session)
            if await applications.get_active(animal.id, applicant.id) is not None:
                raise AlreadyRequested("you already have a request for this animal")

            profile = await MatchmakerProfileRepository(session).get(applicant.id)
            if profile is None:
                raise MatchmakerProfileRequired("No Matchmaker profile yet")

            application = AdoptionApplication.request(
                animal_id=animal.id,
                owner_id=animal.owner_id,
                applicant_id=applicant.id,
                applicant_note=note,
                applicant_profile=ProfileSnapshot.of(profile),
            )
            await applications.add(application)
        return application

    async def get_active_request(
        self, applicant: User, animal_id: UUID
    ) -> AdoptionApplication | None:
        """The caller's open or accepted request for this animal, or None."""
        async with self._session_factory() as session:
            return await AdoptionApplicationRepository(session).get_active(
                animal_id, applicant.id
            )

    async def list_my_requests(self, applicant: User) -> list[SentRequest]:
        """US-17: every request the caller sent, in any status, newest first."""
        async with self._session_factory() as session:
            return await AdoptionApplicationRepository(session).list_sent_by(
                applicant.id
            )

    async def withdraw(
        self, applicant: User, application_id: UUID
    ) -> AdoptionApplication | None:
        """US-17: the applicant withdraws an open or accepted request.

        None if there is no such request or it is not the caller's: to anyone else
        it does not exist. Raises InvalidTransition if it already ended.
        """
        async with self._session_factory.begin() as session:
            # The animal first (ADR 0017, decision 8). Whether the request was
            # accepted, and so whether the animal must be freed, is read under the
            # lock: a withdrawal queued behind an accept sees it accepted.
            application = await lock_animal_and_application(session, application_id)
            if application is None or application.applicant_id != applicant.id:
                return None
            application.withdraw(applicant.id)
            events = await self._dispatcher.dispatch(application.pull_events(), session)
            await AdoptionApplicationRepository(session).update(application)
        await self._dispatcher.publish(events)
        return application
