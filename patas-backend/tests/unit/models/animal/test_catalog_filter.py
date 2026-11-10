from uuid import UUID

import pytest

from patas_backend.models.animal import (
    Animal,
    AnimalSize,
    CatalogFilter,
    District,
    Species,
)
from patas_backend.models.matching.scales import LifeStage

OWNER_ID = UUID("0b1f2a3c-4d5e-4f60-8a7b-9c0d1e2f3a4b")

REX = Animal.publish(
    owner_id=OWNER_ID,
    name="Rex",
    species=Species.DOG,
    age_in_months=36,
    size=AnimalSize.MEDIUM,
    district=District.PORTO,
)
UNDESCRIBED = Animal.publish(owner_id=OWNER_ID, name="Toby", species=Species.DOG)


def test_no_criteria_allow_any_animal() -> None:
    assert CatalogFilter().matches(REX)
    assert CatalogFilter().matches(UNDESCRIBED)


@pytest.mark.parametrize(
    ("same", "other"),
    [
        pytest.param(
            CatalogFilter(species=Species.DOG),
            CatalogFilter(species=Species.CAT),
            id="species",
        ),
        pytest.param(
            CatalogFilter(size=AnimalSize.MEDIUM),
            CatalogFilter(size=AnimalSize.LARGE),
            id="size",
        ),
        pytest.param(
            CatalogFilter(district=District.PORTO),
            CatalogFilter(district=District.LISBOA),
            id="district",
        ),
        pytest.param(
            CatalogFilter(age_group=LifeStage.ADULT),
            CatalogFilter(age_group=LifeStage.SENIOR),
            id="age-group",
        ),
    ],
)
def test_a_criterion_matches_only_its_value(
    same: CatalogFilter, other: CatalogFilter
) -> None:
    assert same.matches(REX)
    assert not other.matches(REX)


@pytest.mark.parametrize(
    "catalog_filter",
    [
        CatalogFilter(size=AnimalSize.MEDIUM),
        CatalogFilter(district=District.PORTO),
        CatalogFilter(age_group=LifeStage.ADULT),
    ],
    ids=["size", "district", "age-group"],
)
def test_an_animal_without_the_value_never_matches(
    catalog_filter: CatalogFilter,
) -> None:
    assert not catalog_filter.matches(UNDESCRIBED)


def test_every_criterion_must_hold() -> None:
    assert CatalogFilter(species=Species.DOG, district=District.PORTO).matches(REX)
    assert not CatalogFilter(species=Species.DOG, district=District.LISBOA).matches(REX)
    assert not CatalogFilter(species=Species.CAT, district=District.PORTO).matches(REX)
