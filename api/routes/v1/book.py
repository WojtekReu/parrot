from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from wing.crud.book import create_book, find_books, get_book, update_book, delete_book
from wing.db.session import get_session
from wing.models.book import Book, BookCreate, BookFind, BookUpdate

router = APIRouter(
    prefix="/book",
    tags=["book"],
)


@router.put(
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
    return await find_books(session=db, book=BookFind())


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


@router.patch(
    "/update/{book_id}",
    summary="Update book",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_book_route(
    book_id: int, data: BookUpdate, db: AsyncSession = Depends(get_session)
) -> None:
    await update_book(session=db, book_id=book_id, book=data)


@router.delete(
    "/delete/{book_id}",
    summary="Delete book",
    status_code=status.HTTP_202_ACCEPTED,
)
async def delete_book_route(book_id: int, db: AsyncSession = Depends(get_session)) -> int:
    return await delete_book(session=db, book_id=book_id)
