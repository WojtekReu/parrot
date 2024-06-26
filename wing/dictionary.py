from dictionary_client import DictionaryClient

from wing.structure import DEFINITION_KEY, DICTIONARY

dictionary_client = DictionaryClient()


async def find_translations(word: str) -> str | None:
    response = dictionary_client.define(word, db=DICTIONARY)
    if response.content:
        return response.content[0][DEFINITION_KEY]
