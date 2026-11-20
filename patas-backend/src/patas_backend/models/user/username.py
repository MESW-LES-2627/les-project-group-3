import re
import unicodedata
from collections.abc import Iterator

from patas_backend.models.user.errors import InvalidUser

MAX_LENGTH = 30

# Same rule as the database CHECK: 3 to 30 letters, digits, '_' or '.', and no '.'
# at either end. Uniqueness ignores case; the username is kept as typed.
_PATTERN = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.]{1,28}[A-Za-z0-9_]")


def validate_username(username: str) -> str:
    cleaned = username.strip()
    if not _PATTERN.fullmatch(cleaned):
        raise InvalidUser(
            "username must be 3 to 30 letters, digits, '_' or '.', "
            "and must not start or end with '.'"
        )
    return cleaned


def derive_username(name: str) -> str:
    """A valid username built from a person's name: "Ana Demo" gives "ana_demo".

    Used for users who have not chosen one yet. Accents are dropped, anything else
    that is not a letter or digit becomes '_', and a too-short result is padded.
    """
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_name.lower()).strip("_")
    if len(slug) < 3:
        slug = f"{slug}_user" if slug else "user"
    return slug[:MAX_LENGTH]


def username_candidates(base: str, *, fallback: str) -> Iterator[str]:
    """base, base2 ... base9, then base_<fallback>: the names to try, in order."""
    yield base
    for number in range(2, 10):
        yield _with_suffix(base, str(number))
    yield _with_suffix(base, f"_{fallback}")


def _with_suffix(base: str, suffix: str) -> str:
    return base[: MAX_LENGTH - len(suffix)] + suffix
