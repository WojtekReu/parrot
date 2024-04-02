#!/usr/bin/env python

import typer

import urllib3

from wing.config import settings
from wing.tools_external import translate

urllib3.disable_warnings()


def main(word: str, debug: bool = False):
    """
    Show word translations from configured API
    """
    headers = {
        "X-Secret": settings.PONS_SECRET_KEY,
    }
    lang = "enpl"
    api_url = f"{settings.API_URL}?l={lang}&q={word}"
    translations = translate(api_url, headers, debug)
    if translations:
        for translation_tuple in translations:
            print(f"{translation_tuple[0]} \t -> \t {translation_tuple[1]}")
    else:
        print("Translation not found.")


if __name__ == "__main__":
    typer.run(main)
