from dataclasses import FrozenInstanceError
from uuid import UUID

import pytest

from patas_backend.auth.authenticated_principal import (
    AuthenticatedPrincipal,
    InvalidClaims,
)

USER_ID = UUID("0b1f2a3c-4d5e-4f60-8a7b-9c0d1e2f3a4b")
VALID = {"sub": str(USER_ID), "email": "ana@example.com", "name": "Ana"}


def _without(claim: str) -> dict[str, object]:
    return {key: value for key, value in VALID.items() if key != claim}


def test_builds_from_valid_claims() -> None:
    principal = AuthenticatedPrincipal.from_claims(VALID)

    assert (principal.id, principal.email, principal.name) == (
        USER_ID,
        "ana@example.com",
        "Ana",
    )


def test_ignores_extra_claims() -> None:
    claims = {**VALID, "iat": 1, "exp": 2, "iss": "x", "aud": "y", "role": "admin"}

    principal = AuthenticatedPrincipal.from_claims(claims)

    assert principal.id == USER_ID


@pytest.mark.parametrize(
    "claims",
    [
        {**VALID, "sub": "not-a-uuid"},
        {**VALID, "sub": 123},
        {**VALID, "sub": None},
        _without("sub"),
        {**VALID, "name": "   "},
        {**VALID, "name": 7},
        _without("name"),
        {**VALID, "email": "no-at-sign"},
        {**VALID, "email": ["a@b.c"]},
        _without("email"),
    ],
)
def test_rejects_invalid_claims(claims: dict[str, object]) -> None:
    with pytest.raises(InvalidClaims):
        AuthenticatedPrincipal.from_claims(claims)


def test_is_immutable() -> None:
    principal = AuthenticatedPrincipal.from_claims(VALID)

    with pytest.raises(FrozenInstanceError):
        principal.name = "Someone else"  # type: ignore[misc]
