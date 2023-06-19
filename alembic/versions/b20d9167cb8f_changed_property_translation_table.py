"""changed property Translation table

Revision ID: b20d9167cb8f
Revises: c1c1049d4ea4
Create Date: 2023-06-13 16:31:18.660827

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b20d9167cb8f'
down_revision = 'c1c1049d4ea4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('translation', 'sentences',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=True)
    op.alter_column('translation', 'book_contents',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('translation', 'book_contents',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=False)
    op.alter_column('translation', 'sentences',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=False)
    # ### end Alembic commands ###