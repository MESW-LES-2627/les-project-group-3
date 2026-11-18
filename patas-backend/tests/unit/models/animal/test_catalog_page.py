from uuid import uuid4

import pytest

from patas_backend.models.animal import Animal, CatalogPage, Species

ANIMALS = [
    Animal.publish(owner_id=uuid4(), name=f"Animal {n}", species=Species.DOG)
    for n in range(50)
]


def test_the_first_page_is_the_first_24() -> None:
    assert CatalogPage().of(ANIMALS) == ANIMALS[:24]


def test_the_next_page_follows_without_a_gap_or_a_repeat() -> None:
    assert CatalogPage(2).of(ANIMALS) == ANIMALS[24:48]


def test_the_last_page_holds_what_is_left() -> None:
    assert CatalogPage(3).of(ANIMALS) == ANIMALS[48:]


def test_a_page_past_the_end_is_empty() -> None:
    assert CatalogPage(4).of(ANIMALS) == []


@pytest.mark.parametrize("number", [0, -1])
def test_pages_are_numbered_from_one(number: int) -> None:
    with pytest.raises(ValueError, match="numbered from 1"):
        CatalogPage(number)
