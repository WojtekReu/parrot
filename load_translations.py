#!/usr/bin/env python
"""
Load translations from csv file to db. Usually file is from Google translator.
"""
import asyncio
from pathlib import Path

import typer

from wing.processing import load_translations_cmd
from wing.views import print_all_books


def main(
    book_id: int = typer.Option(
        default=None,
        help="assign words to book; create new book entry if no book-id",
    ),
    filename_path: Path = typer.Argument(
        ...,
        help="csv file with translations: pl; eng semicolon separated",
    )
):
    loop = asyncio.get_event_loop()
    if not book_id:
        loop.run_until_complete(print_all_books())
        book_id_input = input(f"Choose book number: ").strip()
        book_id = int(book_id_input)
    book = loop.run_until_complete(load_translations_cmd(book_id, filename_path))
    print(f"Loaded translations for '{book.title}'.")


if __name__ == "__main__":
    typer.run(main)
