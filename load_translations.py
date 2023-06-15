#!/usr/bin/env python
"""
Load translations from csv file to db. Usually file is from Google translator.
"""
from pathlib import Path

import typer

from wing.processing import load_translations_cmd


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
    load_translations_cmd(book_id, filename_path)


if __name__ == "__main__":
    typer.run(main)
