"""delete cascade

Revision ID: 751a647610c7
Revises: 66378bd880b1
Create Date: 2024-07-03 17:57:27.444348

"""
import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '751a647610c7'
down_revision = '66378bd880b1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint('sentence_word_word_id_fkey', 'sentence_word', type_='foreignkey')
    op.drop_constraint('sentence_word_sentence_id_fkey', 'sentence_word', type_='foreignkey')
    op.create_foreign_key(None, 'sentence_word', 'word', ['word_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'sentence_word', 'sentence', ['sentence_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('sentence_flashcard_flashcard_id_fkey', 'sentence_flashcard', type_='foreignkey')
    op.drop_constraint('sentence_flashcard_sentence_id_fkey', 'sentence_flashcard', type_='foreignkey')
    op.create_foreign_key(None, 'sentence_flashcard', 'flashcard', ['flashcard_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'sentence_flashcard', 'sentence', ['sentence_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('flashcard_word_word_id_fkey', 'flashcard_word', type_='foreignkey')
    op.drop_constraint('flashcard_word_flashcard_id_fkey', 'flashcard_word', type_='foreignkey')
    op.create_foreign_key(None, 'flashcard_word', 'flashcard', ['flashcard_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'flashcard_word', 'word', ['word_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    op.drop_constraint('flashcard_word_word_id_fkey', 'flashcard_word', type_='foreignkey')
    op.drop_constraint('flashcard_word_flashcard_id_fkey', 'flashcard_word', type_='foreignkey')
    op.create_foreign_key(None, 'flashcard_word', 'word', ['word_id'], ['id'])
    op.create_foreign_key(None, 'flashcard_word', 'flashcard', ['flashcard_id'], ['id'])
    op.drop_constraint('sentence_flashcard_sentence_id_fkey', 'sentence_flashcard', type_='foreignkey')
    op.drop_constraint('sentence_flashcard_flashcard_id_fkey', 'sentence_flashcard', type_='foreignkey')
    op.create_foreign_key(None, 'sentence_flashcard', 'flashcard', ['flashcard_id'], ['id'])
    op.create_foreign_key(None, 'sentence_flashcard', 'sentence', ['sentence_id'], ['id'])
    op.drop_constraint('sentence_word_sentence_id_fkey', 'sentence_word', type_='foreignkey')
    op.drop_constraint('sentence_word_word_id_fkey', 'sentence_word', type_='foreignkey')
    op.create_foreign_key(None, 'sentence_word', 'word', ['word_id'], ['id'])
    op.create_foreign_key(None, 'sentence_word', 'sentence', ['sentence_id'], ['id'])
