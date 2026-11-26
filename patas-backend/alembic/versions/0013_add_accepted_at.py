"""record when an adoption application was accepted

Revision ID: 0013
Revises: 0012
"""

import sqlalchemy as sa

from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The conversation of a request opens when it is accepted and stays readable after
    # it ends (US-21), so the request has to remember that it was accepted.
    op.add_column(
        "adoption_applications",
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        schema="patas",
    )
    # Existing rows: the real moment is unknown, so the request's creation stands in
    # for it. A declined or withdrawn request was accepted if it has a confirmation or
    # a tick, which only an accepted request can have.
    op.execute(
        """
        UPDATE patas.adoption_applications
        SET accepted_at = created_at
        WHERE status IN ('accepted', 'adopted')
           OR (status IN ('declined', 'withdrawn')
               AND (owner_confirmed_at IS NOT NULL
                    OR applicant_confirmed_at IS NOT NULL
                    OR cardinality(handover_checked) > 0))
        """
    )
    # Accepted and adopted always have it; open and closed never do (a request is only
    # closed while open). Declined and withdrawn can be either.
    op.create_check_constraint(
        "adoption_applications_accepted_at_status_check",
        "adoption_applications",
        "status IN ('declined', 'withdrawn') "
        "OR (status IN ('accepted', 'adopted')) = (accepted_at IS NOT NULL)",
        schema="patas",
    )


def downgrade() -> None:
    op.drop_constraint(
        "adoption_applications_accepted_at_status_check",
        "adoption_applications",
        schema="patas",
    )
    op.drop_column("adoption_applications", "accepted_at", schema="patas")
