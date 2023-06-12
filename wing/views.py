import itertools
from collections import OrderedDict

from .models import Sentence, Word
from .processing import get_context_for_word


async def word_context(word: Word) -> str:
    output = OrderedDict()
    if word.id:
        nr = itertools.count(1)
        async for context in get_context_for_word(word.id):
            if context.book_id not in output:
                output[context.book_id] = f"        TITLE: --> {context.book.title} <--\n"
            output[context.book_id] += f"[{next(nr)}] {context.content}\n"
    return ''.join(output.values())


def find_word_in_context(word_str: str) -> tuple[Word, list[str]]:
    """
    find word in context
    """
    word = Word(key_word=word_str)
    word.match_first()


async def word_sentences(word: Word) -> str:
    """
    View book title in first row and the next rows have sentences with translation.
    """
    output = OrderedDict()
    if word.id:
        async for sentence in Sentence.get_by_word(word_id=word.id):
            if sentence.book_id not in output:
                output[sentence.book_id] = f"{sentence.book.title} ({sentence.book_id})\n"
            translations = '; '.join(sentence.translations)
            output[sentence.book_id] += f"    {sentence.text} -> {translations}\n"
    return ''.join(output.values())
