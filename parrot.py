#!/usr/bin/env python
from wing.models import Book
from wing.processing import flashcard_list

DEFAULT_BOOK_NR = 1
DEFAULT_LINE_NR = 0


def show_results(total, correct):
    print(f"\n========== Correct words: {correct}/{total} ==========\n")


def print_all_books():
    for book_row in Book.get_all():
        book = book_row[0]
        print(f"{book.id}. {book.title} - {book.author}")


def learn(book_id: int, start_line: int) -> tuple[int, int]:
    correct = 0
    total = 0

    for flashcard in flashcard_list(book_id)[start_line:]:
        try:
            your_response = input(f"{flashcard.text} - ").strip()
        except KeyboardInterrupt:
            return total, correct

        total += 1

        if your_response in flashcard.translations:
            print("OK")
            correct += 1
        else:
            spaces_nr = len(flashcard.text) + 3
            translations = "; ".join(flashcard.translations)
            print(" " * spaces_nr + translations)

    return total, correct


def main():
    print_all_books()
    book_id_input = input(f"Choose book number[{DEFAULT_BOOK_NR}]: ").strip()
    book_id = int(book_id_input) if book_id_input else DEFAULT_BOOK_NR
    start_line_input = input(f"Begin from line number[{DEFAULT_LINE_NR}]: ").strip()
    start_line = int(start_line_input) if start_line_input else DEFAULT_LINE_NR
    total, correct = learn(book_id, start_line)
    show_results(total, correct)


if __name__ == "__main__":
    main()
