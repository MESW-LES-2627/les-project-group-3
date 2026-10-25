"""create matchmaker profiles

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

# The types are created by hand below, so the table must not try to create them again.
housing_type = postgresql.ENUM(
    "apartment", "house_no_yard", "house_with_yard",
    name="housing_type", schema="patas", create_type=False,
)  # fmt: skip
# energy_level and experience_level are shared scales (models/matching): the animal's
# compatibility profile reuses them, so they are not named after the profile.
energy_level = postgresql.ENUM(
    "low", "moderate", "high",
    name="energy_level", schema="patas", create_type=False,
)  # fmt: skip
time_away = postgresql.ENUM(
    "few_hours", "half_day", "most_of_day",
    name="time_away", schema="patas", create_type=False,
)  # fmt: skip
experience_level = postgresql.ENUM(
    "none", "some", "experienced",
    name="experience_level", schema="patas", create_type=False,
)  # fmt: skip


def upgrade() -> None:
    op.execute(
        "CREATE TYPE patas.housing_type AS ENUM "
        "('apartment', 'house_no_yard', 'house_with_yard')"
    )
    op.execute("CREATE TYPE patas.energy_level AS ENUM ('low', 'moderate', 'high')")
    op.execute(
        "CREATE TYPE patas.time_away AS ENUM ('few_hours', 'half_day', 'most_of_day')"
    )
    op.execute(
        "CREATE TYPE patas.experience_level AS ENUM ('none', 'some', 'experienced')"
    )
    op.create_table(
        "matchmaker_profiles",
        # One profile per user: the user is the key, so a second row cannot exist.
        sa.Column("user_id", sa.UUID(), primary_key=True),
        # Every answer is required: NOT NULL and no default.
        sa.Column("housing", housing_type, nullable=False),
        sa.Column("activity", energy_level, nullable=False),
        sa.Column("time_away", time_away, nullable=False),
        sa.Column("experience", experience_level, nullable=False),
        sa.Column("has_children", sa.Boolean(), nullable=False),
        sa.Column("has_dogs", sa.Boolean(), nullable=False),
        sa.Column("has_cats", sa.Boolean(), nullable=False),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        # Personal data: it goes away with the account.
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["patas.users.id"],
            name="matchmaker_profiles_user_id_fkey",
            ondelete="CASCADE",
        ),
        schema="patas",
    )
    op.execute(
        """
        CREATE TRIGGER trigger_matchmaker_profiles_set_updated_at
        BEFORE UPDATE ON patas.matchmaker_profiles
        FOR EACH ROW EXECUTE FUNCTION patas.set_updated_at()
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER trigger_matchmaker_profiles_set_updated_at "
        "ON patas.matchmaker_profiles"
    )
    op.drop_table("matchmaker_profiles", schema="patas")
    op.execute("DROP TYPE patas.experience_level")
    op.execute("DROP TYPE patas.time_away")
    op.execute("DROP TYPE patas.energy_level")
    op.execute("DROP TYPE patas.housing_type")
