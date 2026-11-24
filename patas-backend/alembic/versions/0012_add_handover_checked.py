"""add the handover checklist to adoption applications

Revision ID: 0012
Revises: 0011
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The keys of the ticked items. The domain checks the values, so a new item
    # needs no migration.
    op.add_column(
        "adoption_applications",
        sa.Column(
            "handover_checked",
            postgresql.ARRAY(sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        schema="patas",
    )
    # Like the confirmations: a request that was never accepted has nothing ticked.
    # A declined or withdrawn one may: the ticks happened first.
    op.create_check_constraint(
        "adoption_applications_handover_checked_status_check",
        "adoption_applications",
        "cardinality(handover_checked) = 0 OR status NOT IN ('open', 'closed')",
        schema="patas",
    )


def downgrade() -> None:
    op.drop_constraint(
        "adoption_applications_handover_checked_status_check",
        "adoption_applications",
        schema="patas",
    )
    op.drop_column("adoption_applications", "handover_checked", schema="patas")
