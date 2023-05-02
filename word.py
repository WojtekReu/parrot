#!/usr/bin/env python
"""
Show word context and translations from configured API
"""
import typer

from wing.processing import find_word_in_context, save_translations, translate


def main(word: str):
    word, context = find_word_in_context(word)
    print(f"Word source: {word.key_word}")
    for row in context:
        print(row)

    translations = translate(word)
    if translations:
        save_translations(word, translations)
        for translation in word.translations:
            print(translation)


if __name__ == "__main__":
    typer.run(main)
