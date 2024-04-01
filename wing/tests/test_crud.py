import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from wing.crud.flashcard import (
    create_flashcard,
    get_flashcards_by_keyword,
    flashcard_join_to_sentences,
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
)
from wing.models.book import Book, BookCreate, BookUpdate
from wing.models.flashcard import FlashcardCreate
from wing.models.sentence import SentenceCreate
from wing.crud.book import delete_book, create_book, get_book, get_books, update_book
from wing.models.user import UserCreate, UserUpdate
from wing.models.word import WordCreate, WordUpdate


@pytest.mark.asyncio
async def test_create_user(session: AsyncSession, user_create: UserCreate):
    created_user = await create_user(session, user_create)
    assert created_user.id is not None
    assert created_user.username == user_create.username


@pytest.mark.asyncio
async def test_get_user_by_email(session: AsyncSession):
    created_user = await create_user(
        session,
        UserCreate(
            username="anowak",
            password="password",
            email="anowak@example.com",
        ),
    )
    user = await get_user_by_email(session, created_user.email)
    assert user.id is not None
    assert user.username == created_user.username
    assert user.email == created_user.email


@pytest.mark.asyncio
async def test_get_user_by_email_user_not_found(session: AsyncSession):
    result = await get_user_by_email(session, "zkapusta@example.com")
    assert result is None


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
async def test_get_books(session: AsyncSession, book_create: BookCreate):
    await create_book(session, book_create)
    books = [book for book in await get_books(session)]
    assert len(books) == 3
    assert isinstance(books[0], Book)
    assert books[2].title == "test book"


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
async def test_get_sentences_with_phrase(session: AsyncSession, book_create: BookCreate):
    created_book = await create_book(session, book_create)
    sentences = [
        "Watshon went to home.",
        "Someone went to home right now.",
    ]
    for nr, sentence in enumerate(sentences):
        await create_sentence(
            session,
            SentenceCreate(
                nr=nr,
                book_id=created_book.id,
                sentence=sentence,
            ),
        )

    result = []
    for sentence in await get_sentences_with_phrase(session, "went to home"):
        result.append(sentence.sentence)

    assert result == sentences


@pytest.mark.asyncio
async def test_flashcard_join_to_sentece(session: AsyncSession, book_create: BookCreate):
    created_book = await create_book(session, book_create)
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
                book_id=created_book.id,
                sentence=sentence_text,
            ),
        )
        sentence_ids.add(sentence.id)

    flashcard = await create_flashcard(
        session,
        FlashcardCreate(
            user_id=1,
            keyword="brood of ducklings",
            translations=["potomstwo kaczątek"],
        ),
    )
    await flashcard_join_to_sentences(session, flashcard.id, sentence_ids)


@pytest.mark.asyncio
async def test_get_sentences_with_word(session: AsyncSession, book_create: BookCreate):
    created_book = await create_book(session, book_create)
    sentences = [
        "Such is the natural life of a pig.",
        "The four young pigs raised their voices timidly.",
        "The pigs did not actually work.",
    ]
    sentence_ids = []
    for nr, sentence_text in enumerate(sentences):
        sentence = await create_sentence(
            session,
            SentenceCreate(
                nr=nr,
                book_id=created_book.id,
                sentence=sentence_text,
            ),
        )
        sentence_ids.append(sentence.id)

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

    result = await get_sentence_ids_with_word(session, "pig")

    assert result == sentence_ids


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


@pytest.mark.asyncio
async def test_create_flashcard(session: AsyncSession):
    user = await get_user(session, 1)
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
async def test_get_flashcard_by_values(session: AsyncSession):
    user = await get_user(session, 1)
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
