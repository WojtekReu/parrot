from datetime import timedelta

from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from wing.auth.user import validate_user
from wing.auth.jwthandler import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from wing.db.session import get_session
from wing.models.user import UserPublic

router = APIRouter()


@router.post(
    "/login",
    summary="Login user",
    status_code=status.HTTP_200_OK,
    response_model=UserPublic,
)
async def login_route(
    user: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_session)
):
    user = await validate_user(user=user, session=db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    token = jsonable_encoder(access_token)
    content = {"message": "You've successfully logged in. Welcome back!"}
    response = JSONResponse(content=content)
    response.set_cookie(
        "Authorization",
        value=f"Bearer {token}",
        httponly=True,
        max_age=1800,
        expires=1800,
        samesite="Lax",
        secure=False,
    )

    return response
