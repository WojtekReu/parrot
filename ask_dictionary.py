#!/usr/bin/env python

import typer

from wing.processing import translate


def main(word: str, debug: bool = False):
    """
    Show word translations from configured API
    """
    translations = translate(word, debug)
    if translations:
        for translation_tuple in translations:
            print(f"{translation_tuple[0]} \t -> \t {translation_tuple[1]}")
    else:
        print("Translation not found.")


if __name__ == "__main__":
    typer.run(main)
