#!/usr/bin/env python

import asyncio
import typer

from wing.processing import find_word
from wing.views import show_matched_for_translation, show_not_matched_for_translation


async def async_main(key_word: str):
    """
    Show word translation, sentence containing word and book context
    """
    bword = await find_word(key_word)
    print(f"lem: {bword.lem}")
    if bword.declination:
        print(f"declinations: {', '.join(bword.declination)}")

    print_result = False

    async for translation in bword.get_translations():
        print_result = await show_matched_for_translation(translation)

    if not print_result and bword.id:
        await show_not_matched_for_translation(bword)


def main(key_word: str):
    """
    Show the occurrence a word in books.
    """
    asyncio.run(async_main(key_word))


if __name__ == "__main__":
    typer.run(main)
