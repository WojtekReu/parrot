from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from wing.crud.flashcard import create_flashcard, get_flashcard, get_flashcard_ids_for_book
from wing.db.session import get_session
from wing.models.flashcard import Flashcard, FlashcardCreate

router = APIRouter(
    prefix="/flashcard",
    tags=["flashcard"],
)


@router.put(
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
