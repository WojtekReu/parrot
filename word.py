#!/usr/bin/env python

import asyncio
import typer

from wing.models import Word
from wing.views import word_context, word_sentences


async def async_main(key_word: str):
    """
    Show word translation, sentence containing word and book context
    """
    word = Word(key_word=key_word)
    await word.match_first()
    translations = '; '.join(word.translations) if word.translations else '----'
    print(f"Word source: `{word.key_word}` -> {translations}")

    print(await word_sentences(word))
    output_word_context = await word_context(word)
    if output_word_context:
        print("---------------- context in books ----------------")
        print(output_word_context)


def main(key_word: str):
    """
    Run asynchronously
    """
    asyncio.run(async_main(key_word))


if __name__ == "__main__":
    typer.run(main)
