#!/usr/bin/env python
"""
Create relations between Word and Sentence in db and add Context for Word from book if it exists
in personal library.
"""
import asyncio

import typer

from wing.processing import connect_words_to_sentences


async def async_main() -> None:
    await connect_words_to_sentences()


def main():
    """
    Connect words to sentences
    """
    asyncio.run(async_main())


if __name__ == "__main__":
    typer.run(main)
