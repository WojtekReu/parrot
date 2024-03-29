from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import delete, select

from wing.models.user import User, UserCreate, UserUpdate


async def get_user(session: AsyncSession, user_id: int) -> User:
    query = select(User).where(User.id == user_id)
    response = await session.execute(query)
    return response.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> User:
    query = select(User).where(User.email == email)
    response = await session.execute(query)
    return response.scalar_one_or_none()


async def create_user(session: AsyncSession, user: UserCreate) -> User:
    db_user = User(**user.dict())
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


async def delete_user(session: AsyncSession, user_id: int) -> int:
    query = delete(User).where(User.id == user_id)
    response = await session.execute(query)
    await session.commit()
    return response.rowcount
