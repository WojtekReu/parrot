from fastapi import APIRouter, status
from wing.dictionary import find_translations

router = APIRouter(
    prefix="/dictionary",
    tags=["dictionary"],
)


@router.get(
    "/find/{word_str}",
    summary="Find word in dictionary",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, str],
)
async def find_translations_route(word_str: str) -> dict[str]:
    return {
        "word": word_str,
        "translation": (await find_translations(word=word_str)) or "",
    }
