import json
from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from patas_backend.models.adoption import ProfileSnapshot
from patas_backend.models.matching import EnergyLevel, ExperienceLevel, TimeAway
from patas_backend.models.matchmaker_profile import HousingType, MatchmakerProfile

EXPECTED_JSON = {
    "housing": "apartment",
    "activity": "moderate",
    "time_away": "half_day",
    "experience": "some",
    "has_children": False,
    "has_dogs": True,
    "has_cats": False,
}


def _profile() -> MatchmakerProfile:
    return MatchmakerProfile(
        user_id=uuid4(),
        housing=HousingType.APARTMENT,
        activity=EnergyLevel.MODERATE,
        time_away=TimeAway.HALF_DAY,
        experience=ExperienceLevel.SOME,
        has_children=False,
        has_dogs=True,
        has_cats=False,
    )


def test_a_snapshot_copies_every_answer_of_the_profile() -> None:
    snapshot = ProfileSnapshot.of(_profile())

    assert snapshot.to_json() == EXPECTED_JSON


def test_a_snapshot_does_not_follow_later_changes_to_the_profile() -> None:
    profile = _profile()
    snapshot = ProfileSnapshot.of(profile)

    profile.housing = HousingType.HOUSE_WITH_YARD
    profile.has_cats = True

    assert snapshot.to_json() == EXPECTED_JSON


def test_the_json_holds_only_plain_json_values() -> None:
    stored = ProfileSnapshot.of(_profile()).to_json()

    assert json.loads(json.dumps(stored)) == stored


def test_a_snapshot_survives_a_json_round_trip() -> None:
    snapshot = ProfileSnapshot.of(_profile())

    assert ProfileSnapshot.from_json(snapshot.to_json()) == snapshot


def test_a_snapshot_cannot_be_changed() -> None:
    snapshot = ProfileSnapshot.of(_profile())

    with pytest.raises(FrozenInstanceError):
        snapshot.has_dogs = False  # type: ignore[misc]
