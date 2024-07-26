from fastapi import HTTPException
from sqlalchemy import func, ScalarResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import delete, select, distinct

from wing.models.book import Book
from wing.models.flashcard import Flashcard
from wing.models.sentence import Sentence, SentenceCreate
from wing.models.sentence_word import SentenceWord
from wing.models.sentence_flashcard import SentenceFlashcard
from wing.models.word import Word


async def get_sentence(
    session: AsyncSession, sentence_id: int, user_id: int | None = None
) -> Sentence:
    query = select(Sentence).where(Sentence.id == sentence_id)
    if user_id:
        query = query.where(Sentence.book_id == Book.id).where(Book.user_id == user_id)
    response = await session.execute(query)
    return response.scalar_one_or_none()


async def get_sentences_for_flashcard(
    session: AsyncSession,
    book_id: int,
    flashcard_id: int,
    user_id: int,
) -> ScalarResult[Sentence]:
    query = (
        select(Sentence)
        .where(Sentence.book_id == book_id)
        .where(SentenceFlashcard.sentence_id == Sentence.id)
        .where(SentenceFlashcard.flashcard_id == flashcard_id)
        .where(SentenceFlashcard.flashcard_id == Flashcard.id)
        .where(Flashcard.user_id == user_id)
        .order_by(Sentence.nr)
    )
    response = await session.execute(query)
    return response.scalars()


async def get_sentence_ids(session: AsyncSession, word: Word, book_id: int) -> list[int]:
    query = (
        select(distinct(SentenceWord.sentence_id))
        .select_from(SentenceWord)
        .join(Sentence)
        .where(Sentence.book_id == book_id)
        .where(SentenceWord.word_id == word.id)
    )
    response = await session.execute(query)
    return [sentence_id for sentence_id in response.scalars()]


async def create_sentence(session: AsyncSession, sentence: SentenceCreate) -> Sentence:
    db_sentence = Sentence(**sentence.dict())
    session.add(db_sentence)
    try:
        await session.commit()
        await session.refresh(db_sentence)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Can't create sentence")
    return db_sentence


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
