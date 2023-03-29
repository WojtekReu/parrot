#!/usr/bin/env python
"""
Load translations from csv file to db
"""
import csv
import itertools
from pathlib import Path

import typer

from wing.models import Book, BookWord, Sentence, Word

BOOKS_PATH = Path("book_list.csv")


def find_book(filename: str) -> tuple[str, str] or None:
    """
    File book_list.csv contains 3 columns: book_dictionary.csv;title;author. Function returns
    tuple: title and author for given filename.
    """
    with open(BOOKS_PATH) as f:
        csv_data = csv.reader(f, delimiter=";")
        for row in csv_data:
            if row[0] == filename:
                return row[1], row[2]  # title, author


def get_book(title, author) -> int:
    book = Book(title=title, author=author)
    book.find_first()
    if not book.id:
        return book.save()

    return book.id


def load_file(filename_path):
    title, author = find_book(filename_path.parts[-1])
    book_id = get_book(title, author)
    order = itertools.count()

    with open(filename_path) as f:
        csv_data = csv.reader(f, delimiter=";")
        for row in csv_data:
            col1, col2 = row[0], row[1]
            if len(col1.strip().split()) == 1:
                word = Word(key_word=col1)
                word.find_first()
                if word.id:
                    if col2 not in word.translations:
                        word.translations.append(col2)
                        word.save()
                    book_word = BookWord(
                        book_id=book_id,
                        word_id=word.id,
                    )
                    book_word.find_first()
                    if not book_word.id:
                        book_word.order = next(order)
                        book_word.save()
                else:
                    word.translations = [col2]
                    book_word = BookWord(
                        book_id=book_id,
                        word_id=word.save(),
                    )
                    book_word.find_first()
                    if not book_word.id:
                        book_word.order = next(order)
                        book_word.save()

            else:
                sentence = Sentence(
                    book_id=book_id,
                    text=col1,
                )
                sentence.find_first()
                if not sentence.id:
                    sentence.order = next(order)
                    sentence.translations = [col2]
                    sentence.save()
                elif col2 not in sentence.translations:
                    sentence.translations.append(col2)
                    sentence.save()


def main(
    filename_path: Path = typer.Argument(
        ...,
        help="csv file with translations: pl; eng semicolon separated",
    )
):
    load_file(filename_path)


if __name__ == "__main__":
    typer.run(main)
