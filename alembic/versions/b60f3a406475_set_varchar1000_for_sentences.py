"""set Varchar1000 for sentences

Revision ID: b60f3a406475
Revises: 61d3652d10d2
Create Date: 2023-06-15 14:52:02.528901

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b60f3a406475'
down_revision = '61d3652d10d2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('sentence', sa.Column('translation', sa.String(length=1000), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('sentence', 'translation')
    # ### end Alembic commands ###
