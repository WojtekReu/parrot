#!/usr/bin/env python
import asyncio

import typer

from wing.processing import load_book_content_cmd, print_all_books


def main(book_path: str):
    """
    Load book content to database
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(print_all_books())
    book_id_input = input(f"Choose book number: ").strip()
    book_id = int(book_id_input)
    book = loop.run_until_complete(load_book_content_cmd(book_path, book_id))
    print(f"Loaded whole book '{book.title}': {book.sentences_count} sentences.")


if __name__ == "__main__":
    typer.run(main)
