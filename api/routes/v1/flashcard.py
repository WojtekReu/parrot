from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from wing.crud.flashcard import (
    create_flashcard,
    get_flashcard,
    get_flashcard_ids_for_book,
    flashcard_join_to_sentences,
    flashcard_separate_sentences,
    get_flashcard_words,
)
from wing.db.session import get_session
from wing.models.flashcard import Flashcard, FlashcardCreate
from wing.models.word import Word

router = APIRouter(
    prefix="/flashcard",
    tags=["flashcard"],
)


@router.post(
    "/",
    summary="Create a new flashcard.",
    status_code=status.HTTP_201_CREATED,
    response_model=Flashcard,
)
async def create_flashcard_route(
    data: FlashcardCreate,
    db: AsyncSession = Depends(get_session),
):
    return await create_flashcard(session=db, flashcard=data)


@router.get(
    "/{flashcard_id}",
    summary="Get a flashcard.",
    status_code=status.HTTP_200_OK,
    response_model=Flashcard,
)
async def get_flashcard_route(flashcard_id: int, db: AsyncSession = Depends(get_session)):
    flashcard = await get_flashcard(session=db, flashcard_id=flashcard_id)
    if flashcard is None:
        raise HTTPException(status_code=404, detail="Flashcard not found with the given ID")
    return flashcard


@router.get(
    "/book/{book_id}",
    summary="Get all flashcard ids for book",
    status_code=status.HTTP_200_OK,
    response_model=list[int],
)
async def get_flashcard_ids_for_book_route(book_id: int, db: AsyncSession = Depends(get_session)):
    return await get_flashcard_ids_for_book(session=db, book_id=book_id, user_id=1)


@router.post(
    "/match-flashcard-sentences/{flashcard_id}",
    summary="Update relations between flashcard and sentences",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def match_flashcard_sentences_route(
    flashcard_id: int,
    disconnect_ids: set[int],
    sentence_ids: set[int],
    db: AsyncSession = Depends(get_session),
) -> None:
    if disconnect_ids:
        await flashcard_separate_sentences(db, flashcard_id, disconnect_ids)
    return await flashcard_join_to_sentences(db, flashcard_id, sentence_ids)


@router.get(
    "/{flashcard_id}/words",
    summary="Get words related to flashcard",
    status_code=status.HTTP_200_OK,
    response_model=list[Word],
)
async def get_flashcard_words_route(
    flashcard_id: int, db: AsyncSession = Depends(get_session)
) -> ScalarResult[Word]:
    return await get_flashcard_words(session=db, flashcard_id=flashcard_id)
