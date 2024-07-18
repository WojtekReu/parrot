from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from wing.models.translation import Translation


async def create_translation(session: AsyncSession, translation: Translation) -> Translation:
    session.add(translation)
    try:
        await session.commit()
        await session.refresh(translation)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Can't create word")
    return translation


async def get_translation_by_word(session: AsyncSession, word_str: str) -> Translation:
    query = select(Translation).where(Translation.word == word_str)
    response = await session.execute(query)
    return response.scalar_one_or_none()
