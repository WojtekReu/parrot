#!/usr/bin/env python
import asyncio

import typer

from wing.processing import connect_words_to_sentences


async def async_main() -> None:
    """
    Asynchronously run cmd
    """
    await connect_words_to_sentences()


def main():
    """
    Connect words to sentences
    """
    print("connect_words.py: For all sentences link translated words\nprocessing...")
    asyncio.run(async_main())
    print("Connecting words to sentences done.")


if __name__ == "__main__":
    typer.run(main)
