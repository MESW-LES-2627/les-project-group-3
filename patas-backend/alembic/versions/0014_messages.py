"""create the messages of a request's conversation

Revision ID: 0014
Revises: 0013
"""

import sqlalchemy as sa

from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("sender_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        # Like the adoption tables: requests and users are never deleted.
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["patas.adoption_applications.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["sender_id"], ["patas.users.id"], ondelete="RESTRICT"),
        # Like the domain: trimmed text of 1 to 2000 characters.
        sa.CheckConstraint(
            "char_length(body) BETWEEN 1 AND 2000 AND body = btrim(body)",
            name="messages_body_check",
        ),
        schema="patas",
    )
    # A conversation is always read in order, and "after" starts from one message.
    op.create_index(
        "messages_application_sent_at_idx",
        "messages",
        ["application_id", "sent_at", "id"],
        schema="patas",
    )


def downgrade() -> None:
    op.drop_index("messages_application_sent_at_idx", "messages", schema="patas")
    op.drop_table("messages", schema="patas")
