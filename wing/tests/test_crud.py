from typing import Coroutine

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from wing.crud.flashcard import (
    create_flashcard,
    get_flashcards_by_keyword,
    flashcard_join_to_sentences,
    update_flashcard,
)
from wing.crud.sentence import (
    create_sentence,
    get_sentence,
    delete_sentence,
    delete_sentences_by_book,
    get_sentences_with_phrase,
)
from wing.crud.user import create_user, get_user, get_user_by_email
from wing.crud.word import (
    create_word,
    delete_word,
    get_word,
    update_word,
    get_sentence_ids_with_word,
    word_join_to_sentences,
    find_words,
)
from wing.models.book import Book, BookCreate, BookUpdate, BookFind
from wing.models.flashcard import FlashcardCreate, FlashcardUpdate
from wing.models.sentence import SentenceCreate
from wing.crud.book import delete_book, create_book, get_book, find_books, update_book
from wing.models.user import UserCreate, UserUpdate
from wing.models.word import Word, WordCreate, WordUpdate, WordFind


@pytest.mark.asyncio
async def test_create_user(session: AsyncSession):
    created_user = await create_user(
        session,
        UserCreate(
            username="zkowalski",
            password="secret-password",
            email="zkowalski@example.com",
        ),
    )
    assert created_user.id is not None
    assert created_user.username == "zkowalski"


@pytest.mark.asyncio
async def test_get_user_by_email(session: AsyncSession, user_coroutine: Coroutine):
    user = await user_coroutine
    retrieved_user = await get_user_by_email(session, user.email)
    assert retrieved_user.id is not None
    assert retrieved_user.username == user.username
    assert retrieved_user.email == user.email


@pytest.mark.asyncio
async def test_get_user_by_email_user_not_found(session: AsyncSession):
    result = await get_user_by_email(session, "zkapusta@example.com")
    assert result is None


@pytest.mark.asyncio
async def test_create_book(session: AsyncSession):
    created_book = await create_book(
        session,
        BookCreate(
            title="Nineteen Eighty-Four",
            author="Eric Arthur Blair",
        ),
    )
    assert created_book.id is not None
    assert created_book.title == created_book.title


@pytest.mark.asyncio
async def test_get_book(session: AsyncSession, book_coroutine: Coroutine):
    book = await book_coroutine
    received_book = await get_book(session, book.id)
    assert received_book == book


@pytest.mark.asyncio
async def test_find_books(session: AsyncSession):
    await create_book(
        session,
        BookCreate(
            title="To The Lighthouse",
            author="Virginia Woolf",
        ),
    )
    books = [book for book in await find_books(session, BookFind())]
    assert len(books) > 1
    assert isinstance(books[0], Book)
    assert "To The Lighthouse" in [book.title for book in books]


@pytest.mark.asyncio
async def test_find_books_by_title(session: AsyncSession):
    book_created = await create_book(
        session,
        BookCreate(
            title="The Sign of the Four",
            author="Arthur Conan Doyle",
        ),
    )
    books = [book for book in await find_books(session, BookFind(title=book_created.title))]
    assert isinstance(books[0], Book)
    assert books[0].title == book_created.title
    assert len(books) == 1


@pytest.mark.asyncio
async def test_update_book(session: AsyncSession, book_for_modification):
    book = await book_for_modification
    await update_book(
        session,
        book.id,
        BookUpdate(
            author="Frank Herbert",
            title="Dune",
        ),
    )
    updated_book = await get_book(session, book.id)
    assert updated_book.title == "Dune"
    assert updated_book.author == "Frank Herbert"


@pytest.mark.asyncio
async def test_delete_book(session: AsyncSession):
    created_book = await create_book(
        session,
        BookCreate(
            title="Animal Farm",
            author="Eric Arthur Blair",
        ),
    )
    deleted_count = await delete_book(session, book_id=created_book.id)
    assert deleted_count == 1
    result = await get_book(session, created_book.id)
    assert result is None


@pytest.mark.asyncio
async def test_create_sentence(session: AsyncSession, book_coroutine: Coroutine):
    book = await book_coroutine
    created_sentence = await create_sentence(
        session,
        SentenceCreate(
            nr=1,
            book_id=book.id,
            sentence="This is the test example sentence.",
        ),
    )
    assert created_sentence.id is not None
    assert created_sentence.sentence == "This is the test example sentence."


@pytest.mark.asyncio
async def test_get_sentence(session: AsyncSession, book_coroutine: Coroutine):
    book = await book_coroutine
    created_sentence = await create_sentence(
        session,
        SentenceCreate(
            nr=1,
            book_id=book.id,
            sentence="This is the test example sentence.",
        ),
    )
    received_sentence = await get_sentence(session, created_sentence.id)
    assert received_sentence == created_sentence


@pytest.mark.asyncio
async def test_get_sentences_with_phrase(session: AsyncSession, book_coroutine: Coroutine):
    book = await book_coroutine
    sentences = [
        "Watshon went to home.",
        "Someone went to home right now.",
    ]
    for nr, sentence in enumerate(sentences):
        await create_sentence(
            session,
            SentenceCreate(
                nr=nr,
                book_id=book.id,
                sentence=sentence,
            ),
        )

    result = []
    for sentence in await get_sentences_with_phrase(session, "went to home"):
        result.append(sentence.sentence)

    assert result == sentences


@pytest.mark.asyncio
async def test_flashcard_join_to_sentence(
    session: AsyncSession, book_coroutine: Coroutine, user_coroutine: Coroutine
):
    book = await book_coroutine
    user = await user_coroutine
    sentences = [
        "The two horses had just lain down when a brood of ducklings",
        "She had protected the lost brood of ducklings.",
    ]
    sentence_ids = set()
    for nr, sentence_text in enumerate(sentences):
        sentence = await create_sentence(
            session,
            SentenceCreate(
                nr=nr,
                book_id=book.id,
                sentence=sentence_text,
            ),
        )
        sentence_ids.add(sentence.id)

    flashcard = await create_flashcard(
        session,
        FlashcardCreate(
            user_id=user.id,
            keyword="brood of ducklings",
            translations=["potomstwo kaczątek"],
        ),
    )
    await flashcard_join_to_sentences(session, flashcard.id, sentence_ids)


@pytest.mark.asyncio
async def test_get_sentences_with_word(session: AsyncSession, book_coroutine: Coroutine):
    book = await book_coroutine
    sentences = [
        "Such is the natural life of a pig.",
        "The four young pigs raised their voices timidly.",
        "The pigs did not actually work.",
    ]
    sentence_ids = set()
    for nr, sentence_text in enumerate(sentences):
        sentence = await create_sentence(
            session,
            SentenceCreate(
                nr=nr,
                book_id=book.id,
                sentence=sentence_text,
            ),
        )
        sentence_ids.add(sentence.id)

    word = await create_word(
        session,
        WordCreate(
            count=3,
            pos="n",
            lem="pig",
            declinations=["pigs"],
            definition="very smart animal",
        ),
    )
    await word_join_to_sentences(session, word.id, sentence_ids)

    result_sentence_ids = await get_sentence_ids_with_word(session, "pig")
    result_sentences = [await get_sentence(session, s_id) for s_id in result_sentence_ids]
    results = sorted(sentence.sentence for sentence in result_sentences)
    assert results == sentences


@pytest.mark.asyncio
async def test_delete_sentence(session: AsyncSession, book_coroutine: Coroutine):
    book = await book_coroutine
    created_sentence = await create_sentence(
        session,
        SentenceCreate(
            nr=1,
            book_id=book.id,
            sentence="This is the test example sentence.",
        ),
    )
    deleted_count = await delete_sentence(session, created_sentence.id)
    assert deleted_count == 1
    result = await get_sentence(session, created_sentence.id)
    assert result is None


@pytest.mark.asyncio
async def test_delete_sentences_by_book(session: AsyncSession):
    book = await create_book(
        session,
        BookCreate(
            title="Ernest Hemingway",
            author="The Old Man and the See",
        ),
    )
    sentences = [
        (1, "It is as though I were inferior."),
        (2, "I know."),
        (3, "Sleep well, old man."),
    ]
    sentence_ids = []
    for nr, text in sentences:
        sentence = await create_sentence(
            session,
            SentenceCreate(
                nr=nr,
                book_id=book.id,
                sentence=text,
            ),
        )
        sentence_ids.append(sentence.id)
    deleted_count = await delete_sentences_by_book(session, book.id)
    assert deleted_count == 3
    for s_id in sentence_ids:
        result = await get_sentence(session, s_id)
        assert result is None


@pytest.mark.asyncio
async def test_create_word(session: AsyncSession):
    word = await create_word(
        session,
        WordCreate(
            lem="shrimp",
            pos="n",
        ),
    )
    assert word.id is not None
    assert word.lem == "shrimp"
    assert word.count == 0


@pytest.mark.asyncio
async def test_get_word(session: AsyncSession, word_coroutine: Coroutine):
    word = await word_coroutine
    received_word = await get_word(session, word.id)
    assert received_word == word


@pytest.mark.asyncio
async def test_find_words_by_lem_pos(session: AsyncSession):
    await create_word(
        session,
        WordCreate(
            lem="mildew",
            pos="n",
        ),
    )
    await create_word(
        session,
        WordCreate(
            lem="mildew",
            pos="n",
        ),
    )
    await create_word(
        session,
        WordCreate(
            lem="mildew",
            pos="v",
        ),
    )
    result = await find_words(session, WordFind(lem="mildew", pos="n"))
    words = [word for word in result]
    assert len(words) == 2
    assert words[0].lem == "mildew"
    assert words[0].pos == "n"


@pytest.mark.asyncio
async def test_find_words_by_lem(session: AsyncSession):
    await create_word(
        session,
        WordCreate(
            lem="mould",
            pos="n",
        ),
    )
    await create_word(
        session,
        WordCreate(
            lem="mould",
            pos="v",
        ),
    )
    result = await find_words(session, WordFind(lem="mould"))
    words = [word for word in result]
    assert len(words) == 2
    assert words[0].lem == "mould"


@pytest.mark.asyncio
async def test_update_word(session: AsyncSession):
    word = await create_word(session, WordCreate(lem="absorb", pos="v"))
    assert word.count == 0
    updated_word = await update_word(
        session,
        word.id,
        WordUpdate(
            count=3,
            declination={"VBN": "absorbed"},
        ),
    )
    assert updated_word.count == 3
    assert updated_word.declination == {"VBN": "absorbed"}


@pytest.mark.asyncio
async def test_delete_word(session: AsyncSession):
    word = await create_word(session, WordCreate(lem="bait", pos="n"))
    deleted_word = await delete_word(session, word_id=word.id)
    assert deleted_word == 1


@pytest.mark.asyncio
async def test_create_flashcard(session: AsyncSession, user_coroutine: Coroutine):
    user = await user_coroutine
    flashcard = await create_flashcard(
        session,
        FlashcardCreate(
            user_id=user.id,
            keyword="stirring",
            translations=["poruszajacy"],
        ),
    )
    assert flashcard.id is not None
    assert flashcard.keyword == "stirring"
    assert flashcard.translations == ["poruszajacy"]


@pytest.mark.asyncio
async def test_get_flashcard_by_values(session: AsyncSession, user_coroutine: Coroutine):
    user = await user_coroutine
    flashcard = await create_flashcard(
        session,
        FlashcardCreate(
            user_id=user.id,
            keyword="rocket",
            translations=["rakieta"],
        ),
    )
    translations = []
    for retrieved_flashcard in await get_flashcards_by_keyword(session, keyword=flashcard.keyword):
        translations.append(retrieved_flashcard.translations)
    assert translations == [["rakieta"]]


@pytest.mark.asyncio
async def test_update_flashcard(session: AsyncSession, flashcard_coroutine: Coroutine):
    flashcard = await flashcard_coroutine
    flashcard_updated = await update_flashcard(
        session,
        flashcard.id,
        FlashcardUpdate(
            user_id=flashcard.user_id,
            keyword=flashcard.keyword,
            translations=["niejednoznaczny"],
        ),
    )
    assert flashcard_updated.keyword == flashcard.keyword
    assert flashcard_updated.translations == ["niejednoznaczny"]
