"""add the animal's district

Revision ID: 0006
Revises: 0005
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

DISTRICTS = (
    "aveiro", "beja", "braga", "braganca", "castelo_branco", "coimbra", "evora",
    "faro", "guarda", "leiria", "lisboa", "portalegre", "porto", "santarem",
    "setubal", "viana_do_castelo", "vila_real", "viseu", "acores", "madeira",
)  # fmt: skip
district = postgresql.ENUM(
    *DISTRICTS, name="district", schema="patas", create_type=False
)


def upgrade() -> None:
    values = ", ".join(f"'{name}'" for name in DISTRICTS)
    op.execute(f"CREATE TYPE patas.district AS ENUM ({values})")
    op.add_column(
        "animals", sa.Column("district", district, nullable=True), schema="patas"
    )


def downgrade() -> None:
    op.drop_column("animals", "district", schema="patas")
    op.execute("DROP TYPE patas.district")
