"""add user_id to book

Revision ID: 1e9b41590381
Revises: 751a647610c7
Create Date: 2024-07-04 09:20:28.698096

"""
import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1e9b41590381'
down_revision = '751a647610c7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('book', sa.Column('user_id', sa.Integer(), nullable=False, server_default="1"))
    op.alter_column('book', 'user_id', server_default=None)
    op.add_column('book', sa.Column('is_public', sa.Boolean(), nullable=False, server_default="True"))
    op.alter_column('book', 'is_public', server_default="False")
    op.create_foreign_key(None, 'book', 'user', ['user_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('book_user_id_fkey', 'book', type_='foreignkey')
    op.drop_column('book', 'is_public')
    op.drop_column('book', 'user_id')
