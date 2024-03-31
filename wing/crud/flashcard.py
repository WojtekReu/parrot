from typing import AsyncIterable

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import delete, select

from wing.models.flashcard import Flashcard, FlashcardCreate
from wing.models.flashcard_word import FlashcardWord
from wing.models.sentence_flashcard import SentenceFlashcard


async def get_flashcard(session: AsyncSession, flashcard_id: int) -> Flashcard:
    query = select(Flashcard).where(Flashcard.id == flashcard_id)
    response = await session.execute(query)
    return response.scalar_one_or_none()


async def get_flashcards_by_keyword(
    session: AsyncSession, keyword: str
) -> AsyncIterable[Flashcard]:
    query = select(Flashcard).where(Flashcard.keyword == keyword)
    response = await session.execute(query)
    for row in response.fetchall():
        yield row[0]


async def create_flashcard(session: AsyncSession, flashcard: FlashcardCreate) -> Flashcard:
    db_flashcard = Flashcard(**flashcard.dict())
    session.add(db_flashcard)
    try:
        await session.commit()
        await session.refresh(db_flashcard)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Can't create flashcard")
    return db_flashcard


async def delete_flashcard(session: AsyncSession, flashcard_id: int) -> int:
    query1 = delete(FlashcardWord).where(FlashcardWord.flashcard_id == flashcard_id)
    query2 = delete(SentenceFlashcard).where(SentenceFlashcard.flashcard_id == flashcard_id)
    query3 = delete(Flashcard).where(Flashcard.id == flashcard_id)
    await session.execute(query1)
    await session.execute(query2)
    response = await session.execute(query3)
    await session.commit()
    return response.rowcount


async def delete_flashcards_by_book(session: AsyncSession, book_id: int) -> int:
    query = delete(Flashcard).where(Flashcard.book_id == book_id)
    response = await session.execute(query)
    await session.commit()
    return response.rowcount
