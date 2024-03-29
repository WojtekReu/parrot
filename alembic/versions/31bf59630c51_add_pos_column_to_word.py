"""add pos column to word

Revision ID: 31bf59630c51
Revises: 7dcdbf6fb41b
Create Date: 2024-03-22 21:43:38.052108

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '31bf59630c51'
down_revision = '7dcdbf6fb41b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('word', sa.Column('pos', sa.String(length=1), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('word', 'pos')
    # ### end Alembic commands ###
