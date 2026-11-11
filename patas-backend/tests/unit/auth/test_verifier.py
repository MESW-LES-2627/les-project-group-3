import time
from uuid import UUID

import pytest
from token_issuer import AUDIENCE, ISSUER, USER_ID, TokenIssuer

from patas_backend.auth.errors import InvalidToken, UnknownSigningKey
from patas_backend.auth.keys import StaticJwksKeyProvider
from patas_backend.auth.verifier import JwtVerifier


@pytest.fixture
def verifier(issuer: TokenIssuer) -> JwtVerifier:
    return JwtVerifier(
        StaticJwksKeyProvider(issuer.jwks()), issuer=ISSUER, audience=AUDIENCE
    )


def test_accepts_a_valid_token(verifier: JwtVerifier, issuer: TokenIssuer) -> None:
    principal = verifier.verify(issuer.token())

    assert principal.id == UUID(USER_ID)
    assert (principal.email, principal.name) == ("ana@example.com", "Ana")


def test_rejects_an_expired_token(verifier: JwtVerifier, issuer: TokenIssuer) -> None:
    with pytest.raises(InvalidToken):
        verifier.verify(issuer.token(exp=int(time.time()) - 10))


def test_rejects_a_token_without_expiry(
    verifier: JwtVerifier, issuer: TokenIssuer
) -> None:
    with pytest.raises(InvalidToken):
        verifier.verify(issuer.token(drop=["exp"]))


def test_rejects_a_token_signed_by_another_key(
    verifier: JwtVerifier, other_issuer: TokenIssuer
) -> None:
    with pytest.raises(InvalidToken):
        verifier.verify(other_issuer.token())


@pytest.mark.parametrize(
    "overrides", [{"iss": "http://evil.example"}, {"aud": "http://evil.example"}]
)
def test_rejects_wrong_issuer_or_audience(
    verifier: JwtVerifier, issuer: TokenIssuer, overrides: dict[str, str]
) -> None:
    with pytest.raises(InvalidToken):
        verifier.verify(issuer.token(**overrides))


def test_rejects_an_unsigned_token(verifier: JwtVerifier, issuer: TokenIssuer) -> None:
    with pytest.raises(InvalidToken):
        verifier.verify(issuer.unsigned_token())


def test_rejects_hs256_signed_with_the_public_key(
    verifier: JwtVerifier, issuer: TokenIssuer
) -> None:
    with pytest.raises(InvalidToken):
        verifier.verify(issuer.hs256_token_signed_with_public_key())


def test_rejects_an_unknown_key_id(verifier: JwtVerifier) -> None:
    unknown = TokenIssuer(kid="rotated-away")

    with pytest.raises(UnknownSigningKey):
        verifier.verify(unknown.token())


@pytest.mark.parametrize("token", ["", "not.a.jwt", "a.b.c"])
def test_rejects_garbage(verifier: JwtVerifier, token: str) -> None:
    with pytest.raises(InvalidToken):
        verifier.verify(token)


@pytest.mark.parametrize("overrides", [{"sub": "not-a-uuid"}, {"name": "   "}])
def test_rejects_valid_signature_with_invalid_claims(
    verifier: JwtVerifier, issuer: TokenIssuer, overrides: dict[str, str]
) -> None:
    with pytest.raises(InvalidToken):
        verifier.verify(issuer.token(**overrides))
