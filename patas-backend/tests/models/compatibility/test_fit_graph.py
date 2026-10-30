import pytest
from profiles import make_adopter

from patas_backend.models.animal import AnimalMatchProfile, AnimalSize
from patas_backend.models.compatibility import (
    Assessment,
    Dimension,
    FitGraph,
    ReasonKind,
    Wording,
)
from patas_backend.models.matching import EnergyLevel, ExperienceLevel, TimeAway
from patas_backend.models.matchmaker_profile import HousingType, MatchmakerProfile

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
SMALL, MEDIUM, LARGE = AnimalSize.SMALL, AnimalSize.MEDIUM, AnimalSize.LARGE
APARTMENT = HousingType.APARTMENT
NO_YARD = HousingType.HOUSE_NO_YARD
WITH_YARD = HousingType.HOUSE_WITH_YARD

# The agreed placeholder tables, spelled out cell by cell: (adopter, animal) -> fit.
ACTIVITY = {
    (LOW, LOW): 1.0,
    (LOW, MODERATE): 0.5,
    (LOW, HIGH): 0.2,
    (MODERATE, LOW): 0.8,
    (MODERATE, MODERATE): 1.0,
    (MODERATE, HIGH): 0.5,
    (HIGH, LOW): 0.6,
    (HIGH, MODERATE): 0.8,
    (HIGH, HIGH): 1.0,
}
# The animal's longest time alone is a ceiling on the adopter's time away.
TIME_ALONE = {
    (FEW_HOURS, FEW_HOURS): 1.0,
    (FEW_HOURS, HALF_DAY): 1.0,
    (FEW_HOURS, MOST_OF_DAY): 1.0,
    (HALF_DAY, FEW_HOURS): 0.5,
    (HALF_DAY, HALF_DAY): 1.0,
    (HALF_DAY, MOST_OF_DAY): 1.0,
    (MOST_OF_DAY, FEW_HOURS): 0.0,
    (MOST_OF_DAY, HALF_DAY): 0.5,
    (MOST_OF_DAY, MOST_OF_DAY): 1.0,
}
# What the animal needs is a floor under what the adopter has.
EXPERIENCE = {
    (NONE, NONE): 1.0,
    (NONE, SOME): 0.5,
    (NONE, EXPERIENCED): 0.0,
    (SOME, NONE): 1.0,
    (SOME, SOME): 1.0,
    (SOME, EXPERIENCED): 0.5,
    (EXPERIENCED, NONE): 1.0,
    (EXPERIENCED, SOME): 1.0,
    (EXPERIENCED, EXPERIENCED): 1.0,
}
SPACE = {
    (APARTMENT, SMALL): 1.0,
    (APARTMENT, MEDIUM): 0.5,
    (APARTMENT, LARGE): 0.0,
    (NO_YARD, SMALL): 1.0,
    (NO_YARD, MEDIUM): 1.0,
    (NO_YARD, LARGE): 0.5,
    (WITH_YARD, SMALL): 1.0,
    (WITH_YARD, MEDIUM): 1.0,
    (WITH_YARD, LARGE): 1.0,
}
# name -> (weight, critical, safety)
FLAGS = {
    "activity": (1, False, False),
    "time_alone": (1, True, False),
    "experience": (1, True, False),
    "space": (1, True, False),
    "children": (2, True, True),
    "dogs": (2, True, True),
    "cats": (2, True, True),
}
HOUSEHOLD = ["children", "dogs", "cats"]


def _assess(
    adopter: MatchmakerProfile, animal: AnimalMatchProfile
) -> dict[str, Assessment]:
    return {a.dimension.name: a for a in FitGraph.standard().assess(adopter, animal)}


@pytest.mark.parametrize(("pair", "fit"), ACTIVITY.items())
def test_activity_fit_follows_the_table(
    pair: tuple[EnergyLevel, EnergyLevel], fit: float
) -> None:
    adopter, animal = pair
    assessed = _assess(
        make_adopter(activity=adopter), AnimalMatchProfile(activity=animal)
    )

    assert assessed["activity"].fit == fit


@pytest.mark.parametrize(("pair", "fit"), TIME_ALONE.items())
def test_time_alone_fit_follows_the_table(
    pair: tuple[TimeAway, TimeAway], fit: float
) -> None:
    away, longest_alone = pair
    assessed = _assess(
        make_adopter(time_away=away), AnimalMatchProfile(max_time_alone=longest_alone)
    )

    assert assessed["time_alone"].fit == fit


@pytest.mark.parametrize(("pair", "fit"), EXPERIENCE.items())
def test_experience_fit_follows_the_table(
    pair: tuple[ExperienceLevel, ExperienceLevel], fit: float
) -> None:
    has, needed = pair
    assessed = _assess(
        make_adopter(experience=has), AnimalMatchProfile(experience_needed=needed)
    )

    assert assessed["experience"].fit == fit


@pytest.mark.parametrize(("pair", "fit"), SPACE.items())
def test_space_fit_follows_the_table(
    pair: tuple[HousingType, AnimalSize], fit: float
) -> None:
    housing, needed = pair
    assessed = _assess(
        make_adopter(housing=housing), AnimalMatchProfile(space_needed=needed)
    )

    assert assessed["space"].fit == fit


@pytest.mark.parametrize("member", HOUSEHOLD)
@pytest.mark.parametrize(("safe", "fit"), [(True, 1.0), (False, 0.0)])
def test_household_fit_is_full_when_safe_and_zero_when_not(
    member: str, safe: bool, fit: float
) -> None:
    assessed = _assess(
        make_adopter(**{f"has_{member}": True}),
        AnimalMatchProfile(**{f"safe_with_{member}": safe}),
    )

    assert assessed[member].fit == fit


@pytest.mark.parametrize(
    "name", [*HOUSEHOLD, "activity", "time_alone", "experience", "space"]
)
def test_an_animal_answer_left_blank_has_no_fit_and_says_so(name: str) -> None:
    adopter = make_adopter(has_children=True, has_dogs=True, has_cats=True)

    blank = _assess(adopter, AnimalMatchProfile())[name]
    answered = _assess(
        adopter,
        AnimalMatchProfile(
            activity=MODERATE,
            max_time_alone=HALF_DAY,
            experience_needed=NONE,
            space_needed=SMALL,
            safe_with_children=True,
            safe_with_dogs=True,
            safe_with_cats=True,
        ),
    )[name]

    # Never read as a "no": it has no fit at all, and is its own kind of reason.
    assert blank.fit is None
    assert blank.reason.kind is ReasonKind.UNKNOWN
    assert blank.reason != answered.reason


@pytest.mark.parametrize("member", HOUSEHOLD)
def test_a_household_dimension_only_counts_when_the_adopter_has_it(
    member: str,
) -> None:
    unsafe = AnimalMatchProfile(
        safe_with_children=False, safe_with_dogs=False, safe_with_cats=False
    )

    assert member not in _assess(make_adopter(), unsafe)
    assert member in _assess(make_adopter(**{f"has_{member}": True}), unsafe)


def test_assessments_come_in_a_fixed_order() -> None:
    adopter = make_adopter(has_children=True, has_dogs=True, has_cats=True)

    names = [
        a.dimension.name
        for a in FitGraph.standard().assess(adopter, AnimalMatchProfile())
    ]

    assert names == list(FLAGS)


def test_an_adopter_without_household_is_assessed_on_lifestyle_only() -> None:
    assessed = _assess(make_adopter(), AnimalMatchProfile())

    assert list(assessed) == ["activity", "time_alone", "experience", "space"]


def test_dimensions_carry_the_agreed_weights_and_flags() -> None:
    dimensions = FitGraph.standard().dimensions

    assert {d.name: (d.weight, d.critical, d.safety) for d in dimensions} == FLAGS


def test_each_band_of_fit_has_its_own_reason() -> None:
    # Time alone: a few hours is the animal's limit and the adopter is away for...
    reasons = {
        _assess(
            make_adopter(time_away=away), AnimalMatchProfile(max_time_alone=FEW_HOURS)
        )["time_alone"].reason
        for away in TimeAway
    }
    reasons.add(_assess(make_adopter(), AnimalMatchProfile())["time_alone"].reason)

    # Fits, partly, misfit (0.0) and unknown.
    assert len(reasons) == 4


@pytest.mark.parametrize(
    ("away", "kind"),
    [
        (FEW_HOURS, ReasonKind.STRENGTH),
        (HALF_DAY, ReasonKind.CONCERN),
        (MOST_OF_DAY, ReasonKind.CONCERN),
    ],
)
def test_a_reason_is_a_strength_when_it_fits_in_full_and_a_concern_otherwise(
    away: TimeAway, kind: ReasonKind
) -> None:
    # The animal's limit is a few hours: fit 1.0, 0.5 and 0.0 as the adopter is away.
    assessed = _assess(
        make_adopter(time_away=away), AnimalMatchProfile(max_time_alone=FEW_HOURS)
    )

    assert assessed["time_alone"].reason.kind is kind


def test_a_dimension_without_a_partial_wording_refuses_a_partial_fit() -> None:
    # Household tables only give 1 or 0, so they carry no partial wording at all.
    dogs_dimension = next(d for d in FitGraph.standard().dimensions if d.name == "dogs")
    assert dogs_dimension.wording.partly is None

    half_fit = Dimension(
        name="half",
        weight=1,
        critical=False,
        safety=False,
        adopter_value=lambda adopter: adopter.activity,
        animal_value=lambda animal: animal.activity,
        table={(MODERATE, MODERATE): 0.5},
        wording=Wording(fits="fits", misfit="misfit", unknown="unknown"),
    )

    with pytest.raises(ValueError, match="partial"):
        half_fit.assess(make_adopter(), AnimalMatchProfile(activity=MODERATE))
