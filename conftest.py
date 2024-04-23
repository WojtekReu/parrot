import asyncio

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
from wing.crud.book import create_book, find_books
from wing.crud.user import create_user, get_user_by_email
from wing.crud.word import create_word, find_words
from wing.models.book import Book, BookCreate, BookFind
from wing.models.word import WordCreate, WordFind
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
            nested_tsx = await conn.begin_nested()
            yield session

            if nested_tsx.is_active:
                await nested_tsx.rollback()
            await tsx.rollback()


@pytest.fixture
def book():
    return Book(
        title="test book",
        author="test author",
    )


@pytest.fixture
async def book_coroutine(session):
    book_find = BookFind(
        title="The Voyage Out",
        author="Virginia Woolf",
    )
    books = await find_books(session, book_find)
    book = books.first()
    if book:
        return book

    return await create_book(session, BookCreate(**book_find.dict(exclude_unset=True)))


@pytest.fixture
async def word_coroutine(session):
    word_find = WordFind(
        pos="n",
        lem="test",
        declinations=["tests"],
        definition="test definition",
    )
    words = await find_words(session, word_find)
    word = words.first()
    if word:
        return word

    return await create_word(session, WordCreate(**word_find.dict(exclude_unset=True)))


@pytest.fixture
async def user_coroutine(session):
    user = await get_user_by_email(session, "jkowalski@example.com")
    if user:
        return user

    return await create_user(
        session,
        UserCreate(
            username="jkowalski",
            password="secret-password",
            email="jkowalski@example.com",
        ),
    )


class BaseTestRouter:
    @pytest_asyncio.fixture(scope="function")
    async def client(self, session):
        app_tested = app
        app_tested.include_router(self.router)
        app_tested.dependency_overrides[get_session] = lambda: session
        async with AsyncClient(app=app_tested, base_url="http://test") as c:
            yield c
