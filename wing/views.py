import itertools
from typing import Any

from .models.book import Book
from .models.word import Word
from .models.flashcard import Flashcard


async def print_all_books() -> None:
    """
    Print id, title and author for all books.
    """
    async for book in Book.all():
        print(f"{book.id}. {book.title} - {book.author}")


def show_correct_translation(flashcard: Any) -> None:
    spaces_nr = len(flashcard.text) + 3
    print(" " * spaces_nr + flashcard.translation)


async def show_matched_for_translation(translation: Flashcard):
    """
    Show results assigned book contents and sentences for translation
    """
    print(f"EN: {translation.key_word},\t PL: {translation.translations}")
    nr = itertools.count(1)
    print("-------------------- Book Contents ---------------------")
    async for bc in translation.get_book_contents():
        print(f"{bc.book_id}, {next(nr)}: {bc.sentence}")
    print("---------------------- Sentences -----------------------")

    async for sentence in translation.get_sentences():
        print(f"{sentence.book_id}, {next(nr)}: {sentence.text}")
        print(f"\t\t {sentence.translation}")


async def show_not_matched_for_translation(word: Word) -> list[tuple[int, Any]]:
    """
    Show and return enumerated list of book_contents.
    """
    print("------------------------ others ------------------------")
    nr = itertools.count(1)
    book_content_list = []
    async for bc in word.get_book_contents():
        nr_current = next(nr)
        book_content_list.append((nr_current, bc))
        print(f"{bc.book_id}, {nr_current}: {bc.sentence}")
    return book_content_list
