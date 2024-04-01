import pytest

from sqlalchemy.ext.asyncio import AsyncSession

from wing.processing import load_translations_content

TRANSLATION_LIST = [
    ("pig", "świnia"),
    ("world", "świat"),
]


@pytest.mark.asyncio
async def test_load_translations(session: AsyncSession):
    pos_collections = await load_translations_content(session, TRANSLATION_LIST)
    assert "pig" in pos_collections[0]  # 0 is nouns
    assert "world" in pos_collections[0]
    assert len(pos_collections[0]["pig"]["sentence_ids"]) == 9
