from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from wing.crud.word import (
    get_word,
    create_word,
    update_word,
    delete_word,
    find_synset,
    word_join_to_sentences,
    word_separate_sentences,
    find_words_for_flashcard,
)
from wing.db.session import get_session
from wing.models.word import Word, WordCreate, WordUpdate

router = APIRouter(
    prefix="/word",
    tags=["word"],
)


@router.post(
    "/",
    summary="Create new word",
    status_code=status.HTTP_201_CREATED,
    response_model=Word,
)
async def put_word_route(word: WordCreate, db: AsyncSession = Depends(get_session)):
    return await create_word(session=db, word=word)


@router.get(
    "/{word_id}",
    summary="Get word",
    status_code=status.HTTP_200_OK,
    response_model=Word,
)
async def get_word_route(word_id: int, db: AsyncSession = Depends(get_session)):
    word = await get_word(session=db, word_id=word_id)
    if not word:
        raise HTTPException(status_code=404, detail="Word not found with the given ID")
    return word


@router.put(
    "/update/{word_id}",
    summary="Update word",
    status_code=status.HTTP_200_OK,
    response_model=Word,
)
async def update_word_route(
    word_id: int, word: WordUpdate, db: AsyncSession = Depends(get_session)
) -> Word:
    return await update_word(session=db, word_id=word_id, word=word)


@router.delete(
    "/delete/{word_id}",
    summary="Delete word",
    status_code=status.HTTP_202_ACCEPTED,
)
async def delete_word_route(word_id: int, db: AsyncSession = Depends(get_session)) -> int:
    return await delete_word(session=db, word_id=word_id)


@router.get(
    "/find-synset/{flashcard_id}/{sentence_id}",
    summary="Get definition for words correlated with flashcard and sentences",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
async def find_synset_route(
    flashcard_id: int, sentence_id: int, db: AsyncSession = Depends(get_session)
) -> dict:
    return await find_synset(session=db, flashcard_id=flashcard_id, sentence_id=sentence_id)


@router.post(
    "/match-word-sentences/{word_id}",
    summary="Update relations between word and sentences",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def match_word_sentences_route(
    word_id: int,
    disconnect_ids: set[int],
    sentence_ids: set[int],
    db: AsyncSession = Depends(get_session),
) -> None:
    if disconnect_ids:
        await word_separate_sentences(db, word_id, disconnect_ids)
    return await word_join_to_sentences(db, word_id, sentence_ids)

@router.get(
    "/find-words/{flashcard_id}",
    summary="Get all word related to flashcard",
    status_code=status.HTTP_200_OK,
    response_model=list[Word],
)
async def find_words_for_flashcard_route(
    flashcard_id: int,
    db: AsyncSession = Depends(get_session)
) -> ScalarResult[Word]:
    return await find_words_for_flashcard(db, flashcard_id)
