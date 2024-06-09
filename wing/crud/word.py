from fastapi import HTTPException
from sqlalchemy import distinct, func, ScalarResult, Result
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import delete, select

from wing.crud.base import model_join_to_set, model_separate_list
from wing.crud.sentence import get_sentence
from wing.models.flashcard_word import FlashcardWord
from wing.models.sentence import Sentence
from wing.models.sentence_word import SentenceWord
from wing.models.word import Word, WordCreate, WordUpdate, WordFind
from wing.ask_ml import find_definition


async def get_word(session: AsyncSession, word_id: int) -> Word:
    query = select(Word).where(Word.id == word_id)
    response = await session.execute(query)
    return response.scalar_one_or_none()


async def find_words(session: AsyncSession, word: WordFind) -> ScalarResult[Word]:
    query = select(Word).order_by(Word.id)
    for column_name, value in word.dict(exclude_unset=True).items():
        query = query.where(getattr(Word, column_name) == value)
    response = await session.execute(query)
    return response.scalars()


async def create_word(session: AsyncSession, word: WordCreate) -> Word:
    db_word = Word(**word.dict())
    session.add(db_word)
    try:
        await session.commit()
        await session.refresh(db_word)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Can't create word")
    return db_word


async def update_word(session: AsyncSession, word_id: int, word: WordUpdate) -> Word:
    db_word = await get_word(session, word_id)
    if not db_word:
        raise HTTPException(status_code=404, detail=f"Not found book by id: {word_id}")

    for k, v in word.dict(exclude_unset=True).items():
        setattr(db_word, k, v)

    try:
        await session.commit()
        await session.refresh(db_word)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail=f"Can't update word, word_id: {word_id}")
    return db_word


async def word_join_to_sentences(session: AsyncSession, word_id: int, sentence_ids: set) -> None:
    await model_join_to_set(
        session=session,
        relation_model=SentenceWord,
        source_id_name="word_id",
        source_id=word_id,
        target_id_name="sentence_id",
        target_ids=sentence_ids,
    )


async def delete_word(session: AsyncSession, word_id: int) -> int:
    query1 = delete(SentenceWord).where(SentenceWord.word_id == word_id)
    query2 = delete(FlashcardWord).where(FlashcardWord.word_id == word_id)
    query3 = delete(Word).where(Word.id == word_id)
    await session.execute(query1)
    await session.execute(query2)
    response = await session.execute(query3)
    await session.commit()
    return response.rowcount


async def count_words_for_book(session: AsyncSession, book_id) -> int:
    query = (
        select(func.count(distinct(SentenceWord.word_id)))
        .select_from(Sentence)
        .join(SentenceWord)
        .where(Sentence.book_id == book_id)
    )
    response = await session.execute(query)
    return response.scalar_one()


async def get_sentence_ids_with_word(session: AsyncSession, word_text: str) -> list[int]:
    query = (
        select(SentenceWord)
        .select_from(SentenceWord)
        .join(Word)
        .where(Word.lem == word_text)
        .order_by(SentenceWord.id)
    )
    response = await session.execute(query)
    return [sentence_word.sentence_id for sentence_word in response.scalars()]


async def find_synset(session: AsyncSession, flashcard_id: int, sentence_id: int) -> dict:
    query = (
        select(Word)
        .join(FlashcardWord)
        .where(Word.id == FlashcardWord.word_id, FlashcardWord.flashcard_id == flashcard_id)
    )
    response = await session.execute(query)
    words = response.first()
    if words:
        word = words[0]
        sentence = await get_sentence(session=session, sentence_id=sentence_id)
        res1 = find_definition(word.lem, sentence.sentence)
        result = {
            "word": word,
            "synsets": res1["synsets"],
        }
        return result
    return {}


async def word_separate_sentences(
    session: AsyncSession, word_id: int, sentence_ids: set[int]
) -> Result:
    return await model_separate_list(
        session=session,
        relation_model=SentenceWord,
        source_id_name="word_id",
        source_id=word_id,
        target_id_name="sentence_id",
        target_ids=sentence_ids,
    )


async def find_words_for_flashcard(
    session: AsyncSession,
    flashcard_id: int,
) -> ScalarResult[Word]:
    query = (
        select(Word)
        .join(FlashcardWord)
        .where(Word.id == FlashcardWord.word_id, FlashcardWord.flashcard_id == flashcard_id)
    )
    response = await session.execute(query)
    return response.scalars()
