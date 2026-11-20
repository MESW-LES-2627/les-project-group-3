"""remember Matchmaker passes and saves

Revision ID: 0011
Revises: 0010
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

swipe_disposition = postgresql.ENUM(
    "passed", "saved", name="swipe_disposition", schema="patas", create_type=False
)


def upgrade() -> None:
    op.execute("CREATE TYPE patas.swipe_disposition AS ENUM ('passed', 'saved')")
    op.create_table(
        "matchmaker_swipes",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("animal_id", sa.UUID(), nullable=False),
        sa.Column("disposition", swipe_disposition, nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("user_id", "animal_id", name="matchmaker_swipes_pkey"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["patas.users.id"],
            name="matchmaker_swipes_user_id_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["animal_id"],
            ["patas.animals.id"],
            name="matchmaker_swipes_animal_id_fkey",
            ondelete="CASCADE",
        ),
        schema="patas",
    )
    op.execute(
        "CREATE INDEX idx_matchmaker_swipes_user_disposition "
        "ON patas.matchmaker_swipes (user_id, disposition)"
    )
    op.execute(
        """
        CREATE TRIGGER trigger_matchmaker_swipes_set_updated_at
        BEFORE UPDATE ON patas.matchmaker_swipes
        FOR EACH ROW EXECUTE FUNCTION patas.set_updated_at()
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER trigger_matchmaker_swipes_set_updated_at "
        "ON patas.matchmaker_swipes"
    )
    op.drop_table("matchmaker_swipes", schema="patas")
    op.execute("DROP TYPE patas.swipe_disposition")
