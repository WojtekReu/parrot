import itertools
from typing import Any

from .models import Book, Bword, Translation


async def print_all_books() -> None:
    """
    Print id, title and author for all books.
    """
    async for book in Book.all():
        print(f"{book.id}. {book.title} - {book.author}")


def show_correct_translation(flashcard: Any) -> None:
    spaces_nr = len(flashcard.text) + 3
    print(" " * spaces_nr + flashcard.translation)


async def show_matched_for_translation(translation: Translation) -> bool:
    """
    Show results assigned book contents and sentences for translation
    """
    print(f"EN: {translation.source},\t PL: {translation.text}")
    print_result = False
    nr = itertools.count(1)
    print("-------------------- Book Contents ---------------------")
    async for bc in translation.get_book_contents():
        print_result = True
        print(f"{bc.book_id}, {next(nr)}: {bc.sentence}")
    print("---------------------- Sentences -----------------------")

    async for sentence in translation.get_sentences():
        print_result = True
        print(f"{sentence.book_id}, {next(nr)}: {sentence.text}")
        print(f"\t\t {sentence.translation}")
    return print_result


async def show_not_matched_for_translation(bword: Bword) -> None:
    print("----------- Automatically found sentences ----------")
    nr = itertools.count(1)
    async for bc in bword.get_book_contents():
        # book_id, nr, book_content.sentence
        print(f"{bc.book_id}, {next(nr)}: {bc.sentence}")
