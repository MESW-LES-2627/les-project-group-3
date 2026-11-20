"""drop the animal postal code; the district is the only location

Revision ID: 0009
Revises: 0008
"""

import sqlalchemy as sa

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("animals", "postal_code", schema="patas")


def downgrade() -> None:
    # The column comes back empty: the dropped values cannot be restored.
    op.add_column(
        "animals", sa.Column("postal_code", sa.Text(), nullable=True), schema="patas"
    )
