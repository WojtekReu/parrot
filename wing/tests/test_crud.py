import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from wing.crud.sentence import (
    create_sentence,
    get_sentence,
    delete_sentence,
    delete_sentences_by_book,
)
from wing.crud.word import create_word, delete_word, get_word, update_word
from wing.models.book import BookCreate, BookUpdate
from wing.models.sentence import SentenceCreate
from wing.crud.book import delete_book, create_book, get_book, update_book
from wing.models.word import WordCreate, WordUpdate


@pytest.mark.asyncio
async def test_create_book(session: AsyncSession, book_create: BookCreate):
    created_book = await create_book(session, book_create)
    assert created_book.id is not None
    assert created_book.title == book_create.title


@pytest.mark.asyncio
async def test_get_book(session: AsyncSession, book_create: BookCreate):
    created_book = await create_book(session, book_create)
    received_book = await get_book(session, created_book.id)
    assert received_book == created_book


@pytest.mark.asyncio
async def test_update_book(session: AsyncSession, book_create: BookCreate):
    created_book = await create_book(session, book_create)
    updated_book = await update_book(
        session,
        created_book.id,
        BookUpdate(
            author="new author",
            title="new update title",
        ),
    )
    assert updated_book.title == "new update title"
    assert updated_book.author == "new author"


@pytest.mark.asyncio
async def test_delete_book(session: AsyncSession, book_create: BookCreate):
    created_book = await create_book(session, book_create)
    deleted_count = await delete_book(session, book_id=created_book.id)
    assert deleted_count == 1


@pytest.mark.asyncio
async def test_create_sentence(session: AsyncSession, book_create: BookCreate):
    created_book = await create_book(session, book_create)
    created_sentence = await create_sentence(
        session,
        SentenceCreate(
            nr=1,
            book_id=created_book.id,
            sentence="This is the test example sentence.",
        ),
    )
    assert created_sentence.id is not None
    assert created_sentence.sentence == "This is the test example sentence."


@pytest.mark.asyncio
async def test_get_sentence(session: AsyncSession, book_create: BookCreate):
    created_book = await create_book(session, book_create)
    created_sentence = await create_sentence(
        session,
        SentenceCreate(
            nr=1,
            book_id=created_book.id,
            sentence="This is the test example sentence.",
        ),
    )
    received_sentence = await get_sentence(session, created_sentence.id)
    assert received_sentence == created_sentence


@pytest.mark.asyncio
async def test_delete_sentence(session: AsyncSession, book_create: BookCreate):
    created_book = await create_book(session, book_create)
    created_sentence = await create_sentence(
        session,
        SentenceCreate(
            nr=1,
            book_id=created_book.id,
            sentence="This is the test example sentence.",
        ),
    )
    deleted_count = await delete_sentence(session, created_sentence.id)
    assert deleted_count == 1


@pytest.mark.asyncio
async def test_delete_sentences_by_book(session: AsyncSession, book_create: BookCreate):
    created_book = await create_book(session, book_create)
    sentences = [
        (1, "This is first test sentence for book."),
        (2, "This is second test sentence for book."),
        (3, "This is third test sentence for book."),
    ]
    for nr, text in sentences:
        await create_sentence(
            session,
            SentenceCreate(
                nr=nr,
                book_id=created_book.id,
                sentence=text,
            ),
        )
    deleted_count = await delete_sentences_by_book(session, created_book.id)
    assert deleted_count == 3


@pytest.mark.asyncio
async def test_create_word(session: AsyncSession, word_create: WordCreate):
    created_word = await create_word(session, word_create)
    assert created_word.id is not None
    assert created_word.lem == word_create.lem


@pytest.mark.asyncio
async def test_get_word(session: AsyncSession, word_create: WordCreate):
    created_word = await create_word(session, word_create)
    received_word = await get_word(session, created_word.id)
    assert received_word == created_word


@pytest.mark.asyncio
async def test_update_word(session: AsyncSession, word_create: WordCreate):
    created_word = await create_word(session, word_create)
    updated_word = await update_word(
        session,
        created_word.id,
        WordUpdate(
            count=3,
            declination={"VBN": "tested"},
        ),
    )
    assert updated_word.count == 3
    assert updated_word.declination == {"VBN": "tested"}


@pytest.mark.asyncio
async def test_delete_word(session: AsyncSession, word_create: WordCreate):
    created_word = await create_word(session, word_create)
    deleted_word = await delete_word(session, word_id=created_word.id)
    assert deleted_word == 1
