"""add a unique username to users

Revision ID: 0008
Revises: 0007
"""

import re
import unicodedata

import sqlalchemy as sa

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

MAX_LENGTH = 30


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.Text()), schema="patas")
    _backfill()
    op.alter_column("users", "username", nullable=False, schema="patas")
    op.create_check_constraint(
        "users_username_format_check",
        "users",
        "username ~ '^[A-Za-z0-9_][A-Za-z0-9_.]{1,28}[A-Za-z0-9_]$'",
        schema="patas",
    )
    op.execute(
        "CREATE UNIQUE INDEX idx_users_username_lower ON patas.users (lower(username))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX patas.idx_users_username_lower")
    op.drop_constraint("users_username_format_check", "users", schema="patas")
    op.drop_column("users", "username", schema="patas")


def _backfill() -> None:
    """Give every existing user a username derived from their name.

    The earliest user keeps the plain form and later ones get a number (ana_demo,
    ana_demo2). A copy of the app's rule, so this migration never changes when the
    app does.
    """
    bind = op.get_bind()
    users = bind.execute(
        sa.text("SELECT id, name FROM patas.users ORDER BY created_at, id")
    ).all()
    taken: set[str] = set()
    for user in users:
        base = _derive(user.name)
        username, number = base, 2
        while username in taken:
            suffix = str(number)
            username = base[: MAX_LENGTH - len(suffix)] + suffix
            number += 1
        taken.add(username)
        bind.execute(
            sa.text("UPDATE patas.users SET username = :username WHERE id = :id"),
            {"username": username, "id": user.id},
        )


def _derive(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_name.lower()).strip("_")
    if len(slug) < 3:
        slug = f"{slug}_user" if slug else "user"
    return slug[:MAX_LENGTH]
