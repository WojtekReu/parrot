from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from wing.crud.user import create_user, get_user
from wing.db.session import get_session
from wing.models.user import UserCreate, UserResponse

router = APIRouter(
    prefix="/user",
    tags=["user"],
)


@router.put(
    "/",
    summary="Create a new user.",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
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
    response_model=UserResponse,
)
async def get_user_route(user_id: int, db: AsyncSession = Depends(get_session)):
    user = await get_user(session=db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found with the given ID")
    return user
