#!/usr/bin/env python
"""
Run script to learn english words.
"""
import asyncio
import typer

from wing.messages import show_end_up_result
from wing.processing import learn
from wing.structure import DEFAULT_BOOK_NR, DEFAULT_LINE_NR
from wing.views import print_all_books


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(print_all_books())
    book_id_input = input(f"Choose book number[{DEFAULT_BOOK_NR}]: ").strip()
    book_id = int(book_id_input) if book_id_input else DEFAULT_BOOK_NR
    start_line_input = input(f"Begin from line number[{DEFAULT_LINE_NR}]: ").strip()
    start_line = int(start_line_input) if start_line_input else DEFAULT_LINE_NR
    total, correct = loop.run_until_complete(learn(book_id, start_line))
    show_end_up_result(total, correct)


if __name__ == "__main__":
    typer.run(main)
