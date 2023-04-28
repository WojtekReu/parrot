#!/usr/bin/env python
"""
Run script to learn english words.
"""
import typer

from wing.processing import learn, print_all_books, show_end_up_result
from wing.structure import DEFAULT_BOOK_NR, DEFAULT_LINE_NR


def main():
    print_all_books()
    book_id_input = input(f"Choose book number[{DEFAULT_BOOK_NR}]: ").strip()
    book_id = int(book_id_input) if book_id_input else DEFAULT_BOOK_NR
    start_line_input = input(f"Begin from line number[{DEFAULT_LINE_NR}]: ").strip()
    start_line = int(start_line_input) if start_line_input else DEFAULT_LINE_NR
    total, correct = learn(book_id, start_line)
    show_end_up_result(total, correct)


if __name__ == "__main__":
    typer.run(main)
