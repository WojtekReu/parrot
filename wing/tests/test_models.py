import pytest

from wing.models import BookContent


pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_find_sentences_with_the_word_in_the_book():
    """
    Test get_sentences class method
    """
    input_word = "needless"
    book_id = 23

    sentences = []
    async for book_content in BookContent.get_sentences(input_word, book_id):
        sentences.append(book_content.sentence)

    assert sentences == ["O cruel, needless misunderstanding!"]
