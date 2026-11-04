from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from patas_backend.models.animal import (
    Animal,
    AnimalCompatibility,
    AnimalRepository,
    AnimalSex,
    AnimalSize,
    CatalogFilter,
    District,
    FirstTimeOwnerSuitability,
    NeuteredStatus,
    Species,
)
from patas_backend.models.matching.scales import EnergyLevel
from patas_backend.models.user import User


class AnimalService:
    """Animal use cases. Each one owns its transaction."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def publish(
        self,
        owner: User,
        *,
        name: str,
        species: Species,
        age_in_months: int | None,
        sex: AnimalSex | None = None,
        is_neutered: NeuteredStatus | None = None,
        postal_code: str | None = None,
        district: District | None = None,
        size: AnimalSize | None = None,
        activity_level: EnergyLevel | None = None,
        space_requirement: AnimalSize | None = None,
        shedding: EnergyLevel | None = None,
        grooming_needs: EnergyLevel | None = None,
        behaves_well_with_children: AnimalCompatibility | None = None,
        behaves_well_with_dogs: AnimalCompatibility | None = None,
        behaves_well_with_cats: AnimalCompatibility | None = None,
        behaves_well_with_other_animals: AnimalCompatibility | None = None,
        training_needs: EnergyLevel | None = None,
        tolerance_for_time_alone: EnergyLevel | None = None,
        noise_level: EnergyLevel | None = None,
        suitable_for_first_time_owners: FirstTimeOwnerSuitability | None = None,
        special_care_notes: str | None = None,
        other_details: str | None = None,
    ) -> Animal:
        """A1 (create): the logged-in user publishes an animal they own."""
        # Built before the transaction opens: an invalid animal raises InvalidAnimal
        # and nothing reaches the database (AC3).
        animal = Animal.publish(
            owner_id=owner.id,
            name=name,
            species=species,
            owner_name=owner.name,
            age_in_months=age_in_months,
            sex=sex,
            is_neutered=is_neutered,
            postal_code=postal_code,
            district=district,
            size=size,
            activity_level=activity_level,
            space_requirement=space_requirement,
            shedding=shedding,
            grooming_needs=grooming_needs,
            behaves_well_with_children=behaves_well_with_children,
            behaves_well_with_dogs=behaves_well_with_dogs,
            behaves_well_with_cats=behaves_well_with_cats,
            behaves_well_with_other_animals=behaves_well_with_other_animals,
            training_needs=training_needs,
            tolerance_for_time_alone=tolerance_for_time_alone,
            noise_level=noise_level,
            suitable_for_first_time_owners=suitable_for_first_time_owners,
            special_care_notes=special_care_notes,
            other_details=other_details,
        )

        async with self._session_factory.begin() as session:
            await AnimalRepository(session).add(animal)
        return animal

    async def list_catalog(self, catalog_filter: CatalogFilter) -> list[Animal]:
        """A2 (list): the published animals that match, newest first. Public."""
        # Read-only: a plain session, no transaction to commit.
        async with self._session_factory() as session:
            animals = await AnimalRepository(session).list_all()
            return [a for a in animals if catalog_filter.matches(a)]

    async def list_by_owner(self, owner: User) -> list[Animal]:
        """List all animals owned by the user, published and unpublished."""
        async with self._session_factory() as session:
            return await AnimalRepository(session).list_by_owner(owner.id)

    async def get(self, animal_id: UUID) -> Animal | None:
        """Fetch an animal by id."""
        async with self._session_factory() as session:
            return await AnimalRepository(session).get_by_id(animal_id)

    async def edit(
        self,
        owner: User,
        animal_id: UUID,
        *,
        name: str,
        species: Species,
        age_in_months: int | None,
        sex: AnimalSex | None = None,
        is_neutered: NeuteredStatus | None = None,
        postal_code: str | None = None,
        district: District | None = None,
        size: AnimalSize | None = None,
        activity_level: EnergyLevel | None = None,
        space_requirement: AnimalSize | None = None,
        shedding: EnergyLevel | None = None,
        grooming_needs: EnergyLevel | None = None,
        behaves_well_with_children: AnimalCompatibility | None = None,
        behaves_well_with_dogs: AnimalCompatibility | None = None,
        behaves_well_with_cats: AnimalCompatibility | None = None,
        behaves_well_with_other_animals: AnimalCompatibility | None = None,
        training_needs: EnergyLevel | None = None,
        tolerance_for_time_alone: EnergyLevel | None = None,
        noise_level: EnergyLevel | None = None,
        suitable_for_first_time_owners: FirstTimeOwnerSuitability | None = None,
        special_care_notes: str | None = None,
        other_details: str | None = None,
    ) -> Animal | None:
        """US-03: the owner replaces the description. None if there is no animal."""
        async with self._session_factory.begin() as session:
            repo = AnimalRepository(session)
            animal = await repo.get_for_update(animal_id)
            if animal is None:
                return None
            animal.edit(
                owner.id,
                name=name,
                species=species,
                age_in_months=age_in_months,
                sex=sex,
                is_neutered=is_neutered,
                postal_code=postal_code,
                district=district,
                size=size,
                activity_level=activity_level,
                space_requirement=space_requirement,
                shedding=shedding,
                grooming_needs=grooming_needs,
                behaves_well_with_children=behaves_well_with_children,
                behaves_well_with_dogs=behaves_well_with_dogs,
                behaves_well_with_cats=behaves_well_with_cats,
                behaves_well_with_other_animals=behaves_well_with_other_animals,
                training_needs=training_needs,
                tolerance_for_time_alone=tolerance_for_time_alone,
                noise_level=noise_level,
                suitable_for_first_time_owners=suitable_for_first_time_owners,
                special_care_notes=special_care_notes,
                other_details=other_details,
            )
            await repo.update(animal)
            return animal

    async def get_owned(self, owner: User, animal_id: UUID) -> Animal | None:
        """One of the owner's animals, unpublished included; None otherwise."""
        async with self._session_factory() as session:
            animal = await AnimalRepository(session).get_by_id(animal_id)
            if animal is None or not animal.is_owned_by(owner.id):
                return None
            return animal

    async def unpublish(self, owner: User, animal_id: UUID) -> Animal | None:
        """Unpublish an animal. Raises AnimalUnauthorized if caller is not the owner."""
        async with self._session_factory.begin() as session:
            repo = AnimalRepository(session)
            animal = await repo.get_for_update(animal_id)
            if animal is None:
                return None
            animal.unpublish(by_user_id=owner.id)
            await repo.update(animal)
            return animal
