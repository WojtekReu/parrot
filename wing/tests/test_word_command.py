import pytest
from ..processing import translate
from ..models.word import Word


@pytest.mark.skip(reason="mock is needed")
def test_word_post():
    word = Word(keyword="post")
    result = translate(word, False)
    expected = [("post", "słup")]

    assert expected == result
