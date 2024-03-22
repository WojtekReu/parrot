"""change unique constrain for word

Revision ID: 57369e7f4f6b
Revises: 31bf59630c51
Create Date: 2024-03-22 22:15:20.181023

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '57369e7f4f6b'
down_revision = '31bf59630c51'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('word_lem_key', 'word', type_='unique')
    op.create_unique_constraint('pos_lem_unique', 'word', ['pos', 'lem'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('pos_lem_unique', 'word', type_='unique')
    op.create_unique_constraint('word_lem_key', 'word', ['lem'])
    # ### end Alembic commands ###
