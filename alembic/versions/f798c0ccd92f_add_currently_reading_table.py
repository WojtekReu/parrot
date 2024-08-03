"""add currently_reading table

Revision ID: f798c0ccd92f
Revises: b311b8f031fc
Create Date: 2024-08-02 21:46:40.068231

"""
import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f798c0ccd92f'
down_revision = 'b311b8f031fc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('currently_reading',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('book_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['book_id'], ['book.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_currently_reading_id'), 'currently_reading', ['id'], unique=False)
    op.create_unique_constraint(None, 'currently_reading', ['user_id', 'book_id'])


def downgrade() -> None:
    op.drop_constraint(None, "currently_reading", type_="unique")
    op.drop_index(op.f('ix_currently_reading_id'), table_name='currently_reading')
    op.drop_table('currently_reading')
