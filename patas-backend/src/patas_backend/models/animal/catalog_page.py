from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar

from patas_backend.models.animal.animal import Animal


@dataclass(frozen=True)
class CatalogPage:
    """One page of the catalog, numbered from 1. A page past the end is empty."""

    SIZE: ClassVar[int] = 24  # fills rows of 2 or 3 cards

    number: int = 1

    def __post_init__(self) -> None:
        if self.number < 1:
            raise ValueError("a catalog page is numbered from 1")

    def of(self, animals: Sequence[Animal]) -> list[Animal]:
        start = (self.number - 1) * self.SIZE
        return list(animals[start : start + self.SIZE])
