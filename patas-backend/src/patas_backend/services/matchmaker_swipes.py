from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from patas_backend.models.animal import AdoptionStatus, Animal, AnimalRepository
from patas_backend.models.compatibility import (
    CompatibilityMode,
    CompatibilityResult,
    strategy_for,
)
from patas_backend.models.matchmaker_profile import MatchmakerProfileRepository
from patas_backend.models.matchmaker_swipe import (
    AlreadySwiped,
    MatchmakerSwipe,
    MatchmakerSwipeRepository,
    SwipeAnimalNotAvailable,
    SwipeDisposition,
    SwipeNotSaved,
    SwipeOwnAnimal,
    SwipeProfileRequired,
)
from patas_backend.models.user import User

FEED_SIZE = 10
SAMPLE_SIZE = 100


@dataclass(frozen=True)
class SwipeAnimal:
    animal: Animal
    fit: CompatibilityResult | None


def _fit_rank(result: SwipeAnimal) -> tuple[bool, int, str]:
    if result.fit is None:
        return False, 0, str(result.animal.id)
    return (
        not result.fit.is_compatible,
        -result.fit.score,
        str(result.animal.id),
    )


class MatchmakerSwipeService:
    """Rank animals for one adopter and persist their pass/save decisions."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def list_feed(self, user: User) -> list[SwipeAnimal]:
        async with self._session_factory() as session:
            profile = await MatchmakerProfileRepository(session).get(user.id)
            if profile is None:
                raise SwipeProfileRequired("Save your Matchmaker profile to start")
            sample = await AnimalRepository(session).sample_for_matchmaker(
                user.id, user.id, SAMPLE_SIZE
            )

        strategy = strategy_for(CompatibilityMode.LOOSE)
        ranked = [
            SwipeAnimal(animal, strategy.evaluate(profile, animal.match_profile()))
            for animal in sample
        ]
        ranked.sort(key=_fit_rank)
        return ranked[:FEED_SIZE]

    async def list_saved(self, user: User) -> list[SwipeAnimal]:
        async with self._session_factory() as session:
            profile = await MatchmakerProfileRepository(session).get(user.id)
            animals = await AnimalRepository(session).list_all()
            swipes = await MatchmakerSwipeRepository(session).list_by_user(user.id)

        available = {
            animal.id: animal
            for animal in animals
            if animal.adoption_status is AdoptionStatus.AVAILABLE
            and animal.owner_id != user.id
        }
        saved = [
            available[swipe.animal_id]
            for swipe in swipes
            if swipe.disposition is SwipeDisposition.SAVED
            and swipe.animal_id in available
        ]
        if profile is None:
            return [SwipeAnimal(animal, None) for animal in saved]

        strategy = strategy_for(CompatibilityMode.LOOSE)
        ranked = [
            SwipeAnimal(animal, strategy.evaluate(profile, animal.match_profile()))
            for animal in saved
        ]
        ranked.sort(key=_fit_rank)
        return ranked

    async def record_swipe(
        self, user: User, animal_id: UUID, disposition: SwipeDisposition
    ) -> MatchmakerSwipe:
        async with self._session_factory.begin() as session:
            animal = await AnimalRepository(session).get_for_update(animal_id)
            if animal is None or not animal.is_published:
                raise SwipeAnimalNotAvailable("This animal is no longer available")
            if animal.owner_id == user.id:
                raise SwipeOwnAnimal("You cannot swipe on your own animal")
            if animal.adoption_status is not AdoptionStatus.AVAILABLE:
                raise SwipeAnimalNotAvailable("This animal is no longer available")
            if await MatchmakerProfileRepository(session).get(user.id) is None:
                raise SwipeProfileRequired("Save your Matchmaker profile to start")

            swipe = MatchmakerSwipe(user.id, animal_id, disposition)
            if not await MatchmakerSwipeRepository(session).add(swipe):
                raise AlreadySwiped("You have already swiped on this animal")
        return swipe

    async def remove_saved(self, user: User, animal_id: UUID) -> None:
        async with self._session_factory.begin() as session:
            repository = MatchmakerSwipeRepository(session)
            swipe = await repository.get_for_update(user.id, animal_id)
            if swipe is None:
                raise SwipeNotSaved("This animal is not in your saved list")
            swipe.remove_from_saved()
            await repository.update(swipe)
