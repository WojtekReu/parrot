"""add translation table

Revision ID: b311b8f031fc
Revises: 1e9b41590381
Create Date: 2024-07-17 18:03:33.949701

"""
import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b311b8f031fc"
down_revision = "1e9b41590381"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "translation",
        sa.Column("word", sqlmodel.sql.sqltypes.AutoString(length=60), nullable=False),
        sa.Column("definition", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_translation_id"), table_name="translation")
    op.drop_table("translation")
