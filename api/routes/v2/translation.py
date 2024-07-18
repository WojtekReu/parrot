from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from wing.crud.translation import get_translation_by_word
from wing.db.session import get_session
from wing.models.translation import Translation

router = APIRouter(
    prefix="/translation",
    tags=["translation"],
)


@router.get(
    "/find/{word_str}",
    summary="Get word translation from database table",
    status_code=status.HTTP_200_OK,
    response_model=Translation,
)
async def get_translation_route(
    word_str: str, db: AsyncSession = Depends(get_session)
) -> Translation:
    translation = await get_translation_by_word(session=db, word_str=word_str)
    if not translation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Translation not found.")
    return translation
