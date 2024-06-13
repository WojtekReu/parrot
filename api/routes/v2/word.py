from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from wing.crud.word import (
    create_word,
    delete_word,
    find_words,
    find_synset,
    get_word,
    get_word_sentences,
    update_word,
    word_join_to_sentences,
    word_separate_sentences,
)
from wing.db.session import get_session
from wing.models.sentence import Sentence
from wing.models.word import Word, WordCreate, WordUpdate, WordFind

router = APIRouter(
    prefix="/words",
    tags=["words"],
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
    "/{word_id}/update",
    summary="Update word",
    status_code=status.HTTP_200_OK,
    response_model=Word,
)
async def update_word_route(
    word_id: int, word: WordUpdate, db: AsyncSession = Depends(get_session)
) -> Word:
    return await update_word(session=db, word_id=word_id, word=word)


@router.delete(
    "/{word_id}/delete",
    summary="Delete word",
    status_code=status.HTTP_202_ACCEPTED,
)
async def delete_word_route(word_id: int, db: AsyncSession = Depends(get_session)) -> int:
    return await delete_word(session=db, word_id=word_id)


@router.get(
    "/find/{word_str}",
    summary="Find word by lem or declination",
    status_code=status.HTTP_200_OK,
    response_model=list[Word],
)
async def find_word_route(
    word_str: str, db: AsyncSession = Depends(get_session)
) -> ScalarResult[Word]:
    return await find_words(session=db, word=WordFind(lem=word_str))


@router.get(
    "/{word_id}/sentences/{sentence_id}/synset",
    summary="Get synsets and definitions for word, the one word can be selected",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
async def find_synset_route(
    word_id: int, sentence_id: int, db: AsyncSession = Depends(get_session)
) -> dict:
    return await find_synset(session=db, word_id=word_id, sentence_id=sentence_id)


@router.get(
    "/{word_id}/sentences",
    summary="Get sentences related to word",
    status_code=status.HTTP_200_OK,
    response_model=list[Sentence],
)
async def get_word_sentences_route(
    word_id: int, db: AsyncSession = Depends(get_session)
) -> ScalarResult[Sentence]:
    return await get_word_sentences(session=db, word_id=word_id)


@router.post(
    "/{word_id}/sentences",
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
