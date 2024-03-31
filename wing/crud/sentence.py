from fastapi import HTTPException
from sqlalchemy import func, ScalarResult
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


async def get_sentences_for_flashcard(
    session: AsyncSession, book_id: int, flashcard_id: int
) -> ScalarResult[Sentence]:
    query = (
        select(Sentence)
        .join(SentenceFlashcard)
        .where(SentenceFlashcard.flashcard_id == flashcard_id)
        .where(Sentence.book_id == book_id)
        .order_by(Sentence.nr)
    )
    response = await session.execute(query)
    return response.scalars()


async def create_sentence(session: AsyncSession, sentence_create: SentenceCreate) -> Sentence:
    sentence = Sentence(**sentence_create.dict())
    session.add(sentence)
    try:
        await session.commit()
        await session.refresh(sentence)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Can't create sentence")
    return sentence


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


async def count_sentences_for_book(session: AsyncSession, book_id: int) -> int:
    query = select(func.count()).where(Sentence.book_id == book_id)
    response = await session.execute(query)
    return response.scalar_one()


async def get_sentences_with_phrase(
    session: AsyncSession, phrase: str, book_id: [int] = None
) -> ScalarResult[Sentence]:
    query = select(Sentence).where(Sentence.sentence.icontains(phrase)).order_by(Sentence.nr)
    if book_id:
        query = query.where(Sentence.book_id == book_id)
    response = await session.execute(query)
    return response.scalars()
