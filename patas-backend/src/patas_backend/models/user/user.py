from dataclasses import dataclass
from uuid import UUID


class InvalidUser(ValueError):
    """A User invariant was violated."""


def validate_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise InvalidUser("name must not be blank")
    return cleaned


def validate_email(email: str) -> str:
    cleaned = email.strip()
    # Same rule as the database CHECK: '@' must come after at least one character.
    if cleaned.find("@") < 1:
        raise InvalidUser("email must contain '@' after at least one character")
    return cleaned


@dataclass
class User:
    id: UUID
    name: str
    email: str
    is_platform_admin: bool = False

    def __post_init__(self) -> None:
        # Invariants hold however a User is built (provisioning or loaded from the DB).
        self.name = validate_name(self.name)
        self.email = validate_email(self.email)

    @classmethod
    def provision(cls, *, id: UUID, name: str, email: str) -> "User":
        """Create a user on first login. Admin rights are never granted here."""
        return cls(id=id, name=name, email=email)

    def change_name(self, name: str) -> None:
        """Change the user's name, enforcing domain invariants."""
        self.name = validate_name(name)

