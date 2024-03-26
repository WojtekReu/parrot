from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from wing.web import (
    all_books,
    get_book,
    get_sentences,
    get_all_flashcards,
    get_flashcard,
    get_sentence,
    get_word,
    get_sentences_by_book,
)

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/books")
async def read_root():
    return await all_books()


@app.get("/book/{book_id}")
async def read_book(book_id: int):
    return await get_book(book_id)


@app.get("/flashcards/{book_id}")
async def fetch_flashcards(book_id: int):
    return await get_all_flashcards(book_id)


@app.get("/flashcard/{flashcard_id}")
async def fetch_flashcard(flashcard_id: int):
    return await get_flashcard(flashcard_id)


@app.get("/sentences/{word_id}")
async def fetch_sentences(word_id: int):
    """
    Results are aggregated by books, and sentences are stored in 'sentences_list' attribute.
    """
    return await get_sentences(word_id)

@app.get("/sentences/book/{book_id}/{flashcard_id}")
async def fetch_sentences_by_book(book_id: int, flashcard_id: int):
    """
    Get all sentences for given book and flashcard
    """
    return await get_sentences_by_book(book_id, flashcard_id)

@app.get("/sentence/{sentence_id}")
async def fetch_sentence(sentence_id: int):
    return await get_sentence(sentence_id)


@app.get("/word/{word_id}")
async def fetch_word(word_id: int):
    return await get_word(word_id)
