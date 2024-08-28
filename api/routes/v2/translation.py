from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from wing.definitions import definitions
from wing.crud.translation import get_translation_by_word
from wing.db.session import get_session
from wing.dictionary import find_translations
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Translation not found in database."
        )
    return translation


@router.get(
    "/dict/{word_str}",
    summary="Find word in external dictionary pl-en DICT",
    status_code=status.HTTP_200_OK,
    response_model=Translation,
)
async def find_translations_route(word_str: str) -> Translation:
    translation_str = await find_translations(word=word_str)
    if not translation_str:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Translation not found in external dictionary.",
        )
    return Translation(word=word_str, definition=translation_str)

@router.get(
    "/synsets/{word_str}",
    summary="Find synsets for the word",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
async def find_synset_route(word_str: str) -> dict:
    return definitions.search_in_nltk(word_str)
