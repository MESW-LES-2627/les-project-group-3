"""add animal photos

Revision ID: 0010
Revises: 0009
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "animals",
        sa.Column(
            "photo_urls",
            postgresql.ARRAY(sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        schema="patas",
    )


def downgrade() -> None:
    op.drop_column("animals", "photo_urls", schema="patas")
