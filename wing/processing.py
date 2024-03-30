import asyncio
import csv
import itertools
import json
import re
from pathlib import Path
from typing import Optional

import nltk
import requests
from sqlalchemy.ext.asyncio import AsyncSession
from urllib3.exceptions import InsecureRequestWarning

from .crud.book import get_book, update_book, create_book
from .crud.flashcard import get_flashcards_by_keyword, create_flashcard
from .crud.sentence import create_sentence, count_sentences_for_book, get_sentences_with_phrase
from .crud.user import get_user_by_email
from .crud.word import (
    get_word_by_lem_pos,
    update_word,
    create_word,
    update_word_join_to_sentences,
    count_words_for_book,
)
from .logging import write_logs
from .db.session import get_session
from .alchemy import API_URL, PONS_SECRET_KEY
from .models.book import Book, BookCreate
from .models.flashcard import Flashcard, FlashcardCreate
from .models.flashcard_word import FlashcardWord
from .models.sentence import Sentence, SentenceCreate
from .models.sentence_flashcard import SentenceFlashcard
from .models.sentence_word import SentenceWord
from .models.user import User
from .models.word import Word, WordCreate
from .structure import (
    ADVERBS,
    DETERMINERS,
    MIN_LEM_WORD,
    MAX_STEM_OCCURRENCE,
    PREPOSITIONS,
    PRONOUNS,
    SENTENCES_LIMIT,
    tag_to_pos,
    TYPE_SENTENCE,
    TYPE_WORD,
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

    async for session in get_session():
        pos_collections = await load_translations_content(session, filename_path)

    async for session in get_session():
        for dest in pos_collections:
            await save_prepared_words(session, dest)
    return book


async def get_or_create_book(book_id: Optional[int], filename_path: Path) -> Book:
    """
    Get book for loading translations
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


async def load_translations_content(session: AsyncSession, filename_path: Path):
    user = await get_user_by_email(session, "jkowalski@example.com")

    with open(filename_path) as f:
        csv_data = csv.reader(f, delimiter=";")

        nouns = {}  # n
        verbs = {}  # v
        adverbs = {}  # r
        adjectives = {}  # a

        for source_text, translation_str in csv_data:
            flashcard = None
            for result_row in await get_flashcards_by_keyword(session, source_text):
                if translation_str in result_row[0].translations:
                    flashcard = result_row[0]
            if not flashcard:
                flashcard = await create_flashcard(
                    session,
                    FlashcardCreate(
                        user_id=user.id,
                        keyword=source_text,
                        translations=[translation_str],
                    ),
                )
            if source_text.split() == 1:
                sentence_ids = "          "
            else:
                sentence_ids = set(
                    [s.id async for s in get_sentences_with_phrase(session, source_text)]
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


def translate(word: str, log_output) -> list[tuple[str, str]]:
    """
    Translate word using dictionary API
    """
    headers = {
        "X-Secret": PONS_SECRET_KEY,
    }
    lang = "enpl"
    url = f"{API_URL}?l={lang}&q={word}"
    response = requests.get(
        url=url,
        headers=headers,
        verify=False,
    )

    if response.status_code == 204:
        print(f"{url = }")
        print("Response status: 204 No content")
        return []

    elif response.status_code == 403:
        print(f"{url = }")
        print("Response status: 404 - Forbidden")
        return []

    elif response.status_code == 504:
        print(f"{url = }")
        print("Response status: 504 - server has problem. Try later.")
        if log_output and response.text:
            logs = {
                "url": url,
                "response": response.text,
            }
            write_logs(logs)
        return []

    elif response.status_code != 200:
        print(f"{url = }")
        print(f"Response status: {response.status_code}")
        if log_output and response.text:
            logs = {
                "url": url,
                "response": response.text,
            }
            write_logs(logs)
        return []
    try:
        response_json = json.loads(response.content)
        if log_output and response_json:
            write_logs(response_json[0])

    except TypeError:
        print(response.raw)
        raise TypeError(response.raw)

    translations = []
    for row in response_json:
        for hit in row["hits"]:
            for rom in hit["roms"]:
                for arab in rom["arabs"]:
                    for translation in arab["translations"]:
                        source = cut_html(translation["source"])
                        target = cut_html(translation["target"])
                        translations.append((source, target))

    return translations


def cut_html(source: str) -> str:
    """
    Dictionary API return word and some description in 'span' tags. Remove span content. For tag
    'strong' remove tag with attributes but leave his content.
    """
    source = re.sub(r" <span .*>.*</span>", "", source)
    return re.sub(r"<.*?>", "", source)


async def save_bwords_to_db(words, status) -> None:
    while True:
        if status["r"]:
            for lem, word in words.items():
                if word.update_later:
                    await word.save()
            return
        else:
            await asyncio.sleep(0.1)


async def put_sentences(book_raw, sentences: asyncio.Queue, status):
    for sentence in nltk.sent_tokenize(book_raw):
        await sentences.put(sentence)
    status["s"] = True


async def task_add_sentence_book_content(
    book_id, sentence_nr, sentences: asyncio.Queue, book_contents, status
):
    while True:
        try:
            sentence_text = sentences.get_nowait()
            if not sentence_text:
                return

            if sentence_text.lower().startswith("chapter "):
                sentence = Sentence(
                    nr=next(sentence_nr),
                    book_id=book_id,
                    sentence=sentence_text.split("\n")[0],
                )
                await sentence.save()
                sentence_text = "\n".join(sentence_text.split("\n")[1:])

            sentence = Sentence(
                nr=next(sentence_nr),
                book_id=book_id,
                sentence=sentence_text,
            )
            await sentence.save()
            await book_contents.put(sentence)
            sentences.task_done()
        except asyncio.QueueEmpty:
            # await sentences.join()
            if status["s"]:
                await sentences.join()
                status["w"] = True
                return
            await asyncio.sleep(0.1)


async def task_split_to_words(book_contents, lemmatizer, words_dict, relations, status):
    stopwords = set(nltk.corpus.stopwords.words("english"))
    while True:
        try:
            sentence = book_contents.get_nowait()
            # run task
            words_set = set()
            for word_str in nltk.word_tokenize(sentence.sentence):
                if not word_str.isalpha():
                    continue

                word_str = word_str.lower()
                lem = lemmatizer.lemmatize(word_str)
                if len(lem) < MIN_LEM_WORD or lem in stopwords:
                    continue

                if lem in words_dict:
                    word_object = words_dict[lem]
                    word_object.count += 1
                    if word_str not in word_object.declination:
                        word_object.declination.append(word_str)
                    word_object.update_later = True
                else:
                    word_object = Word(
                        lem=lem,
                    )
                    await word_object.match_first()
                    if word_object.id:
                        word_object.count += 1
                        if word_str not in word_object.declination:
                            word_object.declination.append(word_str)
                        word_object.update_later = True
                    else:
                        word_object = Word(
                            lem=lem,
                            declination=[word_str],
                            count=1,
                        )
                        word_object.update_later = False
                        await word_object.save()
                    words_dict[lem] = word_object

                if word_object.count < MAX_STEM_OCCURRENCE:
                    words_set.add(word_object)

            for word2 in words_set:
                await relations.put((sentence, word2))

            book_contents.task_done()
        except asyncio.QueueEmpty:
            # await book_contents.join()
            if status["w"]:
                await book_contents.join()
                status["r"] = True
                return
            await asyncio.sleep(0.1)


async def task_join_word_to_sentence(relations, status):
    while True:
        try:
            sentence, word = relations.get_nowait()
            sentence_word = SentenceWord(
                sentence_id=sentence.id,
                word_id=word.id,
            )
            await sentence_word.save()
            relations.task_done()
        except asyncio.QueueEmpty:
            # await relations.join()
            if status["r"]:
                await relations.join()
                return
            await asyncio.sleep(0.1)


async def process_sentences(sentences, tasks, book_id, sentence_nr, book_contents, status):
    task = asyncio.create_task(
        task_add_sentence_book_content(book_id, sentence_nr, sentences, book_contents, status),
        name=f"Task add_sentence {book_id}",
    )
    tasks.append(task)


async def process_words(book_contents, lemmatizer, words, relations, tasks, status):
    task = asyncio.create_task(
        task_split_to_words(book_contents, lemmatizer, words, relations, status),
        name=f"Task split to words",
    )
    tasks.append(task)


async def process_word_sentence_relation(relations, tasks, status):
    task = asyncio.create_task(
        task_join_word_to_sentence(relations, status), name=f"join word to sentence"
    )
    tasks.append(task)


async def tokenize_book_content(book_id, book_raw) -> None:
    sentences = asyncio.Queue(1000)
    book_contents = asyncio.Queue(1500)
    words: dict[str, Word] = {}
    relations = asyncio.Queue(2000)
    lemmatizer = nltk.WordNetLemmatizer()
    sentence_nr = itertools.count()

    tasks = []
    status = {"s": False, "w": False, "r": False, "x": False}
    await asyncio.gather(
        put_sentences(book_raw, sentences, status),
        process_sentences(sentences, tasks, book_id, sentence_nr, book_contents, status),
        process_words(book_contents, lemmatizer, words, relations, tasks, status),
        process_word_sentence_relation(relations, tasks, status),
        return_exceptions=True,
    )

    await save_bwords_to_db(words, status)

    for task in tasks:
        task.cancel()


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
            await update_word_join_to_sentences(session, word.id, word_dict["sentence_ids"])


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
