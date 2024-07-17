from dictionary_client import DictionaryClient

from wing.config import settings


async def find_translations(word: str) -> str | None:
    dictionary_client = DictionaryClient(
        host=settings.DICTIONARY_HOST,
        port=settings.DICTIONARY_PORT,
    )
    response = dictionary_client.define(word, db=settings.DICTIONARY_VOCABULARY)
    if response.content:
        return response.content[0][settings.DICTIONARY_DEFINITION_KEY]
