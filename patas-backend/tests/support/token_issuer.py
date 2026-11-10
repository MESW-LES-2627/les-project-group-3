import time
from collections.abc import Iterable
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from jwt.algorithms import OKPAlgorithm

KID = "test-key"
ISSUER = "http://localhost:3000"
AUDIENCE = "http://localhost:3000"
USER_ID = "0b1f2a3c-4d5e-4f60-8a7b-9c0d1e2f3a4b"


class TokenIssuer:
    """Plays the Next.js / Better-Auth side: owns a keypair and signs real JWTs."""

    def __init__(self, kid: str = KID) -> None:
        self.kid = kid
        self._private_key = Ed25519PrivateKey.generate()

    def jwks(self) -> dict[str, Any]:
        public = OKPAlgorithm.to_jwk(self._private_key.public_key(), as_dict=True)
        return {"keys": [{**public, "kid": self.kid, "alg": "EdDSA", "use": "sig"}]}

    def _payload(
        self, drop: Iterable[str], overrides: dict[str, Any]
    ) -> dict[str, Any]:
        now = int(time.time())
        payload: dict[str, Any] = {
            "sub": USER_ID,
            "email": "ana@example.com",
            "name": "Ana",
            "iss": ISSUER,
            "aud": AUDIENCE,
            "iat": now,
            "exp": now + 900,
            **overrides,
        }
        for claim in drop:
            del payload[claim]
        return payload

    def token(self, *, drop: Iterable[str] = (), **overrides: Any) -> str:
        return jwt.encode(
            self._payload(drop, overrides),
            self._private_key,
            algorithm="EdDSA",
            headers={"kid": self.kid},
        )

    def unsigned_token(self) -> str:
        return jwt.encode(
            self._payload((), {}), None, algorithm="none", headers={"kid": self.kid}
        )

    def hs256_token_signed_with_public_key(self) -> str:
        """Algorithm-confusion attack: the public key used as an HMAC secret."""
        public_bytes = self._private_key.public_key().public_bytes(
            Encoding.Raw, PublicFormat.Raw
        )
        return jwt.encode(
            self._payload((), {}),
            public_bytes,
            algorithm="HS256",
            headers={"kid": self.kid},
        )
