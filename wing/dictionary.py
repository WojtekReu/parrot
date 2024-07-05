from dictionary_client import DictionaryClient

from wing.structure import (
    DICTIONARY_DEFINITION_KEY,
    DICTIONARY_HOST,
    DICTIONARY_PORT,
    DICTIONARY_VOCABULARY,
)


async def find_translations(word: str) -> str | None:
    dictionary_client = DictionaryClient(
        host=DICTIONARY_HOST,
        port=DICTIONARY_PORT,
    )
    response = dictionary_client.define(word, db=DICTIONARY_VOCABULARY)
    if response.content:
        return response.content[0][DICTIONARY_DEFINITION_KEY]
