from fastapi import HTTPException
from sqlalchemy import Result, ScalarResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import delete, select, distinct

from wing.crud.base import model_join_to_set, model_separate_list, get_related_list
from wing.models.flashcard import Flashcard, FlashcardCreate, FlashcardFind, FlashcardUpdate
from wing.models.flashcard_word import FlashcardWord
from wing.models.sentence import Sentence
from wing.models.sentence_flashcard import SentenceFlashcard
from wing.models.word import Word


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
    await model_join_to_set(
        session=session,
        relation_model=SentenceFlashcard,
        source_id_name="flashcard_id",
        source_id=flashcard_id,
        target_id_name="sentence_id",
        target_ids=sentence_ids,
    )


async def flashcard_join_to_words(session: AsyncSession, flashcard_id: int, word_ids: set) -> None:
    await model_join_to_set(
        session=session,
        relation_model=FlashcardWord,
        source_id_name="flashcard_id",
        source_id=flashcard_id,
        target_id_name="word_id",
        target_ids=word_ids,
    )


async def get_flashcard_words(
    session: AsyncSession,
    flashcard_id: int,
) -> ScalarResult[Word]:
    return await get_related_list(
        session=session,
        target_model=Word,
        relation_model=FlashcardWord,
        relation_id_name="flashcard_id",
        relation_id=flashcard_id,
        target_id_name="word_id",
    )


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


async def flashcard_separate_sentences(
    session: AsyncSession, flashcard_id: int, sentence_ids: set[int]
) -> Result:
    return await model_separate_list(
        session=session,
        relation_model=SentenceFlashcard,
        source_id_name="flashcard_id",
        source_id=flashcard_id,
        target_id_name="sentence_id",
        target_ids=sentence_ids,
    )
