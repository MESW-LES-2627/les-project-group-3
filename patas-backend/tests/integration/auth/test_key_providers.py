import pytest
from token_issuer import AUDIENCE, ISSUER, USER_ID, TokenIssuer

from patas_backend.auth.errors import KeysUnavailable, UnknownSigningKey
from patas_backend.auth.keys import RemoteJwksKeyProvider
from patas_backend.auth.verifier import JwtVerifier


def _verifier(url: str) -> JwtVerifier:
    return JwtVerifier(RemoteJwksKeyProvider(url), issuer=ISSUER, audience=AUDIENCE)


def test_verifies_a_token_using_keys_fetched_over_http(
    issuer: TokenIssuer, jwks_url: str
) -> None:
    principal = _verifier(jwks_url).verify(issuer.token())

    assert str(principal.id) == USER_ID


def test_unknown_key_id_is_rejected_not_reported_as_an_outage(
    jwks_url: str,
) -> None:
    unknown = TokenIssuer(kid="rotated-away")

    with pytest.raises(UnknownSigningKey):
        _verifier(jwks_url).verify(unknown.token())


def test_unreachable_jwks_is_reported_as_unavailable(issuer: TokenIssuer) -> None:
    nothing_listens_here = "http://127.0.0.1:1/jwks"

    with pytest.raises(KeysUnavailable):
        _verifier(nothing_listens_here).verify(issuer.token())
