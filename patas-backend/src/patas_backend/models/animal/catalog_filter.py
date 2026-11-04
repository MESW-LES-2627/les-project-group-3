from dataclasses import dataclass

from patas_backend.models.animal.animal import Animal
from patas_backend.models.animal.enums import AnimalSize, District, Species


@dataclass(frozen=True)
class CatalogFilter:
    """What a visitor narrows the catalog to. A criterion left as None allows any;
    an animal without the asked-for value never matches."""

    species: Species | None = None
    size: AnimalSize | None = None
    district: District | None = None

    def matches(self, animal: Animal) -> bool:
        return all(
            wanted is None or wanted == value
            for wanted, value in (
                (self.species, animal.species),
                (self.size, animal.size),
                (self.district, animal.district),
            )
        )
