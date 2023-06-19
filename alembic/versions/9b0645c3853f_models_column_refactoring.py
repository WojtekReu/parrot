"""models column refactoring

Revision ID: 9b0645c3853f
Revises: a95e7710b3d8
Create Date: 2023-06-19 11:16:31.307265

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9b0645c3853f'
down_revision = 'a95e7710b3d8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('word_sentence')
    op.drop_table('book_word')
    op.drop_table('context')
    op.drop_table('word')
    op.alter_column('book', 'sentences_count',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('bword', 'count',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('bword', 'lem',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)
    op.create_unique_constraint(None, 'bword', ['lem'])
    op.add_column('parrot_settings', sa.Column('last_sentence_id', sa.Integer(), nullable=False))
    op.alter_column('translation', 'sentences',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=False)
    op.alter_column('translation', 'book_contents',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('translation', 'book_contents',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=True)
    op.alter_column('translation', 'sentences',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=True)
    op.drop_column('parrot_settings', 'last_sentence_id')
    op.drop_constraint(None, 'bword', type_='unique')
    op.alter_column('bword', 'lem',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)
    op.alter_column('bword', 'count',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('book', 'sentences_count',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.create_table('book_word',
    sa.Column('book_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('word_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('order', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['book_id'], ['book.id'], name='book_word_book_id_fkey'),
    sa.ForeignKeyConstraint(['word_id'], ['word.id'], name='book_word_word_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='book_word_pkey')
    )
    op.create_table('context',
    sa.Column('content', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('book_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('word_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['book_id'], ['book.id'], name='context_book_id_fkey'),
    sa.ForeignKeyConstraint(['word_id'], ['word.id'], name='context_word_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='context_pkey')
    )
    op.create_table('word',
    sa.Column('key_word', sa.VARCHAR(length=40), autoincrement=False, nullable=False),
    sa.Column('translations', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('word_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id', name='word_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_table('word_sentence',
    sa.Column('word_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('sentence_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['sentence_id'], ['sentence.id'], name='word_sentence_sentence_id_fkey'),
    sa.ForeignKeyConstraint(['word_id'], ['word.id'], name='word_sentence_word_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='word_sentence_pkey')
    )
    # ### end Alembic commands ###
