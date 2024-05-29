from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from wing.crud.word import get_word, create_word, update_word, delete_word
from wing.db.session import get_session
from wing.models.word import Word, WordCreate, WordUpdate

router = APIRouter(
    prefix="/word",
    tags=["word"],
)


@router.post(
    "/",
    summary="Create new word",
    status_code=status.HTTP_201_CREATED,
    response_model=Word,
)
async def put_word_route(word: WordCreate, db: AsyncSession = Depends(get_session)):
    return await create_word(session=db, word=word)


@router.get(
    "/{word_id}",
    summary="Get word",
    status_code=status.HTTP_200_OK,
    response_model=Word,
)
async def get_word_route(word_id: int, db: AsyncSession = Depends(get_session)):
    word = await get_word(session=db, word_id=word_id)
    if not word:
        raise HTTPException(status_code=404, detail="Word not found with the given ID")
    return word


@router.put(
    "/update/{word_id}",
    summary="Update word",
    status_code=status.HTTP_200_OK,
    response_model=Word,
)
async def update_word_route(
    word_id: int, word: WordUpdate, db: AsyncSession = Depends(get_session)
) -> Word:
    return await update_word(session=db, word_id=word_id, word=word)


@router.delete(
    "/delete/{word_id}",
    summary="Delete word",
    status_code=status.HTTP_202_ACCEPTED,
)
async def delete_word_route(word_id: int, db: AsyncSession = Depends(get_session)) -> int:
    return await delete_word(session=db, word_id=word_id)
