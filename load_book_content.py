#!/usr/bin/env python
import asyncio
from pathlib import Path

import typer

from wing.processing import load_book_content_cmd
from wing.views import print_all_books


def main(
    book_id: int = typer.Option(
        default=None,
        help="ID of loaded book",
    ),
    filename_path: Path = typer.Argument(
        ...,
        help="Path to book content in raw text format",
    )
):
    """
    Load book content to database
    """
    loop = asyncio.get_event_loop()
    if not book_id:
        loop.run_until_complete(print_all_books())
        book_id_input = input(f"Choose book number: ").strip()
        book_id = int(book_id_input)
    book = loop.run_until_complete(load_book_content_cmd(filename_path, book_id))
    print(f"Loaded whole book '{book.title}': {book.sentences_count} sentences.")


if __name__ == "__main__":
    typer.run(main)
