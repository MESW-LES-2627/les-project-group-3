from uuid import UUID

import pytest

from patas_backend.models.animal import AnimalMatchProfile, AnimalSize
from patas_backend.models.compatibility import (
    CompatibilityMode,
    InvalidCompatibilityMode,
    LooseFitStrategy,
    StrictFitStrategy,
    strategy_for,
)
from patas_backend.models.matching import EnergyLevel, ExperienceLevel, TimeAway
from patas_backend.models.matchmaker_profile import HousingType, MatchmakerProfile


@pytest.mark.parametrize(
    ("mode", "strategy"),
    [("loose", LooseFitStrategy), ("strict", StrictFitStrategy)],
)
def test_each_mode_gives_its_own_strategy(mode: str, strategy: type) -> None:
    assert type(strategy_for(mode)) is strategy


def test_a_mode_member_is_accepted_as_well_as_its_text() -> None:
    assert type(strategy_for(CompatibilityMode.STRICT)) is StrictFitStrategy


@pytest.mark.parametrize("mode", ["", "medium", "Loose", "STRICT", " strict"])
def test_an_unknown_mode_is_rejected_and_the_allowed_ones_are_listed(
    mode: str,
) -> None:
    with pytest.raises(InvalidCompatibilityMode, match="loose, strict"):
        strategy_for(mode)


def test_the_two_modes_judge_the_same_pair_differently() -> None:
    # The worked example: loose scores 75, strict 38. Swapping them would fail here.
    adopter = MatchmakerProfile(
        user_id=UUID("0b1f2a3c-4d5e-4f60-8a7b-9c0d1e2f3a4b"),
        housing=HousingType.APARTMENT,
        activity=EnergyLevel.MODERATE,
        time_away=TimeAway.HALF_DAY,
        experience=ExperienceLevel.SOME,
        has_children=False,
        has_dogs=False,
        has_cats=False,
    )
    animal = AnimalMatchProfile(
        activity=EnergyLevel.MODERATE,
        max_time_alone=TimeAway.FEW_HOURS,
        experience_needed=ExperienceLevel.NONE,
        space_needed=AnimalSize.MEDIUM,
    )

    assert strategy_for("loose").evaluate(adopter, animal).score == 75
    assert strategy_for("strict").evaluate(adopter, animal).score == 38
