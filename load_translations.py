#!/usr/bin/env python
"""
Load translations from csv file to db. Usually file is from Google translator.
"""
from pathlib import Path

import typer

from wing.processing import load_translations


def main(
    book_id: int,
    filename_path: Path = typer.Argument(
        ...,
        help="csv file with translations: pl; eng semicolon separated",
    )
):
    load_translations(book_id, filename_path)


if __name__ == "__main__":
    typer.run(main)
