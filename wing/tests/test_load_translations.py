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
    result = {
        "pig": {
            "count": 1,
            "declination": {},
            "flashcard_ids": {3},
            "lem": "pig",
            "pos": "n",
            "sentence_ids": {5, 6, 7, 44, 46, 47, 19, 21, 22},
        },
        "world": {
            "count": 1,
            "declination": {},
            "flashcard_ids": {4},
            "lem": "world",
            "pos": "n",
            "sentence_ids": set(),
        },
    }
    assert pos_collections[0] == result  # 0 is nouns
