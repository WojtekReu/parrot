from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from wing.crud.book import create_book, get_book, get_books
from wing.db.session import get_session
from wing.models.book import BookCreate, Book

router = APIRouter(
    prefix="/book",
    tags=["book"],
)


@router.post(
    "/",
    summary="Create a new book.",
    status_code=status.HTTP_201_CREATED,
    response_model=Book,
)
async def create_book_route(
    data: BookCreate,
    db: AsyncSession = Depends(get_session),
):
    return await create_book(session=db, book=data)


@router.get(
    "/all",
    summary="Get all books.",
    status_code=status.HTTP_200_OK,
    response_model=list[Book],
)
async def get_books_route(db: AsyncSession = Depends(get_session)):
    return await get_books(session=db)


@router.get(
    "/{book_id}",
    summary="Get a book.",
    status_code=status.HTTP_200_OK,
    response_model=Book,
)
async def get_book_route(book_id: int, db: AsyncSession = Depends(get_session)):
    book = await get_book(session=db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found with the given ID")
    return book
