from uuid import UUID

import pytest

from patas_backend.models.matching import EnergyLevel, ExperienceLevel, TimeAway
from patas_backend.models.matchmaker_profile import (
    HousingType,
    InvalidMatchmakerProfile,
    MatchmakerProfile,
)

USER_ID = UUID("5d0c7a52-3b1e-4c8f-9a6d-2e4f8b1c7d90")

ANSWERS = (
    "housing", "activity", "time_away", "experience",
    "has_children", "has_dogs", "has_cats",
)  # fmt: skip


def _profile(**overrides: object) -> MatchmakerProfile:
    # Carla's answers from AT-07.
    return MatchmakerProfile(
        **{
            "user_id": USER_ID,
            "housing": HousingType.APARTMENT,
            "activity": EnergyLevel.LOW,
            "time_away": TimeAway.FEW_HOURS,
            "experience": ExperienceLevel.SOME,
            "has_children": False,
            "has_dogs": False,
            "has_cats": True,
            **overrides,
        }
    )


def test_a_complete_profile_keeps_every_answer() -> None:
    profile = _profile()

    assert profile.user_id == USER_ID
    assert profile.housing is HousingType.APARTMENT
    assert profile.activity is EnergyLevel.LOW
    assert profile.time_away is TimeAway.FEW_HOURS
    assert profile.experience is ExperienceLevel.SOME
    assert (profile.has_children, profile.has_dogs, profile.has_cats) == (
        False, False, True,
    )  # fmt: skip


def test_an_answer_given_as_text_becomes_its_value() -> None:
    assert _profile(housing="house_with_yard").housing is HousingType.HOUSE_WITH_YARD


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("housing", "castle"),
        ("activity", "extreme"),
        ("time_away", "forever"),
        ("experience", "expert"),
    ],
)
def test_a_value_outside_the_scale_is_rejected(field: str, value: str) -> None:
    with pytest.raises(InvalidMatchmakerProfile, match=field):
        _profile(**{field: value})


@pytest.mark.parametrize("field", ANSWERS)
def test_a_missing_answer_is_rejected(field: str) -> None:
    with pytest.raises(InvalidMatchmakerProfile, match=field):
        _profile(**{field: None})


@pytest.mark.parametrize(("field", "value"), [("has_children", "no"), ("has_cats", 1)])
def test_a_household_answer_must_be_yes_or_no(field: str, value: object) -> None:
    # "no" is a truthy string: accepting it would silently mean "yes".
    with pytest.raises(InvalidMatchmakerProfile, match=field):
        _profile(**{field: value})
