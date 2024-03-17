from wing.models import Book, Bword, Translation


async def all_books() -> dict[int, Book]:
    """
    Get all books
    """
    return {book.id: book async for book in Book.all()}


async def get_book(book_id) -> dict[str, ...]:
    """
    Get book by id
    """
    book = Book(id=book_id)
    await book.match_first()
    return {
        k: v for k, v in book.__dict__.items() if k in ("id", "title", "author", "sentences_count")
    }


async def get_translation(book_id, order):
    """
    Get translation by book_id and its order. Empty result is possible.
    """
    return await Translation.get(book_id, order)


async def get_sentences(book_id, bword_id):
    """
    For the book get sentences where word by bword_id occurred
    """
    sentences = []
    async for sentence in Bword(id=bword_id).get_book_contents(book_id):
        sentences.append(sentence)
    return {"sentences": sentences}