import pytest

from patas_backend.models.user import InvalidUser, derive_username, validate_username
from patas_backend.models.user.username import username_candidates


@pytest.mark.parametrize(
    "username",
    ["ana", "Ana_Demo", "ana.demo", "a_b", "_ana_", "a" * 30, "a.b.c", "Dan2"],
)
def test_accepts_letters_digits_underscore_and_inner_dots(username: str) -> None:
    assert validate_username(username) == username


@pytest.mark.parametrize(
    "username",
    [
        "",
        "an",  # too short
        "a" * 31,  # too long
        ".ana",
        "ana.",
        "ana demo",
        "ana-demo",
        "anã",
        "ana@x",
    ],
)
def test_refuses_other_usernames(username: str) -> None:
    with pytest.raises(InvalidUser):
        validate_username(username)


def test_trims_surrounding_whitespace() -> None:
    assert validate_username("  ana  ") == "ana"


@pytest.mark.parametrize(
    ("name", "username"),
    [
        ("Ana Demo", "ana_demo"),
        ("José Conceição", "jose_conceicao"),
        ("  Ana   --  Demo!! ", "ana_demo"),
        ("Al", "al_user"),
        ("李", "user"),
        ("Maria " * 10, "maria_maria_maria_maria_maria_"),
    ],
)
def test_derives_a_valid_username_from_a_name(name: str, username: str) -> None:
    assert derive_username(name) == username
    assert validate_username(derive_username(name))


def test_candidates_add_a_number_then_the_fallback_within_30_characters() -> None:
    base = "a" * 30

    candidates = list(username_candidates(base, fallback="1a2b3c4d"))

    assert candidates[:3] == [base, "a" * 29 + "2", "a" * 29 + "3"]
    assert candidates[-1] == "a" * 21 + "_1a2b3c4d"
    assert len(candidates) == 10
    assert all(validate_username(c) for c in candidates)
