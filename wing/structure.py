from dataclasses import dataclass
from typing import Optional

TYPE_WORD = 'W'
TYPE_SENTENCE = 'S'

DEFAULT_BOOK_NR = 1
DEFAULT_LINE_NR = 0

SENTENCES_LIMIT = 10
DETERMINERS = "the", "a"
PRONOUNS = "i", "we", "you", "they", "he", "she", "it"


@dataclass
class Flashcard:
    order: int
    text: str
    translations: list[str]
    type: str
    word_id: Optional[int]


@dataclass
class BookContent:
    sentence: str
    stems: tuple


def tag_to_pos(tag):
    """
    Change tag ex. 'VBD' to pos ex. 'v'
    """
    match tag:
        case "NN":
            pos = "n"
        case "VB" | "VBD" | "VBG" | "VBN" | "VBP" | "VBZ":
            pos = "v"
        case "JJ" | "JJT":
            pos = "a"
        case "RB":
            pos = "r"
        case _:
            pos = None
    return pos
