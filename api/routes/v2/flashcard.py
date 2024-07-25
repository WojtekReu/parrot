from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from wing.auth.jwthandler import get_current_user
from wing.crud.flashcard import (
    create_flashcard,
    get_flashcard,
    flashcard_join_to_sentences,
    flashcard_separate_sentences,
    get_flashcard_words,
    update_flashcard,
    get_flashcards_by_keyword,
)
from wing.db.session import get_session
from wing.models.flashcard import Flashcard, FlashcardCreate, FlashcardUpdate
from wing.models.user import UserPublic
from wing.models.word import Word

router = APIRouter(
    prefix="/flashcards",
    tags=["flashcards"],
)


@router.post(
    "/",
    summary="Create a new flashcard.",
    status_code=status.HTTP_201_CREATED,
    response_model=Flashcard,
    dependencies=[Depends(get_current_user)],
)
async def create_flashcard_route(
    data: FlashcardCreate,
    db: AsyncSession = Depends(get_session),
    current_user: UserPublic = Depends(get_current_user),
):
    return await create_flashcard(session=db, flashcard=data, user_id=current_user.id)


@router.get(
    "/find/{keyword}",
    summary="Get flashcards by keyword",
    status_code=status.HTTP_200_OK,
    response_model=list[Flashcard],
    dependencies=[Depends(get_current_user)],
)
async def find_flashcards_route(
    keyword: str,
    db: AsyncSession = Depends(get_session),
    current_user: UserPublic = Depends(get_current_user),
) -> ScalarResult[Flashcard]:
    return await get_flashcards_by_keyword(session=db, keyword=keyword, user_id=current_user.id)


@router.get(
    "/{flashcard_id}",
    summary="Get a flashcard.",
    status_code=status.HTTP_200_OK,
    response_model=Flashcard,
    dependencies=[Depends(get_current_user)],
)
async def get_flashcard_route(
    flashcard_id: int,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    flashcard = await get_flashcard(session=db, flashcard_id=flashcard_id, user_id=current_user.id)
    if flashcard is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flashcard not found with the given ID"
        )
    return flashcard


@router.post(
    "/{flashcard_id}/sentences",
    summary="Update relations between flashcard and sentences",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_user)],
)
async def match_flashcard_sentences_route(
    flashcard_id: int,
    disconnect_ids: set[int],
    sentence_ids: set[int],
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> None:
    flashcard = get_flashcard(db, flashcard_id, current_user.id)

    if not flashcard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flashcard not found by id: {flashcard_id}",
        )

    if disconnect_ids:
        await flashcard_separate_sentences(db, flashcard_id, disconnect_ids)
    return await flashcard_join_to_sentences(db, flashcard_id, sentence_ids)


@router.put(
    "/{flashcard_id}/update",
    summary="Update flashcard",
    status_code=status.HTTP_200_OK,
    response_model=Flashcard,
    dependencies=[Depends(get_current_user)],
)
async def update_flashcard_route(
    flashcard_id: int,
    flashcard: FlashcardUpdate,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Flashcard:
    return await update_flashcard(
        session=db, flashcard_id=flashcard_id, user_id=current_user.id, flashcard=flashcard
    )


@router.get(
    "/{flashcard_id}/words",
    summary="Get words related to flashcard",
    status_code=status.HTTP_200_OK,
    response_model=list[Word],
    dependencies=[Depends(get_current_user)],
)
async def get_flashcard_words_route(
    flashcard_id: int,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> ScalarResult[Word]:
    flashcard = await get_flashcard(session=db, flashcard_id=flashcard_id, user_id=current_user.id)
    if not flashcard:
        raise HTTPException(status_code=404, detail="Flashcard not found with the given ID")
    return await get_flashcard_words(session=db, flashcard_id=flashcard_id)
