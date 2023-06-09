"""add translation table

Revision ID: c1c1049d4ea4
Revises: b465b89c24a0
Create Date: 2023-06-13 16:24:07.982615

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1c1049d4ea4'
down_revision = 'b465b89c24a0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('translation',
    sa.Column('bword_id', sa.Integer(), nullable=False),
    sa.Column('source', sa.String(length=100), nullable=False),
    sa.Column('text', sa.String(length=100), nullable=False),
    sa.Column('sentences', sa.JSON(), nullable=False),
    sa.Column('book_contents', sa.JSON(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['bword_id'], ['bword.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_column('book', 'path')
    op.add_column('bword', sa.Column('lem', sa.String(length=255), nullable=True))
    op.drop_column('bword', 'stem')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bword', sa.Column('stem', sa.VARCHAR(length=255), autoincrement=False, nullable=False))
    op.drop_column('bword', 'lem')
    op.add_column('book', sa.Column('path', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
    op.drop_table('translation')
    # ### end Alembic commands ###
