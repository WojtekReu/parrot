from pathlib import Path
from wing.config import settings

TYPE_WORD = "W"
TYPE_SENTENCE = "S"

DEFAULT_BOOK_NR = 1
DEFAULT_LINE_NR = 0

SENTENCES_LIMIT = 10
DETERMINERS = "the", "a", "an"


PRONOUNS_FILE = Path(settings.NLTK_DATA_PREFIX).joinpath("corpora", "dolch", "pronouns")
with open(PRONOUNS_FILE) as f:
    PRONOUNS = (pronoun for pronoun in f.read().split())

MIN_LEM_WORD = 3
MAX_STEM_OCCURRENCE = 100

# setting dictionary English to Polish, unix command: dict -D
DICTIONARY_HOST = "parrot-dict-1"
DICTIONARY_PORT = 2628
DICTIONARY_VOCABULARY = "fd-eng-pol"
DICTIONARY_DEFINITION_KEY = "definition"

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
