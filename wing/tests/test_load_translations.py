import pytest

from sqlalchemy.ext.asyncio import AsyncSession

from wing.processing import load_translations_content

TRANSLATION_LIST = [
    ("pig", "świnia"),
    ("world", "świat"),
    ("end", "koniec"),
]


@pytest.mark.asyncio
async def test_load_translations(session: AsyncSession):
    pos_collections = await load_translations_content(session, TRANSLATION_LIST)
    assert "pig" in pos_collections[0]  # 0 is nouns
    assert "world" in pos_collections[0]
    assert len(pos_collections[0]["pig"]["sentence_ids"]) == 6


@pytest.mark.asyncio
async def test_check_sentence_ids_for_word(session: AsyncSession):
    pos_collections = await load_translations_content(session, TRANSLATION_LIST)
    assert "end" in pos_collections[0]  # 0 is nouns
    assert len(pos_collections[0]["end"]["sentence_ids"]) == 1
