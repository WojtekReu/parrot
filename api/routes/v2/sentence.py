from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from wing.auth.jwthandler import get_current_user
from wing.crud.book import get_book
from wing.crud.sentence import (
    create_sentence,
    get_sentence,
)
from wing.db.session import get_session
from wing.models.sentence import Sentence, SentenceCreate
from wing.models.user import UserPublic

router = APIRouter(
    prefix="/sentences",
    tags=["sentences"],
)


@router.post(
    "/",
    summary="Create a new sentence.",
    status_code=status.HTTP_201_CREATED,
    response_model=Sentence,
    dependencies=[Depends(get_current_user)],
)
async def create_sentence_route(
    data: SentenceCreate,
    db: AsyncSession = Depends(get_session),
    current_user: UserPublic = Depends(get_current_user),
):
    book = get_book(db, data.book_id, current_user.id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Book not found by id: {data.book_id}"
        )
    return await create_sentence(session=db, sentence=data)


@router.get(
    "/{sentence_id}",
    summary="Get a sentence.",
    status_code=status.HTTP_200_OK,
    response_model=Sentence,
)
async def get_book_route(sentence_id: int, db: AsyncSession = Depends(get_session)):
    sentence = await get_sentence(session=db, sentence_id=sentence_id)
    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found with the given ID")
    return sentence
