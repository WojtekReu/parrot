from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from wing.crud.sentence import (
    create_sentence,
    get_sentence,
    get_sentences_with_phrase,
    get_sentences_for_flashcard,
)
from wing.db.session import get_session
from wing.models.sentence import Sentence, SentenceCreate

router = APIRouter(
    prefix="/sentence",
    tags=["sentence"],
)


@router.post(
    "/",
    summary="Create a new sentence.",
    status_code=status.HTTP_201_CREATED,
    response_model=Sentence,
)
async def create_sentence_route(
    data: SentenceCreate,
    db: AsyncSession = Depends(get_session),
):
    return await create_sentence(session=db, sentence_create=data)


@router.get(
    "/book/{book_id}/{flashcard_id}",
    summary="Get sentences for book and flashcard.",
    status_code=status.HTTP_200_OK,
    response_model=list[Sentence],
)
async def get_sentences_for_flashcard_route(
    book_id: int, flashcard_id: int, db: AsyncSession = Depends(get_session)
):
    return await get_sentences_for_flashcard(session=db, book_id=book_id, flashcard_id=flashcard_id)


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
