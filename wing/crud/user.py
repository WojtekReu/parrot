from fastapi import HTTPException
from fastapi_pagination import Page
from fastapi_pagination.default import Params
from fastapi_pagination.ext.sqlmodel import paginate
from passlib.context import CryptContext
from sqlalchemy import ScalarResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import delete, select

from wing.crud.base import find_model
from wing.models.book import Book
from wing.models.flashcard import Flashcard
from wing.models.user import User, UserCreate, UserFind, UserUpdate, UserPublic
from wing.models.token import Status

DEFAULT_PAGINATION_OFFSET = 1
FLASHCARDS_PAGINATION_LIMIT = 100
BOOKS_PAGINATION_LIMIT = 20

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_user(session: AsyncSession, user_id: int) -> User:
    query = select(User).where(User.id == user_id)
    response = await session.execute(query)
    return response.scalar_one_or_none()


async def get_user_by_username(session: AsyncSession, username: str) -> User:
    query = select(User).where(User.username == username)
    response = await session.execute(query)
    return response.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> User:
    query = select(User).where(User.email == email)
    response = await session.execute(query)
    return response.scalar_one_or_none()


async def find_users(session: AsyncSession, user: UserFind) -> ScalarResult:
    return await find_model(session=session, instance_filter=user, model=User)


async def create_user(session: AsyncSession, user: UserCreate) -> User:
    db_user = User(**user.dict())
    db_user.password = pwd_context.encrypt(user.password)
    session.add(db_user)
    try:
        await session.commit()
        await session.refresh(db_user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Can't create user")
    return db_user


async def update_user(session: AsyncSession, user_id: int, user: UserUpdate) -> User:
    db_user = await get_user(session, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail=f"Not found user by id: {user_id}")

    for k, v in user.dict(exclude_unset=True).items():
        setattr(db_user, k, v)

    try:
        await session.commit()
        await session.refresh(db_user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail=f"Can't update user, user_id: {user_id}")
    return db_user


async def delete_user(session: AsyncSession, user_id: int, current_user) -> Status:
    query = delete(User).where(current_user.id == user_id)
    response = await session.execute(query)
    await session.commit()
    return Status(message=f"Deleted user {user_id}")


async def get_user_flashcards(session: AsyncSession, current_user: UserPublic) -> Page[Flashcard]:
    query = select(Flashcard).where(Flashcard.user_id == current_user.id)
    return await paginate(
        session,
        query,
        Params(limit=FLASHCARDS_PAGINATION_LIMIT, offset=DEFAULT_PAGINATION_OFFSET),
    )


async def get_user_books(session: AsyncSession, current_user: UserPublic) -> Page[Book]:
    query = select(Book).where(Book.user_id == current_user.id).order_by(Book.id)
    return await paginate(
        session,
        query,
        Params(limit=BOOKS_PAGINATION_LIMIT, offset=DEFAULT_PAGINATION_OFFSET),
    )
