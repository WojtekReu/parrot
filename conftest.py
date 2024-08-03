import asyncio
from unittest.mock import MagicMock

from httpx import AsyncClient
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlmodel import SQLModel

from api.server import app
from wing.config import settings, assemble_db_connection
from wing.crud.book import create_book, set_currently_reading
from wing.crud.flashcard import (
    create_flashcard,
    flashcard_join_to_sentences,
    flashcard_join_to_words,
)
from wing.crud.sentence import create_sentence
from wing.crud.translation import create_translation
from wing.crud.user import create_user
from wing.crud.word import create_word, word_join_to_sentences
from wing.models.book import BookCreate
from wing.models.flashcard import FlashcardCreate
from wing.models.sentence import SentenceCreate
from wing.models.translation import Translation
from wing.models.word import WordCreate
from wing.models.user import UserCreate
from wing.db.session import get_session

settings.POSTGRES_DBNAME = "parrotdb_test"
ENGINE_URL = str(assemble_db_connection(values=settings.dict()))


@pytest_asyncio.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine(event_loop) -> AsyncEngine:
    engine = create_async_engine(ENGINE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    engine.sync_engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def session(engine):
    session_local = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with engine.connect() as conn:
        tsx = await conn.begin()
        async with session_local(bind=conn) as session:
            await create_tests_data(session)
            nested_tsx = await conn.begin_nested()
            yield session

            if nested_tsx.is_active:
                await nested_tsx.rollback()
            await tsx.rollback()


async def create_tests_data(session):
    user1 = await create_user(
        session,
        UserCreate(
            username="jkowalski",
            password="secret",
            email="jkowalski@example.com",
        ),
    )
    user2 = await create_user(
        session,
        UserCreate(
            username="anowak",
            password="secret",
            email="anowak@example.com",
        ),
    )
    book1 = await create_book(
        session,
        BookCreate(
            title="The Voyage Out",
            author="Virginia Woolf",
            is_public=True,
        ),
        user1.id,
    )
    await set_currently_reading(session, user1.id, book1.id)
    book2 = await create_book(
        session,
        BookCreate(
            title="To The Lighthouse",
            author="Virginia Woolf",
        ),
        user2.id,
    )
    book3 = await create_book(
        session,
        BookCreate(
            title="The Sign of the Four",
            author="Arthur Conan Doyle",
            is_public=True,
        ),
        user2.id,
    )
    book4 = await create_book(
        session,
        BookCreate(
            title="Some Title for Modification",
            author="Some Author For Modification",
        ),
        user1.id,
    )
    word1 = await create_word(
        session,
        WordCreate(
            pos="n",
            lem="chapter",
            declination={"NNS": "chapters"},
            definition="test definition for chapter",
        ),
    )
    word2 = await create_word(
        session,
        WordCreate(
            pos="n",
            lem="respite",
            declination={"NNS": "respites"},
            definition="a (temporary) relief from harm or discomfort",
            synset="reprieve.n.01",
        ),
    )
    word3 = await create_word(
        session,
        WordCreate(
            pos="x",
            lem="word_for_update",
            declination={"XX": "update_this_declination"},
            definition="update this definition",
            synset="update.x.99",
        ),
    )
    word4 = await create_word(
        session,
        WordCreate(
            pos="n",
            lem="brooch",
            declination={"NNS": "brooches"},
            definition="",
            synset="",
        ),
    )
    sentence1 = await create_sentence(
        session,
        SentenceCreate(
            book_id=book1.id,
            nr=1,
            sentence="Words of two or three syllables, with the stress distributed equally between the first syllable and the last.",
        ),
    )
    sentence2 = await create_sentence(
        session,
        SentenceCreate(
            book_id=book1.id,
            nr=2,
            sentence="This sentence should be updated, if you see it - no good!",
        ),
    )
    sentence3 = await create_sentence(
        session,
        SentenceCreate(
            book_id=book1.id, nr=3, sentence="This is the little brooch we all thought was lost."
        ),
    )
    await word_join_to_sentences(session, word4.id, {sentence3.id})
    await word_join_to_sentences(session, word1.id, {sentence3.id})
    flashcard1 = await create_flashcard(
        session,
        FlashcardCreate(user_id=user1.id, keyword="equivocal", translations=["dwuznaczny"]),
        user1.id,
    )
    await create_flashcard(
        session,
        FlashcardCreate(user_id=user1.id, keyword="ambush", translations=["zasadzka"]),
        user1.id,
    )
    await flashcard_join_to_words(session, flashcard1.id, {word1.id})
    await create_flashcard(
        session,
        FlashcardCreate(
            user_id=user1.id,
            keyword="flashcard-for-update",
            translations=["tłumaczenie do aktualizacji"],
        ),
        user1.id,
    )
    await create_flashcard(
        session,
        FlashcardCreate(user_id=user2.id, keyword="well", translations=["studnia"]),
        user2.id,
    )
    await create_flashcard(
        session,
        FlashcardCreate(user_id=user2.id, keyword="dwarf", translations=["krasnal"]),
        user2.id,
    )
    flashcard6 = await create_flashcard(
        session,
        FlashcardCreate(user_id=user1.id, keyword="syllables", translations=["sylaby"]),
        user1.id,
    )
    await flashcard_join_to_sentences(session, flashcard6.id, {sentence1.id})
    await create_translation(session, Translation(
        word="chapter",
        definition="/ˈʧæptə/ <N>\n  rozdział"
    ))

    return session


class BaseTestRouter:
    @pytest_asyncio.fixture(scope="function")
    async def client(self, session):
        app_tested = app
        app_tested.include_router(self.router)
        app_tested.dependency_overrides[get_session] = lambda: session
        async with AsyncClient(app=app_tested, base_url="http://test") as c:
            yield c


class DictionaryClientMock(MagicMock):
    def define(self, *args, **kwargs):
        search_word = args[0]
        possible_responses = {
            "equivocal": [{
                "word": "equivocal",
                "definition": "equivocal /ɪˈkwɪvəkəl/ <Adj>\n  dwuznaczny, niejednoznaczny",
            }]
        }
        return MagicMock(content=possible_responses.get(search_word))
