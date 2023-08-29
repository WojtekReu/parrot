#!/usr/bin/env python
import asyncio
import csv
from pathlib import Path
import typer

from wing.models import Book


async def async_main():
    """
    Import book title and authors from csv. Omit the first column in the file, it is filename with
    translations.
    """
    bl_path = Path("data/book_list.csv")

    with open(bl_path) as f:
        for row in csv.reader(f, delimiter='\t'):
            book = Book(
                title=row[1],
                author=row[2],
            )
            await book.save()
            print(book)


def main():
    """
    Import book title and authors from data/book_list.csv
    """
    asyncio.run(async_main())


if __name__ == "__main__":
    typer.run(main)
