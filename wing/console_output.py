from .crud.book import find_books_no_pagination
from .db.session import get_session
from .models.book import BookFind


async def print_all_books() -> None:
    """
    Print id, title and author for all books.
    """
    async for session in get_session():
        for book in await find_books_no_pagination(session, BookFind()):
            print(f"{book.id}. {book.title} - {book.author}")
