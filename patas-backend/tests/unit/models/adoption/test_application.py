from datetime import UTC, datetime
from uuid import uuid4

import pytest

from patas_backend.models.adoption import (
    AdoptionApplication,
    ApplicationAccepted,
    ApplicationAdopted,
    ApplicationClosed,
    ApplicationDeclined,
    ApplicationStatus,
    ApplicationUnauthorized,
    ApplicationWithdrawn,
    InvalidApplication,
    InvalidTransition,
    ProfileSnapshot,
)
from patas_backend.models.adoption.state import STATES
from patas_backend.models.matching import EnergyLevel, ExperienceLevel, TimeAway
from patas_backend.models.matchmaker_profile import HousingType

S = ApplicationStatus
OWNER, APPLICANT, STRANGER, ANIMAL = uuid4(), uuid4(), uuid4(), uuid4()
NOW = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)
LATER = datetime(2026, 11, 8, 9, 30, tzinfo=UTC)
SNAPSHOT = ProfileSnapshot(
    housing=HousingType.APARTMENT,
    activity=EnergyLevel.MODERATE,
    time_away=TimeAway.HALF_DAY,
    experience=ExperienceLevel.SOME,
    has_children=False,
    has_dogs=True,
    has_cats=False,
)


def _request(**overrides: object) -> AdoptionApplication:
    return AdoptionApplication.request(
        **{
            "animal_id": ANIMAL,
            "owner_id": OWNER,
            "applicant_id": APPLICANT,
            "applicant_note": "Hello",
            "applicant_profile": SNAPSHOT,
            **overrides,
        }
    )


def _application(status: S = S.OPEN) -> AdoptionApplication:
    application = _request()
    application.status = status  # the state is derived from the status
    return application


# action -> (who does it, {status it may start from: status it ends in})
ACTIONS = {
    "accept": (OWNER, {S.OPEN: S.ACCEPTED}),
    "decline": (OWNER, {S.OPEN: S.DECLINED, S.ACCEPTED: S.DECLINED}),
    "withdraw": (APPLICANT, {S.OPEN: S.WITHDRAWN, S.ACCEPTED: S.WITHDRAWN}),
    "close": (None, {S.OPEN: S.CLOSED}),  # the system, not a person
}
ALLOWED = [
    (action, source, target)
    for action, (_, moves) in ACTIONS.items()
    for source, target in moves.items()
]
REFUSED = [
    (action, status)
    for action, (_, moves) in ACTIONS.items()
    for status in S
    if status not in moves
]


def _perform(application: AdoptionApplication, action: str) -> None:
    actor, _ = ACTIONS[action]
    method = getattr(application, action)
    if actor is None:
        method()
    else:
        method(actor)


# --- a new request ----------------------------------------------------------


def test_a_new_request_is_open_and_carries_the_applicants_snapshot() -> None:
    application = _request()

    assert application.status is S.OPEN
    assert application.applicant_profile == SNAPSHOT
    assert application.owner_note is None
    assert application.owner_confirmed_at is None
    assert application.applicant_confirmed_at is None
    assert application.created_at is None


def test_each_request_gets_its_own_id() -> None:
    assert _request().id != _request().id


def test_the_applicant_cannot_be_the_owner() -> None:
    with pytest.raises(InvalidApplication):
        _request(applicant_id=OWNER)
    # Loading from the database goes through the constructor, not request().
    with pytest.raises(InvalidApplication):
        AdoptionApplication(
            id=uuid4(),
            animal_id=ANIMAL,
            owner_id=OWNER,
            applicant_id=OWNER,
            applicant_note="Hello",
            applicant_profile=SNAPSHOT,
        )


def test_every_status_has_exactly_one_state() -> None:
    assert set(STATES) == set(S)
    assert all(state.status is status for status, state in STATES.items())


# --- which changes each status allows --------------------------------------


@pytest.mark.parametrize(("action", "source", "target"), ALLOWED)
def test_each_allowed_change_moves_the_application(
    action: str, source: S, target: S
) -> None:
    application = _application(source)

    _perform(application, action)

    assert application.status is target


@pytest.mark.parametrize(("action", "status"), REFUSED)
def test_every_other_change_is_refused_and_changes_nothing(
    action: str, status: S
) -> None:
    application = _application(status)

    with pytest.raises(InvalidTransition):
        _perform(application, action)

    assert application.status is status
    assert application.pull_events() == []


@pytest.mark.parametrize("status", [s for s in S if s is not S.ACCEPTED])
def test_a_handover_can_only_be_confirmed_while_accepted(status: S) -> None:
    application = _application(status)

    with pytest.raises(InvalidTransition):
        application.confirm_handover(OWNER, NOW)

    assert application.owner_confirmed_at is None
    assert application.status is status


# --- who may do what --------------------------------------------------------


@pytest.mark.parametrize("actor", [APPLICANT, STRANGER])
@pytest.mark.parametrize("action", ["accept", "decline"])
def test_only_the_owner_can_accept_or_decline(action: str, actor: object) -> None:
    application = _application()

    with pytest.raises(ApplicationUnauthorized):
        getattr(application, action)(actor)

    assert application.status is S.OPEN


@pytest.mark.parametrize("actor", [OWNER, STRANGER])
def test_only_the_applicant_can_withdraw(actor: object) -> None:
    application = _application()

    with pytest.raises(ApplicationUnauthorized):
        application.withdraw(actor)

    assert application.status is S.OPEN


def test_only_the_owner_or_the_applicant_can_confirm_a_handover() -> None:
    application = _application(S.ACCEPTED)

    with pytest.raises(ApplicationUnauthorized):
        application.confirm_handover(STRANGER, NOW)

    assert application.owner_confirmed_at is None
    assert application.applicant_confirmed_at is None


def test_who_is_asking_is_checked_before_the_status() -> None:
    application = _application(S.DECLINED)

    with pytest.raises(ApplicationUnauthorized):
        application.accept(STRANGER)


# --- the owner's note -------------------------------------------------------


@pytest.mark.parametrize("action", ["accept", "decline"])
def test_the_owner_note_is_kept_trimmed(action: str) -> None:
    application = _application()

    getattr(application, action)(OWNER, "  Welcome  ")

    assert application.owner_note == "Welcome"


@pytest.mark.parametrize("note", [None, "   "])
@pytest.mark.parametrize("action", ["accept", "decline"])
def test_a_blank_or_missing_note_is_stored_as_none(
    action: str, note: str | None
) -> None:
    application = _application()

    getattr(application, action)(OWNER, note)

    assert application.owner_note is None


# --- events -----------------------------------------------------------------


def test_accepting_records_one_event_that_can_be_pulled_once() -> None:
    application = _application()

    application.accept(OWNER)

    expected = ApplicationAccepted(application_id=application.id, animal_id=ANIMAL)
    assert application.pull_events() == [expected]
    assert application.pull_events() == []


@pytest.mark.parametrize(
    ("source", "was_accepted"), [(S.OPEN, False), (S.ACCEPTED, True)]
)
def test_declining_says_whether_the_request_had_been_accepted(
    source: S, was_accepted: bool
) -> None:
    application = _application(source)

    application.decline(OWNER)

    expected = ApplicationDeclined(
        application_id=application.id, animal_id=ANIMAL, was_accepted=was_accepted
    )
    assert application.pull_events() == [expected]


@pytest.mark.parametrize(
    ("source", "was_accepted"), [(S.OPEN, False), (S.ACCEPTED, True)]
)
def test_withdrawing_says_whether_the_request_had_been_accepted(
    source: S, was_accepted: bool
) -> None:
    application = _application(source)

    application.withdraw(APPLICANT)

    expected = ApplicationWithdrawn(
        application_id=application.id, animal_id=ANIMAL, was_accepted=was_accepted
    )
    assert application.pull_events() == [expected]


def test_closing_records_one_event() -> None:
    application = _application()

    application.close()

    expected = ApplicationClosed(application_id=application.id, animal_id=ANIMAL)
    assert application.pull_events() == [expected]


# --- confirming the handover ------------------------------------------------


def test_each_side_confirms_with_its_own_time() -> None:
    by_owner = _application(S.ACCEPTED)
    by_applicant = _application(S.ACCEPTED)

    by_owner.confirm_handover(OWNER, NOW)
    by_applicant.confirm_handover(APPLICANT, LATER)

    assert (by_owner.owner_confirmed_at, by_owner.applicant_confirmed_at) == (NOW, None)
    assert (by_applicant.owner_confirmed_at, by_applicant.applicant_confirmed_at) == (
        None,
        LATER,
    )


@pytest.mark.parametrize(("first", "second"), [(OWNER, APPLICANT), (APPLICANT, OWNER)])
def test_the_second_confirmation_adopts_in_either_order(
    first: object, second: object
) -> None:
    application = _application(S.ACCEPTED)

    application.confirm_handover(first, NOW)
    assert application.status is S.ACCEPTED
    assert application.pull_events() == []

    application.confirm_handover(second, LATER)

    assert application.status is S.ADOPTED
    assert application.owner_confirmed_at is not None
    assert application.applicant_confirmed_at is not None
    expected = ApplicationAdopted(application_id=application.id, animal_id=ANIMAL)
    assert application.pull_events() == [expected]


@pytest.mark.parametrize("side", [OWNER, APPLICANT])
def test_a_side_cannot_confirm_twice(side: object) -> None:
    application = _application(S.ACCEPTED)
    application.confirm_handover(side, NOW)

    with pytest.raises(InvalidTransition):
        application.confirm_handover(side, LATER)

    assert application.status is S.ACCEPTED
    assert NOW in (application.owner_confirmed_at, application.applicant_confirmed_at)


@pytest.mark.parametrize(
    ("action", "actor", "final"),
    [("decline", OWNER, S.DECLINED), ("withdraw", APPLICANT, S.WITHDRAWN)],
)
def test_a_confirmation_survives_a_later_decline_or_withdrawal(
    action: str, actor: object, final: S
) -> None:
    application = _application(S.ACCEPTED)
    application.confirm_handover(OWNER, NOW)

    getattr(application, action)(actor)

    assert application.status is final
    assert application.owner_confirmed_at == NOW
