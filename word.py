#!/usr/bin/env python

import asyncio
import typer

from wing.matching import match_book_contents
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

    translations = []
    async for translation in bword.get_translations():
        translations.append(translation)
        await show_matched_for_translation(translation)

    book_content_list = []  # this declaration is not necessary
    print_not_matched = True
    for translation in translations:
        if not translation.book_contents:
            if print_not_matched:
                book_content_list = await show_not_matched_for_translation(bword)
                print_not_matched = False
            list_str = input(
                f"Match sentences for `{translation.source}` -> `{translation.text}`: "
            )
            await match_book_contents(translation, book_content_list, list_str)
            await show_matched_for_translation(translation)


def main(key_word: str):
    """
    Show the occurrence a word in books.
    """
    asyncio.run(async_main(key_word))


if __name__ == "__main__":
    typer.run(main)
