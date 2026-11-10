from dataclasses import fields
from uuid import UUID

import pytest

from patas_backend.models.animal import (
    Animal,
    AnimalCompatibility,
    AnimalMatchProfile,
    AnimalSize,
    FirstTimeOwnerSuitability,
    Species,
)
from patas_backend.models.matching import (
    EnergyLevel,
    ExperienceLevel,
    LifeStage,
    TimeAway,
)
from patas_backend.models.matchmaker_profile import MatchmakerProfile

OWNER_ID = UUID("0b1f2a3c-4d5e-4f60-8a7b-9c0d1e2f3a4b")

# Each answer an adopter gives, and the animal value it is compared with.
COUNTERPART = {
    "housing": "space_needed",
    "activity": "activity",
    "time_away": "max_time_alone",
    "experience": "experience_needed",
    "has_children": "safe_with_children",
    "has_dogs": "safe_with_dogs",
    "has_cats": "safe_with_cats",
}
# The agreed translation tables, spelled out so every source value must be listed.
MAX_TIME_ALONE = {
    EnergyLevel.LOW: TimeAway.FEW_HOURS,
    EnergyLevel.MODERATE: TimeAway.HALF_DAY,
    EnergyLevel.HIGH: TimeAway.MOST_OF_DAY,
}
EXPERIENCE_NEEDED = {
    FirstTimeOwnerSuitability.YES: ExperienceLevel.NONE,
    FirstTimeOwnerSuitability.WITH_SUPPORT: ExperienceLevel.SOME,
    FirstTimeOwnerSuitability.NO: ExperienceLevel.EXPERIENCED,
    FirstTimeOwnerSuitability.UNKNOWN: None,
}
SAFE_WITH = {
    AnimalCompatibility.YES: True,
    AnimalCompatibility.NO: False,
    AnimalCompatibility.WITH_SUPERVISION: None,
    AnimalCompatibility.UNKNOWN: None,
}


def _animal(**overrides: object) -> Animal:
    return Animal.publish(
        **{"owner_id": OWNER_ID, "name": "Rex", "species": Species.DOG, **overrides}
    )


def test_an_animal_with_no_answers_projects_to_nothing_known() -> None:
    projection = _animal().match_profile()

    # A missing answer is never turned into a "no".
    assert all(getattr(projection, f.name) is None for f in fields(projection))


@pytest.mark.parametrize("level", EnergyLevel)
def test_activity_is_carried_over_as_given(level: EnergyLevel) -> None:
    assert _animal(activity_level=level).match_profile().activity is level


@pytest.mark.parametrize("tolerance", EnergyLevel)
def test_tolerance_for_time_alone_becomes_the_longest_time_alone(
    tolerance: EnergyLevel,
) -> None:
    projection = _animal(tolerance_for_time_alone=tolerance).match_profile()

    assert projection.max_time_alone is MAX_TIME_ALONE[tolerance]


def test_more_tolerance_never_means_a_shorter_time_alone() -> None:
    times = [
        _animal(tolerance_for_time_alone=t).match_profile().max_time_alone
        for t in EnergyLevel
    ]

    assert times == sorted(times, key=list(TimeAway).index)


@pytest.mark.parametrize("suitability", FirstTimeOwnerSuitability)
def test_first_time_owner_answer_becomes_the_experience_needed(
    suitability: FirstTimeOwnerSuitability,
) -> None:
    projection = _animal(suitable_for_first_time_owners=suitability).match_profile()

    assert projection.experience_needed is EXPERIENCE_NEEDED[suitability]


def test_a_more_demanding_animal_never_needs_less_experience() -> None:
    # Least to most demanding for a newcomer. The enum's own order is not that.
    demanding = [
        FirstTimeOwnerSuitability.YES,
        FirstTimeOwnerSuitability.WITH_SUPPORT,
        FirstTimeOwnerSuitability.NO,
    ]
    needed = [
        _animal(suitable_for_first_time_owners=s).match_profile().experience_needed
        for s in demanding
    ]

    assert needed == sorted(needed, key=list(ExperienceLevel).index)


@pytest.mark.parametrize("answer", AnimalCompatibility)
@pytest.mark.parametrize(
    ("source", "target"),
    [
        ("behaves_well_with_children", "safe_with_children"),
        ("behaves_well_with_dogs", "safe_with_dogs"),
        ("behaves_well_with_cats", "safe_with_cats"),
    ],
)
def test_behaviour_with_others_becomes_safe_unsafe_or_untested(
    source: str, target: str, answer: AnimalCompatibility
) -> None:
    projection = _animal(**{source: answer}).match_profile()

    assert getattr(projection, target) is SAFE_WITH[answer]


@pytest.mark.parametrize("space", AnimalSize)
def test_space_requirement_is_carried_over_as_the_space_needed(
    space: AnimalSize,
) -> None:
    assert _animal(space_requirement=space).match_profile().space_needed is space


def test_size_is_exposed_but_never_used_to_guess_the_space_needed() -> None:
    projection = _animal(size=AnimalSize.LARGE).match_profile()

    assert projection.size is AnimalSize.LARGE
    assert projection.space_needed is None


def test_every_adopter_answer_has_an_animal_counterpart() -> None:
    answers = {f.name for f in fields(MatchmakerProfile)} - {"user_id"}

    assert set(COUNTERPART) == answers
    assert set(COUNTERPART.values()) <= {f.name for f in fields(AnimalMatchProfile)}


def test_only_edge_context_values_have_no_adopter_answer() -> None:
    unpaired = {f.name for f in fields(AnimalMatchProfile)} - set(COUNTERPART.values())

    # Scoring reads these only against an adopter answer, as an edge of the graph.
    assert unpaired == {"size", "training_needs", "noise_level", "life_stage"}


@pytest.mark.parametrize("level", EnergyLevel)
@pytest.mark.parametrize(
    ("source", "target"),
    [("training_needs", "training_needs"), ("noise_level", "noise_level")],
)
def test_training_needs_and_noise_level_are_carried_over_as_given(
    source: str, target: str, level: EnergyLevel
) -> None:
    projection = _animal(**{source: level}).match_profile()

    assert getattr(projection, target) is level


@pytest.mark.parametrize(
    ("age_in_months", "stage"),
    [
        (0, LifeStage.BABY),
        (11, LifeStage.BABY),
        (12, LifeStage.ADULT),
        (95, LifeStage.ADULT),
        (96, LifeStage.SENIOR),
        (200, LifeStage.SENIOR),
    ],
)
def test_age_becomes_a_life_stage_at_the_agreed_thresholds(
    age_in_months: int, stage: LifeStage
) -> None:
    assert _animal(age_in_months=age_in_months).match_profile().life_stage is stage


def test_an_unknown_age_is_never_guessed_as_a_life_stage() -> None:
    assert _animal(age_in_months=None).match_profile().life_stage is None


def test_the_projection_is_a_snapshot_that_follows_later_changes() -> None:
    animal = _animal(activity_level=EnergyLevel.LOW)
    before = animal.match_profile()

    animal.activity_level = EnergyLevel.HIGH

    assert before.activity is EnergyLevel.LOW
    assert animal.match_profile().activity is EnergyLevel.HIGH


def test_the_research_examples_translate_as_the_matching_research_expects() -> None:
    # Bolinhas, Luna and Max from docs/research/MatchingAlgorithms.md. The doc's
    # needs_yard is our space_requirement; what the doc does not say stays blank.
    bolinhas = _animal(
        activity_level=EnergyLevel.HIGH,
        space_requirement=AnimalSize.LARGE,
        behaves_well_with_dogs=AnimalCompatibility.NO,
        behaves_well_with_cats=AnimalCompatibility.NO,
    )
    luna = _animal(
        species=Species.CAT,
        activity_level=EnergyLevel.LOW,
        space_requirement=AnimalSize.SMALL,
        behaves_well_with_children=AnimalCompatibility.NO,
        behaves_well_with_cats=AnimalCompatibility.YES,
        suitable_for_first_time_owners=FirstTimeOwnerSuitability.YES,
    )
    max_ = _animal(
        activity_level=EnergyLevel.MODERATE,
        behaves_well_with_children=AnimalCompatibility.YES,
        behaves_well_with_cats=AnimalCompatibility.UNKNOWN,
        suitable_for_first_time_owners=FirstTimeOwnerSuitability.YES,
    )

    assert bolinhas.match_profile() == AnimalMatchProfile(
        activity=EnergyLevel.HIGH,
        space_needed=AnimalSize.LARGE,
        safe_with_dogs=False,
        safe_with_cats=False,
    )
    assert luna.match_profile() == AnimalMatchProfile(
        activity=EnergyLevel.LOW,
        space_needed=AnimalSize.SMALL,
        experience_needed=ExperienceLevel.NONE,
        safe_with_children=False,
        safe_with_cats=True,
    )
    # Cats were never tested: untested, not "no".
    assert max_.match_profile() == AnimalMatchProfile(
        activity=EnergyLevel.MODERATE,
        experience_needed=ExperienceLevel.NONE,
        safe_with_children=True,
    )
