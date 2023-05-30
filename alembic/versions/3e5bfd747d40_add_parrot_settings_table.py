"""add parrot_settings table

Revision ID: 3e5bfd747d40
Revises: b66efb0df8a8
Create Date: 2023-05-30 09:55:17.286695

"""
from alembic import op
import sqlalchemy as sa
from wing.models import ParrotSettings, Word
from sqlalchemy import orm

# revision identifiers, used by Alembic.
revision = '3e5bfd747d40'
down_revision = 'b66efb0df8a8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('parrot_settings',
    sa.Column('last_word_id', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###

    bind = op.get_bind()
    session = orm.Session(bind=bind)

    last_word_id = Word.get_max_id()
    # Insert max Word.id to ParrotSettings.last_word_id
    parrot_settings = ParrotSettings(last_word_id=last_word_id)
    parrot_settings.save()
    session.commit()


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('parrot_settings')
    # ### end Alembic commands ###
