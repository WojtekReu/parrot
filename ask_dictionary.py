#!/usr/bin/env python

import typer

from wing.models import Word
from wing.processing import save_translations, translate


def main(key_word: str, debug: bool = False):
    """
    Show word translations from configured API
    """
    word = Word(key_word=key_word)

    translations = translate(word, debug)
    if translations:
        if word.id:
            save_translations(word, translations)
            print(f"{word.key_word} (id: {word.id}) <- SAVED")
        for translation_tuple in translations:
            print(f"{translation_tuple[0]} \t -> \t {translation_tuple[1]}")
    else:
        print("Translation not found.")


if __name__ == "__main__":
    typer.run(main)
