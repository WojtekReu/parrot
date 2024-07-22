from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from wing.auth.jwthandler import get_current_user
from wing.crud.user import create_user, get_user, get_user_flashcards, find_users
from wing.db.session import get_session
from wing.models.user import UserCreate, UserFind, UserPublic
from wing.models.flashcard import Flashcard


router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post(
    "/",
    summary="Create a new user.",
    status_code=status.HTTP_201_CREATED,
    response_model=UserPublic,
)
async def create_user_route(
    data: UserCreate,
    db: AsyncSession = Depends(get_session),
):
    return await create_user(session=db, user=data)


@router.post(
    "/search",
    summary="Search user.",
    status_code=status.HTTP_200_OK,
    response_model=list[UserPublic],
)
async def get_users_route(data: UserFind, db: AsyncSession = Depends(get_session)):
    return await find_users(session=db, user=data)


@router.get(
    "/whoami",
    summary="Get logged in user.",
    status_code=status.HTTP_200_OK,
    response_model=UserPublic,
    dependencies=[Depends(get_current_user)],
)
async def get_current_user_route(current_user: UserPublic = Depends(get_current_user)):
    return current_user


@router.get(
    "/flashcards",
    summary="Get current user flashcards.",
    status_code=status.HTTP_200_OK,
    response_model=list[Flashcard],
    dependencies=[Depends(get_current_user)],
)
async def get_user_flashcards_route(
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    return await get_user_flashcards(session=db, current_user=current_user)


@router.get(
    "/{user_id}",
    summary="Get a user.",
    status_code=status.HTTP_200_OK,
    response_model=UserPublic,
)
async def get_user_route(user_id: int, db: AsyncSession = Depends(get_session)):
    user = await get_user(session=db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found with the given ID"
        )
    return user
