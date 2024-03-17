import pytest
from ..processing import translate
from ..models import Bword


@pytest.mark.skip(reason="It's not finished yet.")
def test_word_post():
    word = Bword(keyword="post")
    result = translate(word, False)
    expected = [("post", "słup")]

    assert expected == result
