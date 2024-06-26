"""change word model

Revision ID: 66378bd880b1
Revises: 62daa9c54b51
Create Date: 2024-06-07 17:41:09.321440

"""
import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '66378bd880b1'
down_revision = '62daa9c54b51'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('word', sa.Column('synset', sqlmodel.sql.sqltypes.AutoString(length=35), nullable=True))
    op.alter_column('word', 'lem', type_=sqlmodel.sql.sqltypes.AutoString(length=30))
    op.alter_column('word', 'pos', type_=sqlmodel.sql.sqltypes.AutoString(length=1))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('word', 'synset')
    # ### end Alembic commands ###
