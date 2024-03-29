import asyncio

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlmodel import SQLModel

from wing.models.book import Book, BookCreate
from wing.models.word import WordCreate

ENGINE_URL = ""


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
def book_create():
    return BookCreate(
        title="test book",
        author="test author",
    )


@pytest.fixture
def word_create():
    return WordCreate(
        count=0,
        pos="n",
        lem="test",
        declinations=["tests"],
        definition="test definition",
    )
