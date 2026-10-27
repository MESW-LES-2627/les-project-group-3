"""add optional animal profile fields

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

animal_sex = postgresql.ENUM(
    "male", "female", "unknown",
    name="animal_sex", schema="patas", create_type=False,
)  # fmt: skip
neutered_status = postgresql.ENUM(
    "yes", "no", "unknown",
    name="neutered_status", schema="patas", create_type=False,
)  # fmt: skip
animal_size = postgresql.ENUM(
    "small", "medium", "large",
    name="animal_size", schema="patas", create_type=False,
)  # fmt: skip
animal_compatibility = postgresql.ENUM(
    "yes", "no", "with_supervision", "unknown",
    name="animal_compatibility", schema="patas", create_type=False,
)  # fmt: skip
first_time_owner_suitability = postgresql.ENUM(
    "yes", "no", "with_support", "unknown",
    name="first_time_owner_suitability", schema="patas", create_type=False,
)  # fmt: skip
energy_level = postgresql.ENUM(
    "low", "moderate", "high",
    name="energy_level", schema="patas", create_type=False,
)  # fmt: skip


def upgrade() -> None:
    op.execute("CREATE TYPE patas.animal_sex AS ENUM ('male', 'female', 'unknown')")
    op.execute("CREATE TYPE patas.neutered_status AS ENUM ('yes', 'no', 'unknown')")
    op.execute("CREATE TYPE patas.animal_size AS ENUM ('small', 'medium', 'large')")
    op.execute(
        "CREATE TYPE patas.animal_compatibility AS ENUM "
        "('yes', 'no', 'with_supervision', 'unknown')"
    )
    op.execute(
        "CREATE TYPE patas.first_time_owner_suitability AS ENUM "
        "('yes', 'no', 'with_support', 'unknown')"
    )
    op.add_column(
        "animals", sa.Column("sex", animal_sex, nullable=True), schema="patas"
    )
    op.add_column(
        "animals",
        sa.Column("is_neutered", neutered_status, nullable=True),
        schema="patas",
    )
    op.add_column(
        "animals", sa.Column("postal_code", sa.Text(), nullable=True), schema="patas"
    )
    op.add_column(
        "animals", sa.Column("size", animal_size, nullable=True), schema="patas"
    )
    op.add_column(
        "animals",
        sa.Column("activity_level", energy_level, nullable=True),
        schema="patas",
    )
    op.add_column(
        "animals",
        sa.Column("space_requirement", animal_size, nullable=True),
        schema="patas",
    )
    op.add_column(
        "animals", sa.Column("shedding", energy_level, nullable=True), schema="patas"
    )
    op.add_column(
        "animals",
        sa.Column("grooming_needs", energy_level, nullable=True),
        schema="patas",
    )
    op.add_column(
        "animals",
        sa.Column("behaves_well_with_children", animal_compatibility, nullable=True),
        schema="patas",
    )
    op.add_column(
        "animals",
        sa.Column("behaves_well_with_dogs", animal_compatibility, nullable=True),
        schema="patas",
    )
    op.add_column(
        "animals",
        sa.Column("behaves_well_with_cats", animal_compatibility, nullable=True),
        schema="patas",
    )
    op.add_column(
        "animals",
        sa.Column(
            "behaves_well_with_other_animals", animal_compatibility, nullable=True
        ),
        schema="patas",
    )
    op.add_column(
        "animals",
        sa.Column("training_needs", energy_level, nullable=True),
        schema="patas",
    )
    op.add_column(
        "animals",
        sa.Column("tolerance_for_time_alone", energy_level, nullable=True),
        schema="patas",
    )
    op.add_column(
        "animals", sa.Column("noise_level", energy_level, nullable=True), schema="patas"
    )
    op.add_column(
        "animals",
        sa.Column(
            "suitable_for_first_time_owners",
            first_time_owner_suitability,
            nullable=True,
        ),
        schema="patas",
    )
    op.add_column(
        "animals",
        sa.Column("special_care_notes", sa.Text(), nullable=True),
        schema="patas",
    )
    op.add_column(
        "animals", sa.Column("other_details", sa.Text(), nullable=True), schema="patas"
    )


def downgrade() -> None:
    op.drop_column("animals", "other_details", schema="patas")
    op.drop_column("animals", "special_care_notes", schema="patas")
    op.drop_column("animals", "suitable_for_first_time_owners", schema="patas")
    op.drop_column("animals", "noise_level", schema="patas")
    op.drop_column("animals", "tolerance_for_time_alone", schema="patas")
    op.drop_column("animals", "training_needs", schema="patas")
    op.drop_column("animals", "behaves_well_with_other_animals", schema="patas")
    op.drop_column("animals", "behaves_well_with_cats", schema="patas")
    op.drop_column("animals", "behaves_well_with_dogs", schema="patas")
    op.drop_column("animals", "behaves_well_with_children", schema="patas")
    op.drop_column("animals", "grooming_needs", schema="patas")
    op.drop_column("animals", "shedding", schema="patas")
    op.drop_column("animals", "space_requirement", schema="patas")
    op.drop_column("animals", "activity_level", schema="patas")
    op.drop_column("animals", "size", schema="patas")
    op.drop_column("animals", "postal_code", schema="patas")
    op.drop_column("animals", "is_neutered", schema="patas")
    op.drop_column("animals", "sex", schema="patas")
    op.execute("DROP TYPE patas.first_time_owner_suitability")
    op.execute("DROP TYPE patas.animal_compatibility")
    op.execute("DROP TYPE patas.animal_size")
    op.execute("DROP TYPE patas.neutered_status")
    op.execute("DROP TYPE patas.animal_sex")
