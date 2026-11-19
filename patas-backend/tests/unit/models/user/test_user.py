from uuid import UUID

import pytest

from patas_backend.models.user import InvalidUser, User

USER_ID = UUID("0b1f2a3c-4d5e-4f60-8a7b-9c0d1e2f3a4b")


def test_provision_creates_a_regular_user() -> None:
    user = User.provision(id=USER_ID, name="Ana", email="ana@example.com")

    assert (user.id, user.name, user.email) == (USER_ID, "Ana", "ana@example.com")
    assert user.is_platform_admin is False


@pytest.mark.parametrize("name", ["", "   "])
def test_rejects_blank_name(name: str) -> None:
    with pytest.raises(InvalidUser):
        User.provision(id=USER_ID, name=name, email="ana@example.com")


@pytest.mark.parametrize("email", ["", "   ", "no-at-sign", "@example.com"])
def test_rejects_malformed_email(email: str) -> None:
    with pytest.raises(InvalidUser):
        User.provision(id=USER_ID, name="Ana", email=email)


def test_trims_surrounding_whitespace_in_name_and_email() -> None:
    user = User.provision(id=USER_ID, name="  Ana  ", email=" ana@example.com ")

    assert (user.name, user.email) == ("Ana", "ana@example.com")


def test_invariants_hold_when_built_directly() -> None:
    with pytest.raises(InvalidUser):
        User(id=USER_ID, name="   ", email="ana@example.com", username="ana")


def test_change_name_updates_and_trims() -> None:
    user = User.provision(id=USER_ID, name="Ana", email="ana@example.com")
    user.change_name("  Ana Silva  ")
    assert user.name == "Ana Silva"


@pytest.mark.parametrize("name", ["", "   "])
def test_change_name_rejects_blank(name: str) -> None:
    user = User.provision(id=USER_ID, name="Ana", email="ana@example.com")
    with pytest.raises(InvalidUser):
        user.change_name(name)
    assert user.name == "Ana"


def test_a_provisioned_user_gets_a_username_from_the_name() -> None:
    user = User.provision(id=USER_ID, name="Ana Demo", email="ana@example.com")
    assert user.username == "ana_demo"


def test_change_username_keeps_it_as_typed() -> None:
    user = User.provision(id=USER_ID, name="Ana", email="ana@example.com")
    user.change_username("  Ana.Demo  ")
    assert user.username == "Ana.Demo"


def test_change_username_refuses_a_malformed_one_and_keeps_the_old() -> None:
    user = User.provision(id=USER_ID, name="Ana", email="ana@example.com")
    with pytest.raises(InvalidUser):
        user.change_username("ana demo")
    assert user.username == "ana"


def test_a_stored_username_is_checked_when_loaded() -> None:
    with pytest.raises(InvalidUser):
        User(id=USER_ID, name="Ana", email="ana@example.com", username=".ana")
