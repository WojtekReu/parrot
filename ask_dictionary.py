#!/usr/bin/env python
import logging

import typer

import urllib3

from wing.config import settings
from wing.tools_external import translate

urllib3.disable_warnings()

logging.basicConfig(encoding='utf-8', level=settings.LOGGING_LEVEL)
logger = logging.getLogger(__name__)


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
            logger.info(f"{translation_tuple[0]} \t -> \t {translation_tuple[1]}")
    else:
        logger.info("Translation not found.")


if __name__ == "__main__":
    typer.run(main)
