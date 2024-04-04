from .crud.book import find_books
from .db.session import get_session
from .models.book import BookFind


async def print_all_books() -> None:
    """
    Print id, title and author for all books.
    """
    async for session in get_session():
        for book in await find_books(session, BookFind()):
            print(f"{book.id}. {book.title} - {book.author}")

