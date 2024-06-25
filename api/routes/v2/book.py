from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from wing.auth.jwthandler import get_current_user
from wing.crud.book import create_book, find_books, get_book, update_book, delete_book
from wing.crud.flashcard import get_flashcard_ids_for_book
from wing.crud.sentence import get_sentences_for_flashcard
from wing.db.session import get_session
from wing.models.book import Book, BookCreate, BookFind, BookUpdate
from wing.models.sentence import Sentence
from wing.models.user import UserPublic

router = APIRouter(
    prefix="/books",
    tags=["books"],
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
) -> Book:
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


@router.delete(
    "/{book_id}/delete",
    summary="Delete book",
    status_code=status.HTTP_202_ACCEPTED,
)
async def delete_book_route(book_id: int, db: AsyncSession = Depends(get_session)) -> int:
    return await delete_book(session=db, book_id=book_id)


@router.get(
    "/{book_id}/flashcards",
    summary="Get all flashcard ids for book",
    status_code=status.HTTP_200_OK,
    response_model=list[int],
    dependencies=[Depends(get_current_user)],
)
async def get_flashcard_ids_for_book_route(
    book_id: int,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    return await get_flashcard_ids_for_book(session=db, book_id=book_id, user_id=current_user.id)


@router.get(
    "/{book_id}/flashcards/{flashcard_id}/sentences",
    summary="Get sentences for book and flashcard.",
    status_code=status.HTTP_200_OK,
    response_model=list[Sentence],
)
async def get_sentences_for_flashcard_route(
    book_id: int, flashcard_id: int, db: AsyncSession = Depends(get_session)
):
    return await get_sentences_for_flashcard(session=db, book_id=book_id, flashcard_id=flashcard_id)


@router.put(
    "/{book_id}/update",
    summary="Update book",
    status_code=status.HTTP_200_OK,
    response_model=Book,
)
async def update_book_route(
    book_id: int, book: BookUpdate, db: AsyncSession = Depends(get_session)
) -> Book:
    return await update_book(session=db, book_id=book_id, book=book)
