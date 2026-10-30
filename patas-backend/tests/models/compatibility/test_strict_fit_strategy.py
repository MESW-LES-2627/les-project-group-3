from uuid import UUID

from patas_backend.models.animal import AnimalMatchProfile, AnimalSize
from patas_backend.models.compatibility import (
    CompatibilityResult,
    FitGraph,
    StrictFitStrategy,
    rules,
)
from patas_backend.models.compatibility.fit_graph import STANDARD_DIMENSIONS
from patas_backend.models.matching import (
    EnergyLevel,
    ExperienceLevel,
    LifeStage,
    TimeAway,
)
from patas_backend.models.matchmaker_profile import HousingType, MatchmakerProfile

USER_ID = UUID("0b1f2a3c-4d5e-4f60-8a7b-9c0d1e2f3a4b")


def _texts(result: CompatibilityResult) -> tuple[str, ...]:
    return tuple(reason.text for reason in result.reasons)


def _adopter(**overrides: object) -> MatchmakerProfile:
    # By default an adopter every lifestyle dimension of _animal() fits in full.
    answers: dict[str, object] = {
        "user_id": USER_ID,
        "housing": HousingType.HOUSE_WITH_YARD,
        "activity": EnergyLevel.MODERATE,
        "time_away": TimeAway.FEW_HOURS,
        "experience": ExperienceLevel.NONE,
        "has_children": False,
        "has_dogs": False,
        "has_cats": False,
        **overrides,
    }
    return MatchmakerProfile(**answers)  # type: ignore[arg-type]


def _animal(**overrides: object) -> AnimalMatchProfile:
    answers: dict[str, object] = {
        "activity": EnergyLevel.MODERATE,
        "max_time_alone": TimeAway.FEW_HOURS,
        "experience_needed": ExperienceLevel.NONE,
        "space_needed": AnimalSize.SMALL,
        **overrides,
    }
    return AnimalMatchProfile(**answers)  # type: ignore[arg-type]


def test_the_worked_example_scores_38_where_loose_scores_75() -> None:
    # Time alone and space are one step short: the weakest link halves the 0.75.
    adopter = _adopter(
        housing=HousingType.APARTMENT,
        time_away=TimeAway.HALF_DAY,
        experience=ExperienceLevel.SOME,
    )
    animal = _animal(space_needed=AnimalSize.MEDIUM)

    result = StrictFitStrategy().evaluate(adopter, animal)

    assert result.score == 38  # 37.5, rounded half up
    assert result.is_compatible
    assert _texts(result) == (
        rules.ACTIVITY_WORDING.fits,
        rules.TIME_ALONE_WORDING.partly,
        rules.EXPERIENCE_WORDING.fits,
        rules.SPACE_WORDING.partly,
    )


def test_one_step_short_on_one_critical_dimension_scales_the_score_by_its_fit() -> None:
    # Time alone fits 0.5, the rest 1: base 0.875, weakest 0.5.
    result = StrictFitStrategy().evaluate(
        _adopter(time_away=TimeAway.HALF_DAY), _animal()
    )

    assert result.score == 44  # 43.75


def test_two_steps_short_on_a_critical_dimension_hides_the_animal() -> None:
    result = StrictFitStrategy().evaluate(
        _adopter(time_away=TimeAway.MOST_OF_DAY), _animal()
    )

    assert not result.is_compatible
    assert result.score == 0
    assert _texts(result) == (rules.TIME_ALONE_WORDING.misfit,)


def test_a_household_member_the_animal_is_not_safe_with_hides_it() -> None:
    result = StrictFitStrategy().evaluate(
        _adopter(has_dogs=True), _animal(safe_with_dogs=False)
    )

    assert not result.is_compatible
    assert _texts(result) == (rules.household_wording("dogs").misfit,)


def test_a_blank_answer_costs_through_the_average_but_is_not_the_weakest_link() -> None:
    # Space left blank counts 0.25: base (1 + 1 + 1 + 0.25) / 4, and no scaling.
    result = StrictFitStrategy().evaluate(_adopter(), _animal(space_needed=None))

    assert result.is_compatible
    assert result.score == 81  # 81.25
    assert result.reasons[-1].text == rules.SPACE_WORDING.unknown


def test_an_animal_with_nothing_answered_is_low_but_still_shown() -> None:
    result = StrictFitStrategy().evaluate(_adopter(), AnimalMatchProfile())

    assert result.is_compatible
    assert result.score == 25


def test_a_blank_household_answer_counts_a_quarter_and_never_hides_the_animal() -> None:
    # Four lifestyle dimensions at 1, children at 0.25 with weight 2: (4 + 0.5) / 6.
    result = StrictFitStrategy().evaluate(_adopter(has_children=True), _animal())

    assert result.is_compatible
    assert result.score == 75
    assert rules.household_wording("children").unknown in _texts(result)


def test_an_edge_takes_its_full_penalty_off() -> None:
    result = StrictFitStrategy().evaluate(
        _adopter(), _animal(training_needs=EnergyLevel.HIGH)
    )

    assert result.score == 85  # 100 - 15
    assert result.reasons[-1].text == rules.EDGE_REASON["training_experience"]


def test_stacked_edges_take_the_cap_off_in_full() -> None:
    # Training 15 + noise 10 + baby 15 = 40, held at the cap of 25.
    adopter = _adopter(
        housing=HousingType.APARTMENT,
        time_away=TimeAway.MOST_OF_DAY,
        experience=ExperienceLevel.NONE,
    )
    animal = _animal(
        max_time_alone=TimeAway.MOST_OF_DAY,
        space_needed=AnimalSize.SMALL,
        training_needs=EnergyLevel.HIGH,
        noise_level=EnergyLevel.HIGH,
        life_stage=LifeStage.BABY,
    )

    result = StrictFitStrategy().evaluate(adopter, animal)

    assert result.score == 75
    assert len(result.reasons) == 7  # four dimensions and three edges


def test_a_graph_without_critical_dimensions_is_not_scaled() -> None:
    activity_only = FitGraph(dimensions=(STANDARD_DIMENSIONS[0],))

    result = StrictFitStrategy(activity_only).evaluate(
        _adopter(), _animal(activity=EnergyLevel.HIGH)
    )

    assert result.score == 50
