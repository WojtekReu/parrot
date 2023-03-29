"""create models table

Revision ID: e86cf65823c4
Revises: 
Create Date: 2023-03-23 11:31:59.004504

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e86cf65823c4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "book",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(50), nullable=False),
        sa.Column("author", sa.String(50), nullable=False),
    )
    op.create_table(
        "sentence",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("book_id", sa.Integer, sa.ForeignKey("book.id"), nullable=False),
        sa.Column("order", sa.Integer, nullable=False),
        sa.Column("text", sa.String(100), nullable=False),
        sa.Column("translations", sa.JSON, nullable=False),
    )
    op.create_table(
        "book_word",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("book_id", sa.Integer, sa.ForeignKey("book.id"), nullable=False),
        sa.Column("word_id", sa.Integer, sa.ForeignKey("word.id"), nullable=False),
        sa.Column("order", sa.Integer, nullable=False),
    )
    op.create_table(
        "word",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("key_word", sa.String(100), nullable=False),
        sa.Column("translations", sa.JSON, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("word")
    op.drop_table("sentence")
    op.drop_table("book")
