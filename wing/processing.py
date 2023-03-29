from dataclasses import dataclass

from .models import Sentence, Word


@dataclass
class Flashcard:
    order: int
    text: str
    translations: list[str]


def flashcard_list(book_id: int) -> list:
    flashcards = [
        Flashcard(
            w_row[1],
            w_row[0].key_word,
            w_row[0].translations,
        )
        for w_row in Word.get_by_book(book_id)
    ] + [
        Flashcard(
            w_row[0].order,
            w_row[0].text,
            w_row[0].translations,
        )
        for w_row in Sentence.get_by_book(book_id)
    ]

    flashcards.sort(key=lambda f: f.order)

    return flashcards
