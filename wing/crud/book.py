from fastapi import HTTPException, status
from sqlalchemy import ScalarResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import delete, select

from wing.crud.base import find_model
from wing.models.book import Book, BookCreate, BookFind, BookUpdate


async def get_book(session: AsyncSession, book_id: int, user_id: int | None = None) -> Book:
    query = select(Book).where(Book.id == book_id)
    if user_id:
        query = query.where(Book.user_id == user_id)
    response = await session.execute(query)
    return response.scalar_one_or_none()


async def find_books(session: AsyncSession, book: BookFind) -> ScalarResult:
    return await find_model(session=session, instance_filter=book, model=Book)


async def create_book(session: AsyncSession, book: BookCreate, user_id: int) -> Book:
    db_book = Book(**book.dict())
    db_book.user_id = user_id
    session.add(db_book)
    try:
        await session.commit()
        await session.refresh(db_book)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Can't create book")
    return db_book


async def update_book(session: AsyncSession, book_id: int, user_id: int, book: BookUpdate) -> Book:
    db_book = await get_book(session, book_id)
    if db_book.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"This user can not book by id: {book_id}",
        )
    if not db_book:
        raise HTTPException(status_code=404, detail=f"Not found book by id: {book_id}")

    for k, v in book.dict(exclude_unset=True).items():
        setattr(db_book, k, v)

    try:
        await session.commit()
        await session.refresh(db_book)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail=f"Can't update book, book_id: {book_id}")
    return db_book


async def delete_book(session: AsyncSession, book_id: int, user_id: int) -> int:
    query = delete(Book).where(Book.id == book_id, Book.user_id == user_id)
    response = await session.execute(query)
    await session.commit()
    return response.rowcount
