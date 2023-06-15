from dataclasses import dataclass
from typing import Optional, Any
from wing.alchemy import ADVERBS_FILE, PREPOSITIONS_FILE, PRONOUNS_FILE

TYPE_WORD = 'W'
TYPE_SENTENCE = 'S'

DEFAULT_BOOK_NR = 1
DEFAULT_LINE_NR = 0

SENTENCES_LIMIT = 10
DETERMINERS = "the", "a", "an"

MIN_LEM_WORD = 3
MAX_STEM_OCCURRENCE = 100

with open(ADVERBS_FILE) as f:
    ADVERBS = (adverbs for adverbs in f.read().split())

with open(PRONOUNS_FILE) as f:
    PRONOUNS = (pronoun for pronoun in f.read().split())

with open(PREPOSITIONS_FILE) as f:
    PREPOSITIONS = (preposition for preposition in f.read().split())


@dataclass
class Flashcard:
    order: int
    text: str
    translation: str
    type: str
    translation_obj: Optional[Any]


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
