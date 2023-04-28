import re
import pytest

from ..processing import get_pattern


def test_find_word_in_content():
    """
    find all my examples
    """
    word = 'operation'
    contents = {
        "couldn't have? This operation is best. Go a head.": " This operation is best.",
        "My x. What about this operation a? Not now.": " What about this operation a?",
        "Ok. This is my last operation a": " This is my last operation a",
        '"Status operation" No way.': 'Status operation',
    }
    pattern = get_pattern(word)
    for source, dest in contents.items():
        res = re.findall(pattern, source, re.IGNORECASE)
        final_res = res[0] if res else ''
        assert dest == final_res
