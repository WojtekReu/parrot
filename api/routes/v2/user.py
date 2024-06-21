from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from wing.auth.jwthandler import get_current_user
from wing.crud.user import create_user, get_user
from wing.db.session import get_session
from wing.models.user import UserCreate, UserPublic

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


@router.get(
    "/{user_id}",
    summary="Get a user.",
    status_code=status.HTTP_200_OK,
    response_model=UserPublic,
)
async def get_user_route(user_id: int, db: AsyncSession = Depends(get_session)):
    user = await get_user(session=db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found with the given ID")
    return user


@router.get(
    "/users/whoami",
    summary="Get logged in user.",
    status_code=status.HTTP_200_OK,
    response_model=UserPublic,
    dependencies=[Depends(get_current_user)],
)
async def get_current_user_route(current_user: UserPublic = Depends(get_current_user)):
    return current_user
