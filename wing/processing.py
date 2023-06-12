import asyncio
import csv
import itertools
import json
import re
import queue
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Coroutine, Generator, Optional

import nltk
import requests
from urllib3.exceptions import InsecureRequestWarning

from .logging import write_logs
from .models import (
    Book,
    BookContent,
    BookWord,
    Context,
    ParrotSettings,
    Sentence,
    Word,
    WordSentence,
    max_order_for_book_id, Bword, BwordBookContent,
)
from .alchemy import API_URL, BOOKS_PATH, PONS_SECRET_KEY
from .structure import (
    ADVERBS,
    DETERMINERS,
    Flashcard,
    MIN_STEM_WORD,
    MAX_STEM_OCCURRENCE,
    PREPOSITIONS,
    PRONOUNS,
    SENTENCES_LIMIT,
    tag_to_pos,
    TYPE_SENTENCE,
    TYPE_WORD,
)

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


async def flashcard_list(book_id: int) -> list[Flashcard]:
    """
    Flashcards are composed of words and sentences
    """
    flashcards = [
        Flashcard(
            word.order,
            word.key_word,
            word.translations,
            TYPE_WORD,
            word.id,
        )
        async for word in Word.get_by_book(book_id)
    ] + [
        Flashcard(
            sentence.order, sentence.text, sentence.translations, TYPE_SENTENCE, None
        )
        async for sentence in Sentence.get_by_book(book_id)
    ]

    flashcards.sort(key=lambda f: f.order)

    return flashcards


async def get_context_for_word(word_id: int) -> Generator:
    """
    Get all sentences from book that match to this word.
    """
    async for context in Context.get_by_word(word_id):
        yield context


def get_pattern(word: str) -> str:
    """
    Pattern to find sentences with this word in book
    """
    return r'([^.?!"]*\s' + word + r'[^.?!"]*[.?!]?)|(^' + word + r'[^.?!"]*[.?!]?)'


def find_book(filename: str) -> Optional[Book]:
    """
    File book_list.csv contains 4 columns. Function will add book to db.
    """
    with open(BOOKS_PATH) as f:
        csv_data = csv.reader(f, delimiter=";")
        for row in csv_data:
            if row[0] == filename:
                book = Book(
                    title=row[1],
                    author=row[2],
                    path=row[3],  # path to book in personal library if library contain this book
                )
                book.save_if_not_exists()
                return book

        raise ValueError(f"Path {filename} not in {BOOKS_PATH}")


def prepare_sentences(stemmer) -> list[tuple[int, list[str]]]:
    """
    Get all sentences and prepare stem for all words
    """
    sentences = []
    for sentence in Sentence.all():
        sentence_list = [
            stemmer.stem(word) for word in nltk.word_tokenize(sentence.text)
        ]
        sentences.append((sentence.id, sentence_list))

    return sentences


def prepare_book_sentences(stemmer, book: Book) -> list[BookContent]:
    """
    Get whole book as list of BookContent
    """
    book_contents = []
    book_content = get_book_content(book)

    for sentence in nltk.sent_tokenize(book_content):
        if sentence:
            words = []
            stems = []
            for word in nltk.word_tokenize(sentence):
                words.append(word)
                stems.append(stemmer.stem(word))
            book_contents.append(
                BookContent(
                    sentence,
                    tuple(words),
                    tuple(stems),
                )
            )
    return book_contents


def get_book_content(book_path: Path) -> str:
    """
    Get whole book content
    """
    with open(book_path) as f:
        book_content = f.read()
    return book_content


def connect_words_to_sentences():
    """
    Create relations between words and sentences
    """
    stemmer = nltk.PorterStemmer()
    sentences = prepare_sentences(stemmer)
    print(f"Loaded {len(sentences)} sentences.")

    for word in Word.newer_than(ParrotSettings.get_last_word_id()):
        word_stem = stemmer.stem(word.key_word)
        for sentence_tuple in sentences:
            if word_stem in sentence_tuple[1]:
                ws = WordSentence(
                    word_id=word.id,
                    sentence_id=sentence_tuple[0],
                )
                ws.save_if_not_exists()

    print("Connecting words to sentences done.")


def find_words_in_book(book):
    """
    Find words in book using stem word for matching.
    """
    stemmer = nltk.PorterStemmer()
    book_contents = prepare_book_sentences(stemmer, book)
    print(f"Loaded whole book '{book.title}': {len(book_contents)} sentences.")

    # for word in Word.get_by_book(book.id):
    for word in Word.newer_than(ParrotSettings.get_last_word_id()):
        word_stem = stemmer.stem(word.key_word)
        for content in book_contents:
            if word_stem in content.stems:
                context = Context(
                    content=content.sentence,
                    word_id=word.id,
                    book_id=book.id,
                )
                context.save_if_not_exists()

        if not word.key_word.startswith(word_stem):
            for content in book_contents:
                if word.key_word in content.words:
                    context = Context(
                        content=content.sentence,
                        word_id=word.id,
                        book_id=book.id,
                    )
                    context.save_if_not_exists()


def find_books():
    """
    For any book in db check is in library
    Replace “ and ” to " in all books
    """
    for book in Book.all():
        if book.path:
            find_words_in_book(book)

    ParrotSettings.update_last_settings_id()


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


def load_translations(book_id, filename_path):
    """
    Load csv translation file to db
    """
    asyncio.run(load_translations_asyncio(book_id, filename_path))


async def load_translations_asyncio(book_id, filename_path):
    book = Book(id=book_id)
    await book.match_first()
    max_order = await max_order_for_book_id(book.id) + 1
    order = itertools.count(start=max_order)
    lemmatizer = nltk.WordNetLemmatizer()

    with open(filename_path) as f:
        csv_data = csv.reader(f, delimiter=";")
        for row in csv_data:
            col1, col2 = row[0], row[1]
            col1 = lemmatize(lemmatizer, col1)
            if len(col1.strip().split()) == 1:
                word = Word(key_word=col1)
                await word.match_first()
                if word.id:
                    if col2 not in word.translations:
                        word.translations.append(col2)
                        await word.save()
                    book_word = BookWord(
                        book_id=book.id,
                        word_id=word.id,
                    )
                    await book_word.match_first()
                    if not book_word.id:
                        book_word.order = next(order)
                        await book_word.save()
                else:
                    word.translations = [col2]
                    await word.save()
                    book_word = BookWord(
                        book_id=book.id,
                        word_id=word.id,
                    )
                    await book_word.match_first()
                    if not book_word.id:
                        book_word.order = next(order)
                        await book_word.save()

            else:
                sentence = Sentence(
                    book_id=book.id,
                    text=col1,
                )
                await sentence.match_first()
                if not sentence.id:
                    sentence.order = next(order)
                    sentence.translations = [col2]
                    await sentence.save()
                elif col2 not in sentence.translations:
                    sentence.translations.append(col2)
                    await sentence.save()


def show_end_up_result(total, correct):
    """
    Show end up result
    """
    print(f"\n========== Correct words: {correct}/{total} ==========\n")


async def print_all_books():
    """
    Print id, title and author for all books.
    """
    async for book in Book.all():
        print(f"{book.id}. {book.title} - {book.author}")


async def learn(book_id: int, start_line: int) -> tuple[int, int]:
    """
    Print flashcard and read input from user. Compare them and show results.
    """
    correct = 0
    total = 0

    f_list = await flashcard_list(book_id)
    for flashcard in f_list[start_line:]:
        try:
            your_response = input(f"{flashcard.text} - ").strip()
        except KeyboardInterrupt:
            return total, correct

        total += 1

        if your_response in flashcard.translations:
            print("OK")
            correct += 1
        else:
            spaces_nr = len(flashcard.text) + 3
            translations = "; ".join(flashcard.translations)
            print(" " * spaces_nr + translations)
            if flashcard.type == TYPE_WORD:
                nr = itertools.count(1)
                async for context in get_context_for_word(flashcard.word_id):
                    print(f"{context.book_id}, {next(nr)}: {context.content}")

    return total, correct


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


def save_translations(word: Word, translations: list):
    """
    Add translation to words translations.
    """
    is_changed = False
    for translation_tuple in translations:
        source, translation = translation_tuple
        if source == word.key_word and translation not in word.translations:
            is_changed = True
            word.translations.append(translation)

    if is_changed:
        word.save()


async def add_sentence_book_content(book_id, sentence_nr, sentence, book_contents) -> None:
    if not sentence:
        return

    if sentence.lower().startswith('chapter '):
        book_content = BookContent(
            nr=next(sentence_nr),
            book_id=book_id,
            sentence=sentence.split("\n")[0],
        )
        await book_content.save()
        sentence = "\n".join(sentence.split("\n")[1:])[:255]

    book_content = BookContent(
        nr=next(sentence_nr),
        book_id=book_id,
        sentence=sentence[:255],
    )
    await book_content.save()
    await book_contents.put(book_content)


async def split_to_words(book_content, stemmer, bwords, relations) -> None:
    bword_ids = set()
    for word in nltk.word_tokenize(book_content.sentence):
        if not word.isalpha():
            continue

        word = word.lower()
        stem = stemmer.stem(word)
        if len(stem) < MIN_STEM_WORD:
            continue

        if stem in bwords:
            bword = bwords[stem]
            bword.count += 1
            bword.update_later = True
        else:
            bword = await Bword(stem=stem).find_stem()
            if bword:
                bword.update_later = True
            else:
                bword = Bword(
                    stem=stem,
                    declination=[word],
                    count=1,
                )
                bword.update_later = False
                await bword.save()
            bwords[stem] = bword

        if word not in bword.declination:
            bword.declination.append(word)

        if bword.count < MAX_STEM_OCCURRENCE and bword.id not in bword_ids:
            bword_ids.add(bword.id)

    for bword_id in bword_ids:
        await relations.put((book_content.id, bword_id))


async def join_word_to_sentence(book_content_id, bword_id) -> None:
    bbc = BwordBookContent(
        book_content_id=book_content_id,
        bword_id=bword_id,
    )
    await bbc.save()


async def save_bwords_to_db(bwords, status) -> None:
    while True:
        if status['r']:
            for stem, bword in bwords.items():
                if bword.update_later:
                    await bword.save()
            return
        else:
            await asyncio.sleep(0.1)


async def put_sentences(book_raw, sentences: asyncio.Queue, status):
    for sentence in nltk.sent_tokenize(book_raw):
        await sentences.put(sentence)
    status['s'] = True


async def task_add_sentence_book_content(book_id, sentence_nr, sentences: asyncio.Queue, book_contents, status):
    while True:
        try:
            sentence = sentences.get_nowait()
            await add_sentence_book_content(book_id, sentence_nr, sentence, book_contents)
            sentences.task_done()
        except asyncio.QueueEmpty:
            # await sentences.join()
            if status['s']:
                await sentences.join()
                status['w'] = True
                return
            await asyncio.sleep(0.1)


async def task_split_to_words(book_contents, stemmer, bwords, relations, status):
    while True:
        try:
            book_content = book_contents.get_nowait()
            await split_to_words(book_content, stemmer, bwords, relations)
            book_contents.task_done()
        except asyncio.QueueEmpty:
            # await book_contents.join()
            if status['w']:
                await book_contents.join()
                status['r'] = True
                return
            await asyncio.sleep(0.1)


async def task_join_word_to_sentence(relations, status):
    while True:
        try:
            book_content_id, bword_id = relations.get_nowait()
            await join_word_to_sentence(book_content_id, bword_id)
            relations.task_done()
        except asyncio.QueueEmpty:
            # await relations.join()
            if status['r']:
                await relations.join()
                return
            await asyncio.sleep(0.1)


async def process_sentences(sentences, tasks, book_id, sentence_nr, book_contents, status):
    task = asyncio.create_task(
        task_add_sentence_book_content(book_id, sentence_nr, sentences, book_contents, status),
        name=f"Task add_sentence {book_id}",
    )
    tasks.append(task)


async def process_words(book_contents, stemmer, bwords, relations, tasks, status):
    task = asyncio.create_task(
        task_split_to_words(book_contents, stemmer, bwords, relations, status),
        name=f"Task split to words",
    )
    tasks.append(task)


async def process_word_sentence_relation(relations, tasks, status):
    task = asyncio.create_task(
        task_join_word_to_sentence(relations, status),
        name=f"join word to sentnece"
    )
    tasks.append(task)


async def tokenize_book_content(book_id, book_raw) -> None:
    sentences = asyncio.Queue(1000)
    book_contents = asyncio.Queue(1500)
    bwords: dict[str, Bword] = {}
    relations = asyncio.Queue(2000)
    stemmer = nltk.PorterStemmer()
    sentence_nr = itertools.count()

    tasks = []
    status = {'s': False, 'w': False, 'r': False, 'x': False}
    await asyncio.gather(
        put_sentences(book_raw, sentences, status),
        process_sentences(sentences, tasks, book_id, sentence_nr, book_contents, status),
        process_words(book_contents, stemmer, bwords, relations, tasks, status),
        process_word_sentence_relation(relations, tasks, status),
    )

    await save_bwords_to_db(bwords, status)

    for task in tasks:
        task.cancel()


async def load_book_content(book_path_str: str, book_id: int) -> None:
    """
    Load book from path, and add book.
    """
    book = Book(id=book_id)
    await book.match_first()
    if book.title is None:
        raise ValueError(f"ERROR: Not found book for id = {book_id}.")

    book_raw = get_book_content(Path(book_path_str))

    await tokenize_book_content(book_id, book_raw)

    book.sentences_count = await BookContent.count_sentences_for_book(book.id)
    await book.save()

    print(f"Loaded whole book '{book.title}': {book.sentences_count} sentences.")
