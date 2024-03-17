import nltk
import pytest

from wing.processing import lemmatize, match_word_definitions

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.skip(reason="It's not finished yet.")
def test_load_needless():
    """
    Problem is that words `needless` and `needle` have the same lemma - `needle`.
    """
    input_word = "needless"
    translation = "nieproduktywny"

    lemmatizer = nltk.WordNetLemmatizer()
    actual = lemmatize(lemmatizer, input_word)

    # lemmatizer.lemmatize('needless', pos='n')  # needle
    # lemmatizer.lemmatize('needless', pos='v')  # needle
    # lemmatizer.lemmatize('needless', pos='s')  # needless
    # lemmatizer.lemmatize('needlessly', pos='r')  # needless

    # I expect `needless` has lemma `needless`

    assert actual == input_word


@pytest.mark.asyncio
async def test_match_word_definition():
    """
    Test matching word definition
    """
    input_word = "needless"
    sentence = "O cruel, needless misunderstanding!"

    definitions = await match_word_definitions(input_word, sentence)

    assert definitions == ["gratuitous.s.03: unnecessary and unwarranted"]
