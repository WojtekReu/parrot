from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from fastapi_pagination import Page
from sqlalchemy import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from wing.auth.jwthandler import get_current_user
from wing.crud.book import (
    create_book,
    delete_book,
    find_books,
    get_book,
    get_currently_reading,
    set_currently_reading,
    unset_currently_reading,
    update_book,
)
from wing.crud.flashcard import get_flashcard_ids_for_book
from wing.crud.sentence import get_sentences_for_flashcard, count_sentences_for_book
from wing.crud.word import count_words_for_book
from wing.db.session import get_session
from wing.models.book import Book, BookCreate, BookFind, BookUpdate
from wing.models.sentence import Sentence
from wing.models.user import UserPublic
from wing.processing import load_sentences, save_prepared_words

router = APIRouter(
    prefix="/books",
    tags=["books"],
)


@router.post(
    "/",
    summary="Create a new book.",
    status_code=status.HTTP_201_CREATED,
    response_model=Book,
    dependencies=[Depends(get_current_user)],
)
async def create_book_route(
    data: BookCreate,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Book:
    return await create_book(session=db, book=data, user_id=current_user.id)


@router.post(
    "/upload/{book_id}",
    summary="Upload book content.",
    status_code=status.HTTP_200_OK,
    response_model=Book,
    dependencies=[Depends(get_current_user)],
)
async def create_upload_file(
    book_id: int,
    file: UploadFile,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    book = await get_book(db, book_id, current_user.id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found with the given ID"
        )
    data = (await file.read()).decode()

    pos_collections = await load_sentences(db, data, book_id)

    for dest in pos_collections:
        await save_prepared_words(db, dest)

    book.sentences_count = await count_sentences_for_book(db, book.id)
    book.words_count = await count_words_for_book(db, book.id)
    await update_book(db, book.id, current_user.id, BookUpdate(**book.dict()))

    return book


@router.get(
    "/public",
    summary="Get public books.",
    status_code=status.HTTP_200_OK,
    response_model=Page[Book],
)
async def get_books_route(db: AsyncSession = Depends(get_session)) -> Page[Book]:
    return await find_books(session=db, book=BookFind(is_public=True))


@router.get(
    "/reading",
    summary="Get all user reading books.",
    status_code=status.HTTP_200_OK,
    response_model=list[int],
    dependencies=[Depends(get_current_user)],
)
async def get_currently_reading_route(
    current_user: UserPublic = Depends(get_current_user), db: AsyncSession = Depends(get_session)
) -> ScalarResult[int]:
    response = await get_currently_reading(session=db, user_id=current_user.id)
    return response


@router.post(
    "/reading",
    summary="Set or unset currently reading book.",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_user)],
)
async def set_currently_reading_route(
    data: dict[int, bool],
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> None:
    for book_id, is_currently_reading in data.items():
        if is_currently_reading:
            book = await get_book(db, book_id)
            if book.user_id == current_user.id or book.is_public:
                await set_currently_reading(db, current_user.id, book_id)
        else:
            await unset_currently_reading(db, current_user.id, book_id)


@router.get(
    "/{book_id}",
    summary="Get a book.",
    status_code=status.HTTP_200_OK,
    response_model=Book,
    dependencies=[Depends(get_current_user)],
)
async def get_book_route(
    book_id: int,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Book:
    book = await get_book(session=db, book_id=book_id, user_id=current_user.id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found with the given ID"
        )
    return book


@router.delete(
    "/{book_id}/delete",
    summary="Delete book",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(get_current_user)],
)
async def delete_book_route(
    book_id: int,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> int:
    return await delete_book(session=db, book_id=book_id, user_id=current_user.id)


@router.get(
    "/{book_id}/flashcards",
    summary="Get all flashcard ids for book",
    status_code=status.HTTP_200_OK,
    response_model=list[int],
    dependencies=[Depends(get_current_user)],
)
async def get_flashcard_ids_for_book_route(
    book_id: int,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    return await get_flashcard_ids_for_book(session=db, book_id=book_id, user_id=current_user.id)


@router.get(
    "/{book_id}/flashcards/{flashcard_id}/sentences",
    summary="Get sentences for book and flashcard.",
    status_code=status.HTTP_200_OK,
    response_model=list[Sentence],
    dependencies=[Depends(get_current_user)],
)
async def get_sentences_for_flashcard_route(
    book_id: int,
    flashcard_id: int,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    return await get_sentences_for_flashcard(
        session=db,
        book_id=book_id,
        flashcard_id=flashcard_id,
        user_id=current_user.id,
    )


@router.put(
    "/{book_id}/update",
    summary="Update book",
    status_code=status.HTTP_200_OK,
    response_model=Book,
    dependencies=[Depends(get_current_user)],
)
async def update_book_route(
    book_id: int,
    book: BookUpdate,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Book:
    return await update_book(session=db, book_id=book_id, user_id=current_user.id, book=book)
