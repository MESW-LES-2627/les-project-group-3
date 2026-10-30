from uuid import UUID

import pytest

from patas_backend.models.animal import AnimalMatchProfile
from patas_backend.models.compatibility import FitGraph, ReasonKind
from patas_backend.models.matching import (
    EnergyLevel,
    ExperienceLevel,
    LifeStage,
    TimeAway,
)
from patas_backend.models.matchmaker_profile import HousingType, MatchmakerProfile

USER_ID = UUID("0b1f2a3c-4d5e-4f60-8a7b-9c0d1e2f3a4b")

LOW, MODERATE, HIGH = EnergyLevel.LOW, EnergyLevel.MODERATE, EnergyLevel.HIGH
FEW_HOURS, HALF_DAY, MOST_OF_DAY = (
    TimeAway.FEW_HOURS,
    TimeAway.HALF_DAY,
    TimeAway.MOST_OF_DAY,
)
NONE, SOME, EXPERIENCED = (
    ExperienceLevel.NONE,
    ExperienceLevel.SOME,
    ExperienceLevel.EXPERIENCED,
)
APARTMENT = HousingType.APARTMENT
NO_YARD = HousingType.HOUSE_NO_YARD
WITH_YARD = HousingType.HOUSE_WITH_YARD

# (animal's training needs, adopter's experience) -> points, spelled out. 0 is absent.
TRAINING_X_EXPERIENCE = {
    (LOW, NONE): 0.0,
    (LOW, SOME): 0.0,
    (LOW, EXPERIENCED): 0.0,
    (MODERATE, NONE): 7.5,
    (MODERATE, SOME): 0.0,
    (MODERATE, EXPERIENCED): 0.0,
    (HIGH, NONE): 15.0,
    (HIGH, SOME): 7.5,
    (HIGH, EXPERIENCED): 0.0,
}
# (animal's noise level, adopter's housing) -> points.
NOISE_X_HOUSING = {
    (LOW, APARTMENT): 0.0,
    (LOW, NO_YARD): 0.0,
    (LOW, WITH_YARD): 0.0,
    (MODERATE, APARTMENT): 5.0,
    (MODERATE, NO_YARD): 0.0,
    (MODERATE, WITH_YARD): 0.0,
    (HIGH, APARTMENT): 10.0,
    (HIGH, NO_YARD): 5.0,
    (HIGH, WITH_YARD): 0.0,
}
# A baby animal: (adopter's time away, adopter's experience) -> points.
BABY_X_TIME_AND_EXPERIENCE = {
    (FEW_HOURS, NONE): 7.5,
    (FEW_HOURS, SOME): 3.75,
    (FEW_HOURS, EXPERIENCED): 0.0,
    (HALF_DAY, NONE): 11.25,
    (HALF_DAY, SOME): 7.5,
    (HALF_DAY, EXPERIENCED): 3.75,
    (MOST_OF_DAY, NONE): 15.0,
    (MOST_OF_DAY, SOME): 11.25,
    (MOST_OF_DAY, EXPERIENCED): 7.5,
}
MAX_PENALTY = {"training_experience": 15, "noise_housing": 10, "baby_care": 15}


def _adopter(**overrides: object) -> MatchmakerProfile:
    answers: dict[str, object] = {
        "user_id": USER_ID,
        "housing": WITH_YARD,
        "activity": MODERATE,
        "time_away": FEW_HOURS,
        "experience": EXPERIENCED,
        "has_children": False,
        "has_dogs": False,
        "has_cats": False,
        **overrides,
    }
    return MatchmakerProfile(**answers)  # type: ignore[arg-type]


def _points(name: str, adopter: MatchmakerProfile, animal: AnimalMatchProfile) -> float:
    penalties = {
        p.interaction.name: p for p in FitGraph.standard().penalties(adopter, animal)
    }
    return penalties[name].points if name in penalties else 0.0


@pytest.mark.parametrize(("pair", "points"), TRAINING_X_EXPERIENCE.items())
def test_training_needs_beyond_the_adopters_experience_cost_points(
    pair: tuple[EnergyLevel, ExperienceLevel], points: float
) -> None:
    training, experience = pair

    result = _points(
        "training_experience",
        _adopter(experience=experience),
        AnimalMatchProfile(training_needs=training),
    )

    assert result == pytest.approx(points)


@pytest.mark.parametrize(("pair", "points"), NOISE_X_HOUSING.items())
def test_noise_beyond_what_the_home_tolerates_costs_points(
    pair: tuple[EnergyLevel, HousingType], points: float
) -> None:
    noise, housing = pair

    result = _points(
        "noise_housing",
        _adopter(housing=housing),
        AnimalMatchProfile(noise_level=noise),
    )

    assert result == pytest.approx(points)


@pytest.mark.parametrize(("pair", "points"), BABY_X_TIME_AND_EXPERIENCE.items())
def test_a_baby_animal_costs_points_for_time_away_and_missing_experience(
    pair: tuple[TimeAway, ExperienceLevel], points: float
) -> None:
    away, experience = pair

    result = _points(
        "baby_care",
        _adopter(time_away=away, experience=experience),
        AnimalMatchProfile(life_stage=LifeStage.BABY),
    )

    assert result == pytest.approx(points)


@pytest.mark.parametrize("stage", [LifeStage.ADULT, LifeStage.SENIOR, None])
def test_only_a_baby_animal_gets_the_baby_edge(stage: LifeStage | None) -> None:
    worst_adopter = _adopter(time_away=MOST_OF_DAY, experience=NONE)

    assert (
        _points("baby_care", worst_adopter, AnimalMatchProfile(life_stage=stage)) == 0
    )


def test_an_edge_never_fires_on_an_answer_the_owner_left_blank() -> None:
    worst_adopter = _adopter(housing=APARTMENT, time_away=MOST_OF_DAY, experience=NONE)

    assert FitGraph.standard().penalties(worst_adopter, AnimalMatchProfile()) == []


def test_penalties_come_in_a_fixed_order_with_a_reason_each() -> None:
    worst_adopter = _adopter(housing=APARTMENT, time_away=MOST_OF_DAY, experience=NONE)
    everything_wrong = AnimalMatchProfile(
        training_needs=HIGH, noise_level=HIGH, life_stage=LifeStage.BABY
    )

    penalties = FitGraph.standard().penalties(worst_adopter, everything_wrong)

    assert [p.interaction.name for p in penalties] == list(MAX_PENALTY)
    assert all(p.reason.kind is ReasonKind.CONCERN for p in penalties)
    assert len({p.reason for p in penalties}) == len(penalties)


def test_each_edge_carries_the_agreed_maximum_penalty() -> None:
    interactions = FitGraph.standard().interactions

    assert {i.name: i.max_penalty for i in interactions} == MAX_PENALTY


def test_the_total_penalty_is_the_plain_sum_below_the_cap() -> None:
    graph = FitGraph.standard()
    penalties = graph.penalties(
        _adopter(experience=NONE), AnimalMatchProfile(training_needs=HIGH)
    )

    assert graph.total_penalty(penalties) == pytest.approx(15.0)


def test_stacked_penalties_are_capped_but_every_reason_still_shows() -> None:
    graph = FitGraph.standard()
    worst_adopter = _adopter(housing=APARTMENT, time_away=MOST_OF_DAY, experience=NONE)
    everything_wrong = AnimalMatchProfile(
        training_needs=HIGH, noise_level=HIGH, life_stage=LifeStage.BABY
    )

    penalties = graph.penalties(worst_adopter, everything_wrong)

    # 15 + 10 + 15 = 40 points raw, held at the agreed cap.
    assert sum(p.points for p in penalties) == pytest.approx(40.0)
    assert graph.total_penalty(penalties) == pytest.approx(25.0)
    assert len(penalties) == 3
