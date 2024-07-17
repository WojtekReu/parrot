import pytest
from unittest.mock import patch

from wing.dictionary import find_translations

from conftest import DictionaryClientMock


@pytest.mark.asyncio
@patch("wing.dictionary.DictionaryClient", new=DictionaryClientMock)
async def test_find_translations():
    result = await find_translations("equivocal")
    assert result == "equivocal /ɪˈkwɪvəkəl/ <Adj>\n  dwuznaczny, niejednoznaczny"


@pytest.mark.asyncio
@patch("wing.dictionary.DictionaryClient", new=DictionaryClientMock)
async def test_translations_not_found():
    result = await find_translations("nonexisting")
    assert result is None
