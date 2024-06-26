"""create models

Revision ID: 62daa9c54b51
Revises: 
Create Date: 2024-03-30 18:05:39.829104

"""
import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '62daa9c54b51'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('book',
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('author', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('sentences_count', sa.Integer(), nullable=False),
    sa.Column('words_count', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_book_id'), 'book', ['id'], unique=False)
    op.create_table('user',
    sa.Column('username', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('password', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('first_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('last_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_id'), 'user', ['id'], unique=False)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    op.create_table('word',
    sa.Column('count', sa.Integer(), nullable=False),
    sa.Column('pos', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('lem', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('declination', sa.JSON(), nullable=True),
    sa.Column('definition', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_word_id'), 'word', ['id'], unique=False)
    op.create_table('flashcard',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('keyword', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('translations', sa.JSON(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_flashcard_id'), 'flashcard', ['id'], unique=False)
    op.create_table('sentence',
    sa.Column('nr', sa.Integer(), nullable=False),
    sa.Column('book_id', sa.Integer(), nullable=False),
    sa.Column('sentence', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['book_id'], ['book.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sentence_id'), 'sentence', ['id'], unique=False)
    op.create_table('flashcard_word',
    sa.Column('id', sa.Integer(), nullable=True),
    sa.Column('flashcard_id', sa.Integer(), nullable=False),
    sa.Column('word_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['flashcard_id'], ['flashcard.id'], ),
    sa.ForeignKeyConstraint(['word_id'], ['word.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_flashcard_word_id'), 'flashcard_word', ['id'], unique=False)
    op.create_table('sentence_flashcard',
    sa.Column('id', sa.Integer(), nullable=True),
    sa.Column('sentence_id', sa.Integer(), nullable=False),
    sa.Column('flashcard_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['flashcard_id'], ['flashcard.id'], ),
    sa.ForeignKeyConstraint(['sentence_id'], ['sentence.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sentence_flashcard_id'), 'sentence_flashcard', ['id'], unique=False)
    op.create_table('sentence_word',
    sa.Column('id', sa.Integer(), nullable=True),
    sa.Column('sentence_id', sa.Integer(), nullable=False),
    sa.Column('word_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['sentence_id'], ['sentence.id'], ),
    sa.ForeignKeyConstraint(['word_id'], ['word.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sentence_word_id'), 'sentence_word', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_sentence_word_id'), table_name='sentence_word')
    op.drop_table('sentence_word')
    op.drop_index(op.f('ix_sentence_flashcard_id'), table_name='sentence_flashcard')
    op.drop_table('sentence_flashcard')
    op.drop_index(op.f('ix_flashcard_word_id'), table_name='flashcard_word')
    op.drop_table('flashcard_word')
    op.drop_index(op.f('ix_sentence_id'), table_name='sentence')
    op.drop_table('sentence')
    op.drop_index(op.f('ix_flashcard_id'), table_name='flashcard')
    op.drop_table('flashcard')
    op.drop_index(op.f('ix_word_id'), table_name='word')
    op.drop_table('word')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_id'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    op.drop_index(op.f('ix_book_id'), table_name='book')
    op.drop_table('book')
    # ### end Alembic commands ###
