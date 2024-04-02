import asyncio
import csv
import itertools
from pathlib import Path
from typing import Optional, Iterable

import nltk
import requests
from sqlalchemy.ext.asyncio import AsyncSession
from urllib3.exceptions import InsecureRequestWarning

from .crud.book import get_book, update_book, create_book
from .crud.flashcard import (
    get_flashcards_by_keyword,
    create_flashcard,
    flashcard_join_to_sentences,
)
from .crud.sentence import create_sentence, count_sentences_for_book, get_sentences_with_phrase
from .crud.user import get_user_by_email
from .crud.word import (
    get_word_by_lem_pos,
    update_word,
    create_word,
    word_join_to_sentences,
    count_words_for_book,
    get_sentence_ids_with_word,
)
from .db.session import get_session
from .models.book import Book, BookCreate
from .models.flashcard import Flashcard, FlashcardCreate
from .models.flashcard_word import FlashcardWord
from .models.sentence import Sentence, SentenceCreate
from .models.sentence_flashcard import SentenceFlashcard
from .models.sentence_word import SentenceWord
from .models.user import User
from .models.word import Word, WordCreate
from .structure import (
    DETERMINERS,
    PRONOUNS,
    tag_to_pos,
)
from .messages import book_created_message, book_not_found_message, loading_message

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


def get_pattern(word: str) -> str:
    """
    Pattern to find sentences with this word in book
    """
    return r'([^.?!"]*\s' + word + r'[^.?!"]*[.?!]?)|(^' + word + r'[^.?!"]*[.?!]?)'


async def find_word(word_str: str) -> Word:
    """
    Find word in db
    """
    lemmatizer = nltk.WordNetLemmatizer()
    lem = lemmatizer.lemmatize(word_str)
    word = Word(lem=lem)
    await word.match_first()
    return word


def get_book_content(book_path: Path) -> str:
    """
    Get whole book content
    """
    with open(book_path) as f:
        book_content = f.read()
    return book_content

def get_translations_content(translations_path: Path) -> list:
    """
    Read csv file and return list with translations
    """
    with open(translations_path) as f:
        return [row for row in csv.reader(f, delimiter=";")]


def filter_source(words: list) -> tuple[list, str] | None:
    """
    Find words which has additional parts
    """
    if len(words) == 2:
        if words[0].lower() == "to":
            return [words[1]], "v"
        elif words[0].lower() in DETERMINERS:
            return [words[1]], "n"
        elif words[0].lower() in PRONOUNS:
            return [words[1]], "v"


def find_pos(words: list) -> Optional[str]:
    """
    For single word in list find tag and change it to pos
    """
    if len(words) == 1:
        word, tag_pos = nltk.pos_tag([words[0]])[0]
        pos = tag_to_pos(tag_pos)
        return pos


def lemmatize(lemmatizer, source: str) -> str:
    """
    Lemmatize word or return unchanged
    """
    words = nltk.word_tokenize(source)
    words_and_pos = filter_source(words)
    if words_and_pos:
        words, pos = words_and_pos
    else:
        pos = find_pos(words)

    if pos:
        if len(words) == 1:
            return lemmatizer.lemmatize(words[0], pos=pos)

    return source


async def load_translations_cmd(book_id: Optional[int], filename_path: Path) -> Book:
    """
    Run asynchronous function which load translations from csv to db
    """
    book = await get_or_create_book(book_id, filename_path)
    translations_list = get_translations_content(filename_path)

    async for session in get_session():
        pos_collections = await load_translations_content(session, translations_list)

    async for session in get_session():
        for dest in pos_collections:
            await save_prepared_words(session, dest)
    return book


async def get_or_create_book(book_id: Optional[int], filename_path: Path) -> Book:
    """
    Get book for loading translations or create new book based on filename.
    """
    async for session in get_session():
        if book_id:
            book = await get_book(session, book_id)
            if not book.title:
                raise ValueError(f"Book not found by id: {book_id}")
        else:
            title_from_filename = filename_path.name.split(".")[0]
            book = await create_book(
                session,
                BookCreate(
                    title=title_from_filename,
                    author="",
                ),
            )
            book_created_message(book.id, book.title)

        loading_message(book.id, book.title)
        return book


async def load_translations_content(session: AsyncSession, translation_rows: Iterable):
    user = await get_user_by_email(session, "jkowalski@example.com")

    nouns = {}  # n
    verbs = {}  # v
    adverbs = {}  # r
    adjectives = {}  # a

    for source_text, translation_str in translation_rows:
        flashcard = None
        for retrieved_flashcard in await get_flashcards_by_keyword(session, source_text):
            if translation_str in retrieved_flashcard.translations:
                flashcard = retrieved_flashcard
        if not flashcard:
            flashcard = await create_flashcard(
                session,
                FlashcardCreate(
                    user_id=user.id,
                    keyword=source_text,
                    translations=[translation_str],
                ),
            )
        if len(source_text.split()) == 1:
            sentence_ids = set(await get_sentence_ids_with_word(session, source_text))
        else:
            sentence_ids = set(
                [s.id for s in await get_sentences_with_phrase(session, source_text)]
            )

        for word_str, tag in nltk.pos_tag(nltk.word_tokenize(source_text)):
            if tag in ("NN", "NNP", "NNPS", "NNS"):
                empty = bool(tag in ("NN", "NNP"))
                pos = nltk.corpus.wordnet.NOUN  # n
                dest = nouns

            elif tag in ("VB", "VBD", "VBG", "VBN", "VBP", "VBZ"):
                empty = bool(tag in ("VB", "VBP"))
                pos = nltk.corpus.wordnet.VERB  # v
                dest = verbs

            elif tag in ("RB", "RBR", "RBS"):
                empty = bool(tag == "RB")
                pos = nltk.corpus.wordnet.ADV  # r
                dest = adverbs

            elif tag in ("JJ", "JJR", "JJS"):
                empty = bool(tag == "JJ")
                pos = nltk.corpus.wordnet.ADJ  # a
                dest = adjectives

            else:
                continue

            create_word_clone(
                sentence_ids, flashcard.id, word_str.lower(), tag, pos, empty, dest
            )

    return nouns, verbs, adverbs, adjectives


def create_word_clone(
    sentence_ids: set[int],
    flashcard_id: [int],
    word_str: str,
    tag: str,
    pos: str,
    empty: bool,
    dest: dict[str, dict],
) -> None:
    """
    Create Word object and add to dest dict
    """
    lem = nltk.corpus.wordnet.morphy(word_str, pos) if pos else None
    if not lem:
        lem = word_str

    if lem in dest:
        word_dict = dest[lem]
        word_dict["count"] += 1
        word_dict["sentence_ids"].update(sentence_ids)
        if flashcard_id:
            word_dict["flashcard_ids"].add(flashcard_id)
        if not empty:
            word_dict["declination"][tag] = word_str

    else:
        word_dict = {
            "count": 1,
            "lem": lem if lem else word_str,
            "pos": pos,
            "declination": {} if empty else {tag: word_str},
            "sentence_ids": sentence_ids,
            "flashcard_ids": {flashcard_id} if flashcard_id else set(),  # set
        }
        dest[lem] = word_dict


async def save_sentence(sentence_nr: ..., book_id: int, sentence_text: str) -> Sentence:
    sentence = Sentence(
        nr=next(sentence_nr),
        book_id=book_id,
        sentence=sentence_text.split("\n")[0],
    )
    await sentence.save()
    return sentence


async def split_to_sentences(session: AsyncSession, book_raw: str, book_id: int) -> Sentence:
    sentence_nr = itertools.count()

    for sentence_text in nltk.sent_tokenize(book_raw):
        if sentence_text.lower().startswith("chapter "):
            chapter, *rest = sentence_text.split("\n")
            await create_sentence(
                session,
                SentenceCreate(
                    nr=next(sentence_nr),
                    book_id=book_id,
                    sentence=chapter,
                ),
            )
            sentence_text = "\n".join(rest)

        if not sentence_text:
            continue

        sentence = await create_sentence(
            session,
            SentenceCreate(
                nr=next(sentence_nr),
                book_id=book_id,
                sentence=sentence_text,
            ),
        )
        yield sentence


async def load_book_content_cmd(book_path: Path, book_id: int) -> Book:
    """
    Load book from path, and add book.
    """
    async for session in get_session():
        book = await get_book(session, book_id=book_id)

    if book.title is None:
        raise ValueError(f"ERROR: Not found book for id = {book_id}.")

    book_raw = get_book_content(book_path)

    pos_collections = await load_sentences(session, book_raw, book_id)

    for dest in pos_collections:
        await save_prepared_words(session, dest)

    async for session in get_session():
        book.sentences_count = await count_sentences_for_book(session, book.id)
        book.words_count = await count_words_for_book(session, book.id)
        await update_book(session, book.id, book)

    return book


async def load_sentences(
    session: AsyncSession, book_raw: str, book_id: int
) -> tuple[dict, dict, dict, dict]:
    nouns = {}  # n
    verbs = {}  # v
    adverbs = {}  # r
    adjectives = {}  # a

    async for sentence in split_to_sentences(session, book_raw, book_id):
        for word_str, tag in nltk.pos_tag(nltk.word_tokenize(sentence.sentence)):
            if tag in ("NN", "NNP", "NNPS", "NNS"):
                empty = bool(tag in ("NN", "NNP"))
                pos = nltk.corpus.wordnet.NOUN  # n
                dest = nouns

            elif tag in ("VB", "VBD", "VBG", "VBN", "VBP", "VBZ"):
                empty = bool(tag in ("VB", "VBP"))
                pos = nltk.corpus.wordnet.VERB  # v
                dest = verbs

            elif tag in ("RB", "RBR", "RBS"):
                empty = bool(tag == "RB")
                pos = nltk.corpus.wordnet.ADV  # r
                dest = adverbs

            elif tag in ("JJ", "JJR", "JJS"):
                empty = bool(tag == "JJ")
                pos = nltk.corpus.wordnet.ADJ  # a
                dest = adjectives

            else:
                continue

            create_word_clone({sentence.id}, None, word_str.lower(), tag, pos, empty, dest)

    return nouns, verbs, adverbs, adjectives


async def save_prepared_words(session: AsyncSession, dest: dict) -> None:
    for lem, word_dict in dest.items():
        word = await get_word_by_lem_pos(session, lem=word_dict["lem"], pos=word_dict["pos"])
        if word:
            word.count += word_dict["count"]
            word.declination.update(word_dict["declination"])
            await update_word(session, word.id, word)
        else:
            word = await create_word(
                session,
                WordCreate(
                    count=word_dict["count"],
                    declination=word_dict["declination"],
                    lem=word_dict["lem"],
                    pos=word_dict["pos"],
                ),
            )

        if word_dict["sentence_ids"]:
            await word_join_to_sentences(session, word.id, word_dict["sentence_ids"])
        if word_dict["flashcard_ids"]:
            for flashcard_id in word_dict["flashcard_ids"]:
                await flashcard_join_to_sentences(session, flashcard_id, word_dict["sentence_ids"])


async def match_word_definitions(word: str, sentence: str) -> list[str]:
    """
    Find definition for word from sentence
    """
    word_list = nltk.word_tokenize(sentence)
    tags = nltk.pos_tag(word_list)
    tags = [t[1] for t in tags if t[0] == word]
    tag = tags[0] if tags else None
    pos = tag_to_pos(tag)
    definitions = []
    for synset in nltk.corpus.wordnet.synsets(word, pos=pos):
        definition = f"{synset.name()}: {synset.definition()}"
        definitions.append(definition)
    return definitions
