#!/usr/bin/env python
import asyncio

import typer

from wing.processing import load_book_content, print_all_books


def main(book_path: str):
    """
    Load book content to database
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(print_all_books())
    book_id_input = input(f"Choose book number: ").strip()
    book_id = int(book_id_input)
    loop.run_until_complete(load_book_content(book_path, book_id))


if __name__ == "__main__":
    typer.run(main)
