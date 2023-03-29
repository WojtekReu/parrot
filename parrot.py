#!/usr/bin/env python
from wing.models import Book
from wing.processing import flashcard_list


def show_results(total, correct):
    print(f"\n========== Correct words: {correct}/{total} ==========\n")


def print_all_books():
    for book_row in Book.get_all():
        book = book_row[0]
        print(f"{book.id}. {book.title} - {book.author}")


def learn(book_id) -> tuple[int, int]:
    correct = 0
    total = 0

    for flashcard in flashcard_list(book_id):
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
    book_id = int(input("Choose book number: ").strip())
    total, correct = learn(book_id)
    show_results(total, correct)


if __name__ == "__main__":
    main()
