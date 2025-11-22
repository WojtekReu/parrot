#!/usr/bin/env python
import asyncio
import csv
import logging
from pathlib import Path
import typer

from wing.crud.book import create_book
from wing.crud.user import create_user, get_user_by_email
from wing.db.session import get_session
from wing.models import *

logging.basicConfig(encoding='utf-8', level=logging.INFO)
logger = logging.getLogger(__name__)


async def async_main():
    """
    Import book title and authors from csv. Omit the first column in the file, it is filename with
    translations.
    """
    async for session in get_session():
        db_user = await get_user_by_email(session, "jkowalski@example.com")
        if not db_user:
            await create_user(session, user.UserCreate(
                username="jkowalski",
                password="password",
                email="jkowalski@example.com",
            ))

        bl_path = Path("data/book_list.csv")

        with open(bl_path) as f:
            for row in csv.reader(f, delimiter='\t'):
                db_book = await create_book(session, book.BookCreate(
                    title = row[1],
                    author = row[2],
                ), db_user.id)
                logger.info(f"Created book '{db_book.title}'")


def main():
    """
    Import book title and authors from data/book_list.csv
    """
    asyncio.run(async_main())


if __name__ == "__main__":
    typer.run(main)
