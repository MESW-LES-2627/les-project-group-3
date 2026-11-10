import pytest
from profiles import make_adopter, make_animal, texts

from patas_backend.models.animal import AnimalMatchProfile, AnimalSize
from patas_backend.models.compatibility import (
    FitGraph,
    FitGraphStrategy,
    LooseFitStrategy,
    ReasonKind,
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
from patas_backend.models.matchmaker_profile import HousingType


def test_the_worked_example_scores_75_and_explains_each_dimension_in_order() -> None:
    # Apartment, away half a day, some experience; the animal tolerates a few hours
    # alone and needs medium space. Time alone and space are one step short each.
    adopter = make_adopter(
        housing=HousingType.APARTMENT,
        time_away=TimeAway.HALF_DAY,
        experience=ExperienceLevel.SOME,
    )
    animal = make_animal(space_needed=AnimalSize.MEDIUM)

    result = LooseFitStrategy().evaluate(adopter, animal)

    assert result.score == 75
    assert result.is_compatible
    assert texts(result) == (
        rules.ACTIVITY_WORDING.fits,
        rules.TIME_ALONE_WORDING.partly,
        rules.EXPERIENCE_WORDING.fits,
        rules.SPACE_WORDING.partly,
    )
    assert [r.kind for r in result.reasons] == [
        ReasonKind.STRENGTH,
        ReasonKind.CONCERN,
        ReasonKind.STRENGTH,
        ReasonKind.CONCERN,
    ]


def test_an_animal_with_nothing_answered_sits_in_the_middle() -> None:
    result = LooseFitStrategy().evaluate(make_adopter(), AnimalMatchProfile())

    assert result.score == 50
    assert result.is_compatible
    assert texts(result) == (
        rules.ACTIVITY_WORDING.unknown,
        rules.TIME_ALONE_WORDING.unknown,
        rules.EXPERIENCE_WORDING.unknown,
        rules.SPACE_WORDING.unknown,
    )
    assert {r.kind for r in result.reasons} == {ReasonKind.UNKNOWN}


def test_a_household_member_the_animal_is_not_safe_with_hides_it() -> None:
    result = LooseFitStrategy().evaluate(
        make_adopter(has_children=True), make_animal(safe_with_children=False)
    )

    assert not result.is_compatible
    assert result.score == 0
    assert texts(result) == (rules.household_wording("children").misfit,)
    assert result.reasons[0].kind is ReasonKind.CONCERN


def test_a_two_step_shortfall_on_a_lifestyle_dimension_lowers_the_score_only() -> None:
    # Away most of the day, for an animal that tolerates a few hours: fit 0.
    result = LooseFitStrategy().evaluate(
        make_adopter(time_away=TimeAway.MOST_OF_DAY), make_animal()
    )

    assert result.is_compatible
    assert result.score == 75
    assert rules.TIME_ALONE_WORDING.misfit in texts(result)


def test_a_household_answer_weighs_double_a_lifestyle_one() -> None:
    # Time alone fits 0; children fits 1 with weight 2: (1 + 0 + 1 + 1 + 2) / 6.
    result = LooseFitStrategy().evaluate(
        make_adopter(has_children=True, time_away=TimeAway.MOST_OF_DAY),
        make_animal(safe_with_children=True),
    )

    assert result.score == 83


def test_a_blank_household_answer_counts_half_and_never_hides_themake_animal() -> None:
    # Four lifestyle dimensions at 1, children at 0.5 with weight 2: (4 + 1) / 6.
    result = LooseFitStrategy().evaluate(make_adopter(has_children=True), make_animal())

    assert result.is_compatible
    assert result.score == 83
    assert rules.household_wording("children").unknown in texts(result)


def test_an_edge_takes_half_its_penalty_off_and_adds_its_reason_last() -> None:
    # Training needs high against no experience: 15 points, halved to 7.5.
    result = LooseFitStrategy().evaluate(
        make_adopter(), make_animal(training_needs=EnergyLevel.HIGH)
    )

    assert result.score == 93  # 100 - 7.5 = 92.5, rounded half up
    assert result.reasons[-1].text == rules.EDGE_REASON["training_experience"]
    assert result.reasons[-1].kind is ReasonKind.CONCERN


def test_stacked_edges_are_held_at_the_cap_before_being_halved() -> None:
    # Training 15 + noise 10 + baby 15 = 40, capped at 25, halved to 12.5.
    adopter = make_adopter(
        housing=HousingType.APARTMENT,
        time_away=TimeAway.MOST_OF_DAY,
        experience=ExperienceLevel.NONE,
    )
    animal = make_animal(
        max_time_alone=TimeAway.MOST_OF_DAY,
        space_needed=AnimalSize.SMALL,
        training_needs=EnergyLevel.HIGH,
        noise_level=EnergyLevel.HIGH,
        life_stage=LifeStage.BABY,
    )

    result = LooseFitStrategy().evaluate(adopter, animal)

    assert result.score == 88  # 100 - 12.5 = 87.5, rounded half up
    assert texts(result)[-3:] == (
        rules.EDGE_REASON["training_experience"],
        rules.EDGE_REASON["noise_housing"],
        rules.EDGE_REASON["baby_care"],
    )


def test_the_graph_it_judges_with_can_be_replaced() -> None:
    activity_only = FitGraph(dimensions=(STANDARD_DIMENSIONS[0],))

    result = LooseFitStrategy(activity_only).evaluate(
        make_adopter(), make_animal(activity=EnergyLevel.HIGH)
    )

    assert result.score == 50
    assert texts(result) == (rules.ACTIVITY_WORDING.partly,)


@pytest.mark.parametrize("strategy", [LooseFitStrategy, StrictFitStrategy])
def test_a_graph_with_nothing_that_applies_is_refused_not_divided_by_zero(
    strategy: type[FitGraphStrategy],
) -> None:
    children_only = FitGraph(dimensions=(STANDARD_DIMENSIONS[4],))

    with pytest.raises(ValueError, match="no dimension applies"):
        strategy(children_only).evaluate(make_adopter(), make_animal())
