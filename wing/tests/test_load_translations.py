import pytest

from sqlalchemy.ext.asyncio import AsyncSession

from wing.crud.book import create_book
from wing.crud.flashcard import get_flashcard_ids_for_book, get_flashcard
from wing.crud.sentence import get_sentence
from wing.crud.user import create_user
from wing.models.book import BookCreate
from wing.models.user import UserCreate
from wing.processing import load_translations_content, load_sentences, save_prepared_words

TRANSLATION_LIST = [
    ("pig", "świnia"),
    ("world", "świat"),
    ("end", "koniec"),
    ("he was considerably reassured", "był znacznie uspokojony"),
]

BOOK_RAW = """She had the face of an impertinent but jolly little pig, mottled red under 
a dusting of powder. He bored me considerably. When he had definitely decided that a certain 
light apart from the others higher up the hill was their light, he was considerably reassured. 
At the back of the house some one was rattling cans. sticking Norman arches on one’s pigsties. 
Girl who came out with the pigs and hens to receive them. We live with pigs in the drawing-room.
The dining-room at this moment had a certain fantastic resemblance to a farmyard scattered with 
grain on which bright pigeons kept descending. In spite of his certainty a slight redness came 
into his face as he spoke the last two words. When they had come to an end, or, to speak more 
accurately. Sprinkled with endearments. I have promised to lend her Gibbon."""


@pytest.mark.asyncio
async def test_load_translations(session: AsyncSession):
    book = await create_book(
        session,
        BookCreate(
            title="The Voyage Out",
            author="Virginia Woolf",
        ),
    )
    user = await create_user(
        session,
        UserCreate(
            username="gkowalska",
            password="secret-password",
            email="gkowalska@example.com",
        ),
    )
    pos_collections = await load_sentences(session, BOOK_RAW, book.id)
    assert "pig" in pos_collections[0]  # 0 is nouns
    assert "promise" in pos_collections[1]
    sentences = [
        await get_sentence(session, s_id) for s_id in pos_collections[0]["pig"]["sentence_ids"]
    ]
    for sentence in sentences:
        assert "pig" in sentence.sentence

    assert len(sentences) == 3
    assert "end" in pos_collections[0]  # 0 is nouns
    assert len(pos_collections[0]["end"]["sentence_ids"]) == 1

    for dest in pos_collections:
        await save_prepared_words(session, dest)

    await load_translations_content(session, TRANSLATION_LIST, book.id, user.id)
    flashcard_ids = await get_flashcard_ids_for_book(session, book.id, user.id)
    flashcards = [await get_flashcard(session, f_id) for f_id in flashcard_ids]
    result = sorted(flashcard.keyword for flashcard in flashcards)
    expected = ["end", "he was considerably reassured", "pig"]
    assert result == expected
