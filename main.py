from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from wing.web import all_books, get_book, get_translation, get_sentences

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


@app.get("/translations_by_book/{book_id}/{order_nr}")
async def read_translations_by_book(book_id: int, order_nr: int|None):
    if order_nr is None:
        order_nr = 1
    return await get_translation(book_id, order_nr)


@app.get("/fetch_sentences/{book_id}/{bword_id}")
async def fetch_sentences(book_id: int, bword_id: int):
    return await get_sentences(book_id, bword_id)

