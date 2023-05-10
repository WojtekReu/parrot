#!/usr/bin/env python
"""
Show word context and translations from configured API
"""
import typer

from wing.processing import find_word_in_context, save_translations, translate


def main(word: str, debug: bool = False):
    word, context = find_word_in_context(word)
    print(f"Word source: {word.key_word}")
    for row in context:
        print(row)

    translations = translate(word, debug)
    if translations and word.id:
        save_translations(word, translations)
        for translation_tuple in translations:
            print(f"{translation_tuple[0]} \t -> \t {translation_tuple[1]}")


if __name__ == "__main__":
    typer.run(main)
