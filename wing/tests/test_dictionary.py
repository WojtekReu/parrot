import pytest
from unittest.mock import patch, Mock

from wing.dictionary import find_translations


@pytest.mark.asyncio
@patch("wing.dictionary.dictionary_client")
async def test_find_translations(dictionary_client):
    def define(*args, **kwargs):
        return Mock(
            content=[
                {
                    "word": args[0],
                    "definition": "equivocal /ɪˈkwɪvəkəl/ <Adj>\n  dwuznaczny, niejednoznaczny",
                }
            ]
        )

    dictionary_client.define = define

    result = await find_translations("equivocal")
    assert result == "equivocal /ɪˈkwɪvəkəl/ <Adj>\n  dwuznaczny, niejednoznaczny"


@pytest.mark.asyncio
@patch("wing.dictionary.dictionary_client")
async def test_translations_not_found(dictionary_client):
    def define(*args, **kwargs):
        return Mock(content=None)

    dictionary_client.define = define

    result = await find_translations("nonexisting")
    assert result is None
