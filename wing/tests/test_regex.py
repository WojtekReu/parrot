import re
import pytest

from ..processing import get_pattern


def test_find_word_in_content():
    """
    find all my examples
    """
    word = 'operation'
    contents = {
        # pattern: result,
        "couldn't have? This operation is best. Go a head.": [(' This operation is best.', '')],
        "My x. What about this operation a? Not now.": [(' What about this operation a?', '')],
        "Ok. This is my last operation a": [(' This is my last operation a', '')],
        '"Status operation" No way.': [('Status operation', '')],
        "Mark! Operation started. Now!": [(' Operation started.', '')],
        "Operation.": [('', 'Operation.')],
    }
    pattern = get_pattern(word)
    for source, expected in contents.items():
        result = re.findall(pattern, source, re.IGNORECASE)
        assert result == expected


def test_check_similar_pattern():
    """
    Avoid similar words.
    """
    word = "devour"
    content = " whose expression of devout attention seemed to prove."
    pattern = get_pattern(word)
    result = re.findall(pattern, content, re.IGNORECASE)
    assert result == []


def test_part_of_word():
    """
    Avoid similar words.
    """
    word = "hem"
    content = "Give them this."
    pattern = get_pattern(word)
    result = re.findall(pattern, content, re.IGNORECASE)
    assert result == []
