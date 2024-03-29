from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import delete, select

from wing.models.sentence import Sentence, SentenceCreate
from wing.models.sentence_word import SentenceWord
from wing.models.sentence_flashcard import SentenceFlashcard


async def get_sentence(session: AsyncSession, sentence_id: int) -> Sentence:
    query = select(Sentence).where(Sentence.id == sentence_id)
    response = await session.execute(query)
    return response.scalar_one_or_none()


async def create_sentence(session: AsyncSession, book: SentenceCreate) -> Sentence:
    db_book = Sentence(**book.dict())
    session.add(db_book)
    try:
        await session.commit()
        await session.refresh(db_book)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Can't create sentence")
    return db_book


async def delete_sentence(session: AsyncSession, sentence_id: int) -> int:
    query1 = delete(SentenceWord).where(SentenceWord.sentence_id == sentence_id)
    query2 = delete(SentenceFlashcard).where(SentenceFlashcard.sentence_id == sentence_id)
    query3 = delete(Sentence).where(Sentence.id == sentence_id)
    await session.execute(query1)
    await session.execute(query2)
    response = await session.execute(query3)
    await session.commit()
    return response.rowcount


async def delete_sentences_by_book(session: AsyncSession, book_id: int) -> int:
    query = delete(Sentence).where(Sentence.book_id == book_id)
    response = await session.execute(query)
    await session.commit()
    return response.rowcount
