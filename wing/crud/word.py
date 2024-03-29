from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import delete, select

from wing.models.flashcard_word import FlashcardWord
from wing.models.sentence_word import SentenceWord
from wing.models.word import Word, WordCreate, WordUpdate


async def get_word(session: AsyncSession, word_id: int) -> Word:
    query = select(Word).where(Word.id == word_id)
    response = await session.execute(query)
    return response.scalar_one_or_none()


async def get_word_by_lem_pos(session: AsyncSession, lem: str, pos: str) -> Word:
    query = select(Word).where(Word.lem == lem).where(Word.pos == pos)
    response = await session.execute(query)
    return response.scalar_one_or_none()


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


async def update_word_join_to_sentences(
    session: AsyncSession, word_id: int, sentence_ids: set
) -> None:
    for sentence_id in sentence_ids:
        sentence_word = SentenceWord(
            word_id=word_id,
            sentence_id=sentence_id,
        )
        session.add(sentence_word)
    await session.commit()


async def delete_word(session: AsyncSession, word_id: int) -> int:
    query1 = delete(SentenceWord).where(SentenceWord.word_id == word_id)
    query2 = delete(FlashcardWord).where(FlashcardWord.word_id == word_id)
    query3 = delete(Word).where(Word.id == word_id)
    await session.execute(query1)
    await session.execute(query2)
    response = await session.execute(query3)
    await session.commit()
    return response.rowcount
