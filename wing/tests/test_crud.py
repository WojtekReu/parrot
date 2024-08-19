from unittest.mock import patch

from fastapi_pagination.default import Params
from fastapi_pagination.ext.sqlmodel import paginate

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from wing.crud.book import delete_book, create_book, get_book, find_books, update_book
from wing.crud.flashcard import (
    create_flashcard,
    get_flashcards_by_keyword,
    flashcard_join_to_sentences,
    update_flashcard,
    get_flashcard,
    flashcard_join_to_words,
    get_flashcard_words,
    flashcard_separate_words,
)
from wing.crud.sentence import (
    create_sentence,
    get_sentence,
    delete_sentence,
    delete_sentences_by_book,
    get_sentences_with_phrase,
    get_sentences_for_flashcard,
)
from wing.crud.translation import create_translation, get_translation_by_word
from wing.crud.user import (
    create_user,
    get_user,
    get_user_by_email,
    get_user_by_username,
    get_user_flashcards,
    update_user,
)
from wing.crud.word import (
    create_word,
    delete_word,
    get_word,
    update_word,
    get_sentence_ids_with_word,
    word_join_to_sentences,
    find_synset,
    find_words,
    word_separate_sentences,
    get_word_sentences,
    get_words,
)
from wing.models.book import Book, BookCreate, BookUpdate, BookFind
from wing.models.flashcard import FlashcardCreate, FlashcardUpdate, Flashcard
from wing.models.sentence import SentenceCreate, Sentence
from wing.models.translation import Translation
from wing.models.user import UserCreate, UserUpdate
from wing.models.word import Word, WordCreate, WordUpdate, WordFind


async def paginate_mock(*args, **kwargs):
    """
    Add params with `limit` and `offset` to paginate method.
    """
    args = *args, Params(limit=10, offset=3)
    return await paginate(*args)


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
async def test_update_user(session: AsyncSession):
    created_user = await create_user(
        session,
        UserCreate(
            username="ukowalska",
            password="secret-password",
            email="ukowalska@example.com",
        ),
    )
    updated_user = await update_user(
        session=session,
        user_id=created_user.id,
        user=UserUpdate(
            username="ukowalska",
            first_name="Urszula",
            last_name="Kowalska",
        ),
    )
    assert updated_user.username == "ukowalska"
    assert updated_user.first_name == "Urszula"
    assert updated_user.last_name == "Kowalska"


@pytest.mark.asyncio
async def test_get_user_by_email(session: AsyncSession):
    retrieved_user = await get_user_by_email(session, "jkowalski@example.com")
    assert retrieved_user.id is not None
    assert retrieved_user.username == "jkowalski"
    assert retrieved_user.email == "jkowalski@example.com"


@pytest.mark.asyncio
async def test_get_user_by_email_user_not_found(session: AsyncSession):
    result = await get_user_by_email(session, "zkapusta@example.com")
    assert result is None


@patch("wing.crud.user.paginate", paginate_mock)
@pytest.mark.asyncio
async def test_get_user_flashcards(session: AsyncSession):
    user = await get_user_by_username(session, "anowak")
    results = await get_user_flashcards(session, user)
    flashcard_list = [(f.keyword, f.translations) for f in results.items]
    assert flashcard_list == [("well", ["studnia"]), ("dwarf", ["krasnal"])]


@patch("wing.crud.book.paginate", paginate_mock)
@pytest.mark.asyncio
async def test_get_user_books(session: AsyncSession):
    user = await get_user_by_username(session, "anowak")
    results = await find_books(session, BookFind(user_id=user.id))
    book_list = [(f.author, f.title) for f in results.items]
    assert book_list == [
        ("Virginia Woolf", "To The Lighthouse"),
        ("Arthur Conan Doyle", "The Sign of the Four"),
    ]


@pytest.mark.asyncio
async def test_create_book(session: AsyncSession):
    user = await get_user_by_username(session, "jkowalski")
    created_book = await create_book(
        session,
        BookCreate(
            title="Nineteen Eighty-Four",
            author="Eric Arthur Blair",
        ),
        user.id,
    )
    assert created_book.id is not None
    assert created_book.title == created_book.title


@pytest.mark.asyncio
async def test_get_book(session: AsyncSession):
    book = await get_book(session, 1)
    assert book.title == "The Voyage Out"
    assert book.author == "Virginia Woolf"


@patch("wing.crud.book.paginate", paginate_mock)
@pytest.mark.asyncio
async def test_find_books(session: AsyncSession):
    books = [book for book in await find_books(session, BookFind(is_public=True))]
    assert books == [
        (
            "items",
            [
                Book(
                    title="The Voyage Out",
                    user_id=1,
                    words_count=0,
                    is_public=True,
                    author="Virginia Woolf",
                    sentences_count=0,
                    id=1,
                ),
                Book(
                    title="The Sign of the Four",
                    user_id=2,
                    words_count=0,
                    is_public=True,
                    author="Arthur Conan Doyle",
                    sentences_count=0,
                    id=3,
                ),
            ],
        ),
        ("total", 2),
        ("page", 1),
        ("size", 50),
        ("pages", 1),
    ]


@patch("wing.crud.book.paginate", paginate_mock)
@pytest.mark.asyncio
async def test_find_books_by_title(session: AsyncSession):
    books = [book for book in await find_books(session, BookFind(title="The Sign of the Four"))]
    assert books == [
        (
            "items",
            [
                Book(
                    title="The Sign of the Four",
                    user_id=2,
                    words_count=0,
                    is_public=True,
                    author="Arthur Conan Doyle",
                    sentences_count=0,
                    id=3,
                )
            ],
        ),
        ("total", 1),
        ("page", 1),
        ("size", 50),
        ("pages", 1),
    ]


@patch("wing.crud.book.paginate", paginate_mock)
@pytest.mark.asyncio
async def test_update_book(session: AsyncSession):
    user = await get_user_by_username(session, "jkowalski")
    book_items = await find_books(session, BookFind(title="Some Title for Modification"))
    books = [book for book in book_items.items]
    book = books[0]
    await update_book(
        session,
        book.id,
        user.id,
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
    user = await get_user_by_username(session, "jkowalski")
    created_book = await create_book(
        session,
        BookCreate(
            title="Animal Farm",
            author="Eric Arthur Blair",
        ),
        user.id,
    )
    deleted_count = await delete_book(session, book_id=created_book.id, user_id=user.id)
    assert deleted_count == 1
    result = await get_book(session, created_book.id)
    assert result is None


@pytest.mark.asyncio
async def test_create_sentence(session: AsyncSession):
    book = await get_book(session, 1)
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
async def test_get_sentence(session: AsyncSession):
    book = await get_book(session, 1)
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
async def test_get_sentences_for_flashcard(session: AsyncSession):
    user = await get_user(session, 1)
    book = await get_book(session, 1)
    flashcard = await get_flashcard(session, 6)
    sentences = list(await get_sentences_for_flashcard(session, book.id, flashcard.id, user.id))
    expected_sentence = await get_sentence(session, 1)
    assert sentences == [expected_sentence]


@pytest.mark.asyncio
async def test_get_sentences_with_phrase(session: AsyncSession):
    book = await get_book(session, 1)
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
async def test_flashcard_join_to_sentence(session: AsyncSession):
    book = await get_book(session, 1)
    user = await get_user(session, 1)
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
        user.id,
    )
    await flashcard_join_to_sentences(session, flashcard.id, sentence_ids)

    sentences = list(await get_sentences_for_flashcard(session, book.id, flashcard.id, user.id))
    assert sentences == [
        Sentence(
            book_id=1,
            id=8,
            nr=0,
            sentence="The two horses had just lain down when a brood of ducklings",
        ),
        Sentence(book_id=1, id=9, nr=1, sentence="She had protected the lost brood of ducklings."),
    ]


@pytest.mark.asyncio
async def test_flashcard_join_to_words(session: AsyncSession):
    user = await get_user(session, 1)
    flashcard = await create_flashcard(
        session,
        FlashcardCreate(
            user_id=user.id,
            keyword="he possessed disciplines",
            translation=["posiadał dyscyplinę"],
        ),
        user.id,
    )
    word1 = await create_word(session, WordCreate(pos="v", lem="possess"))
    word2 = await create_word(session, WordCreate(pos="n", lem="discipline"))
    word_ids = {word1.id, word2.id}
    await flashcard_join_to_words(session, flashcard.id, word_ids)

    words = list(await get_flashcard_words(session, flashcard.id))

    assert words == [
        Word(lem="possess", definition=None, synset=None, count=0, pos="v", declination={}, id=5),
        Word(
            lem="discipline", definition=None, synset=None, count=0, pos="n", declination={}, id=6
        ),
    ]

    await flashcard_separate_words(session, flashcard.id, {word2.id})

    words = list(await get_flashcard_words(session, flashcard.id))

    assert words == [
        Word(lem="possess", definition=None, synset=None, pos="v", count=0, declination={}, id=5)
    ]


@pytest.mark.asyncio
async def test_get_sentences_with_word(session: AsyncSession):
    book = await get_book(session, 1)
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
async def test_delete_sentence(session: AsyncSession):
    book = await get_book(session, 1)
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
    user = await get_user_by_username(session, "jkowalski")
    book = await create_book(
        session,
        BookCreate(
            title="Ernest Hemingway",
            author="The Old Man and the See",
        ),
        user.id,
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
async def test_get_word(session: AsyncSession):
    word = await get_word(session, 1)
    assert word.lem == "chapter"


@pytest.mark.asyncio
async def test_get_words(session: AsyncSession):
    result = await get_words(session)
    words = list(result)
    assert len(words) > 4
    assert "brooch" in words


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
async def test_create_flashcard(session: AsyncSession):
    user = await get_user(session, 1)
    flashcard = await create_flashcard(
        session,
        FlashcardCreate(
            user_id=user.id,
            keyword="stirring",
            translations=["poruszajacy"],
        ),
        user.id,
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
        user.id,
    )
    translations = []
    for retrieved_flashcard in await get_flashcards_by_keyword(session, keyword=flashcard.keyword):
        translations.append(retrieved_flashcard.translations)
    assert translations == [["rakieta"]]


@pytest.mark.asyncio
async def test_get_flashcard_by_values_for_user(session: AsyncSession):
    user = await get_user_by_username(session, "jkowalski")
    flashcards = await get_flashcards_by_keyword(session, keyword="ambush", user_id=user.id)
    assert list(flashcards) == [
        Flashcard(translations=["zasadzka"], user_id=1, keyword="ambush", id=2)
    ]


@pytest.mark.asyncio
async def test_update_flashcard(session: AsyncSession):
    user = await get_user(session, 1)
    flashcard = await create_flashcard(
        session,
        FlashcardCreate(user_id=user.id, keyword="equivocal", translations=["dwuznaczny"]),
        user.id,
    )
    flashcard_updated = await update_flashcard(
        session,
        flashcard.id,
        user.id,
        FlashcardUpdate(
            user_id=flashcard.user_id,
            keyword=flashcard.keyword,
            translations=["niejednoznaczny"],
        ),
    )
    assert flashcard_updated.keyword == flashcard.keyword
    assert flashcard_updated.translations == ["niejednoznaczny"]


@patch("wing.crud.word.find_definition")
@pytest.mark.asyncio
async def test_find_synset(find_definition_mock, session: AsyncSession):
    word = await get_word(session, 4)  # brooch
    sentence = await get_sentence(session, 3)  # ...little brooch...

    find_definition_mock.return_value = {
        "found": 1,
        "word": "brooch",
        "synsets": [
            [False, "brooch.n.01", "a decorative pin worn by women"],
            [True, "brooch.v.01", "fasten with or as if with a brooch"],
        ],
        "matched_synset": "brooch.v.01",
    }
    result = await find_synset(session, word.id, sentence.id)

    expected = {
        "errorMessage": "",
        "synsets": [
            [False, "brooch.n.01", "a decorative pin worn by women"],
            [True, "brooch.v.01", "fasten with or as if with a brooch"],
        ],
        "word": Word(
            pos="n",
            synset="",
            lem="brooch",
            count=0,
            declination={"NNS": "brooches"},
            definition="",
            id=4,
        ),
    }
    assert result == expected


@pytest.mark.asyncio
async def test_match_word_sentences(session: AsyncSession):
    word = await get_word(session, 1)  # chapter
    book = await get_book(session, 1)
    sentence = await create_sentence(
        session,
        SentenceCreate(book_id=book.id, nr=1, sentence="The first chapter."),
    )
    await word_join_to_sentences(session, word_id=word.id, sentence_ids={sentence.id})

    results = await get_word_sentences(session, word.id)

    assert sentence in results


@pytest.mark.asyncio
async def test_match_word_sentences(session: AsyncSession):
    word = await get_word(session, 1)  # chapter
    results = await get_word_sentences(session, word.id)

    await word_separate_sentences(session, word_id=word.id, sentence_ids={3})
    results1 = await get_word_sentences(session, word.id)

    assert len(list(results)) == len(list(results1)) + 1


@pytest.mark.asyncio
async def test_create_translation(session: AsyncSession):
    translation = Translation(
        word="magic",
        definition="/ˈmæʤɪk/\nI.  <N>  magia, czary, czar\nII.  <Adj>  magiczny, czarodziejski",
    )
    translation_db = await create_translation(session, translation)
    assert translation_db.word == translation.word
    assert translation_db.definition == translation.definition


@pytest.mark.asyncio
async def test_get_translation(session: AsyncSession):
    translation_db = await get_translation_by_word(session, "chapter")
    assert translation_db.word == "chapter"
    assert translation_db.definition == "/ˈʧæptə/ <N>\n  rozdział"
