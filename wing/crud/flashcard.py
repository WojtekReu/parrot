from fastapi import HTTPException
from sqlalchemy import ScalarResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import delete, select, distinct

from wing.models.flashcard import Flashcard, FlashcardCreate, FlashcardFind, FlashcardUpdate
from wing.models.flashcard_word import FlashcardWord
from wing.models.sentence import Sentence
from wing.models.sentence_flashcard import SentenceFlashcard


async def get_flashcard(session: AsyncSession, flashcard_id: int) -> Flashcard:
    query = select(Flashcard).where(Flashcard.id == flashcard_id)
    response = await session.execute(query)
    return response.scalar_one_or_none()


async def find_flashcards(session: AsyncSession, flashcard: FlashcardFind) -> ScalarResult:
    query = select(Flashcard).order_by(Flashcard.id)
    for column_name, value in flashcard.dict(exclude_unset=True).items():
        query = query.where(getattr(Flashcard, column_name) == value)
    response = await session.execute(query)
    return response.scalars()


async def get_flashcards_by_keyword(session: AsyncSession, keyword: str) -> ScalarResult[Flashcard]:
    query = select(Flashcard).where(Flashcard.keyword == keyword)
    response = await session.execute(query)
    return response.scalars()


async def get_flashcard_ids_for_book(
    session: AsyncSession, book_id: int, user_id: int
) -> list[int]:
    query = (
        select(distinct(SentenceFlashcard.flashcard_id))
        .select_from(SentenceFlashcard)
        .join(Sentence)
        .join(Flashcard)
        .where(Flashcard.user_id == user_id)
        .where(Sentence.book_id == book_id)
    )
    response = await session.execute(query)
    return [sf for sf in response.scalars()]


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


async def update_flashcard(
    session: AsyncSession, flashcard_id: int, flashcard: FlashcardUpdate
) -> Flashcard:
    db_flashcard = await get_flashcard(session, flashcard_id)
    if not db_flashcard:
        raise HTTPException(status_code=404, detail=f"Not found flashcard by id: {flashcard_id}")

    for k, v in flashcard.dict(exclude_unset=True).items():
        setattr(db_flashcard, k, v)

    try:
        await session.commit()
        await session.refresh(db_flashcard)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409, detail=f"Can't update flashcard, flashcard_id: {flashcard_id}"
        )
    return db_flashcard


async def flashcard_join_to_sentences(
    session: AsyncSession, flashcard_id: int, sentence_ids: set
) -> None:
    for sentence_id in sentence_ids:
        result = await session.execute(
            select(SentenceFlashcard)
            .where(SentenceFlashcard.flashcard_id == flashcard_id)
            .where(SentenceFlashcard.sentence_id == sentence_id)
        )
        if not result.first():
            sentence_flashcard = SentenceFlashcard(
                flashcard_id=flashcard_id,
                sentence_id=sentence_id,
            )
            session.add(sentence_flashcard)
    await session.commit()


async def flashcard_join_to_word(session: AsyncSession, flashcard_id: int, word_ids: set) -> None:
    for word_id in word_ids:
        result = await session.execute(
            select(FlashcardWord)
            .where(FlashcardWord.flashcard_id == flashcard_id)
            .where(FlashcardWord.word_id == word_id)
        )
        if not result.first():
            flashcard_word = FlashcardWord(
                flashcard_id=flashcard_id,
                word_id=word_id,
            )
            session.add(flashcard_word)
    await session.commit()


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
