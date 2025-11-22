from fastapi import HTTPException, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate
from sqlalchemy import or_, ScalarResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import delete, select

from wing.models.book import Book, BookCreate, BookFind, BookUpdate
from wing.models.currently_reading import CurrentlyReading


async def get_book(session: AsyncSession, book_id: int, user_id: int | None = None) -> Book:
    query = select(Book).where(Book.id == book_id)
    if user_id:
        query = query.where(or_(Book.user_id == user_id, Book.is_public == True))
    response = await session.execute(query)
    return response.scalar_one_or_none()


async def find_books(session: AsyncSession, book: BookFind) -> Page[Book]:
    query = select(Book).order_by(Book.id)
    for attr_name, value in book.dict(exclude_unset=True).items():
        query = query.where(getattr(Book, attr_name) == value)
    return await paginate(session, query)


async def find_books_no_pagination(session: AsyncSession, book: BookFind) -> ScalarResult[Book]:
    query = select(Book).order_by(Book.id)

    for attr_name, value in book.dict(exclude_unset=True).items():
        query = query.where(getattr(Book, attr_name) == value)

    response = await session.execute(query)
    return response.scalars()


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


async def get_currently_reading(session: AsyncSession, user_id: int) -> ScalarResult[int]:
    query = select(CurrentlyReading.book_id).where(CurrentlyReading.user_id == user_id)
    response = await session.execute(query)
    return response.scalars()


async def set_currently_reading(session: AsyncSession, user_id: int, book_id: int) -> None:
    session.add(CurrentlyReading(user_id=user_id, book_id=book_id))
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()


async def unset_currently_reading(session: AsyncSession, user_id: int, book_id: int) -> None:
    query = delete(CurrentlyReading).where(
        CurrentlyReading.user_id == user_id, CurrentlyReading.book_id == book_id
    )
    try:
        await session.execute(query)
        await session.commit()
    except IntegrityError:
        await session.rollback()
