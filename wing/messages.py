"""
Simple console messages
"""


def loading_message(book_id: int, title: str) -> None:
    print(f"Loading translations for Book({book_id}) `{title}`")


def book_not_found_message(book_id: int) -> None:
    print(f"Book not found for book_id = {book_id}")


def book_created_message(book_id: int, title: str) -> None:
    print(f"Book({book_id}) created: `{title}`")


def show_end_up_result(total, correct):
    """
    Show end up result
    """
    print(f"\n========== Correct words: {correct}/{total} ==========\n")
