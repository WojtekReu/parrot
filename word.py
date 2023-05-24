#!/usr/bin/env python

import typer

from wing.models import Sentence, Word
from wing.processing import save_translations, translate
from wing.views import word_context, word_sentences


def main(key_word: str):
    """
    Show word translation, sentence containing word and book context
    """
    word = Word(key_word=key_word)
    word.match_first()
    translations = '; '.join(word.translations) if word.translations else '----'
    print(f"Word source: `{word.key_word}` -> {translations}")

    print(word_sentences(word))
    output_word_context = word_context(word)
    if output_word_context:
        print("---------------- context in books ----------------")
        print(output_word_context)


if __name__ == "__main__":
    typer.run(main)
