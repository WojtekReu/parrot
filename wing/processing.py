import asyncio
import csv
import itertools
import json
import re
from pathlib import Path
from typing import Optional, AsyncIterable

import nltk
import requests
from urllib3.exceptions import InsecureRequestWarning

from .logging import write_logs
from .models import (
    Book,
    BookTranslation,
    BookContent,
    Bword,
    BwordBookContent,
    max_order_for_book_id,
    ParrotSettings,
    Sentence,
    Translation,
)
from .alchemy import API_URL, BOOKS_PATH, PONS_SECRET_KEY
from .structure import (
    ADVERBS,
    DETERMINERS,
    Flashcard,
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
from .views import (
    show_matched_for_translation,
    show_not_matched_for_translation,
    show_correct_translation,
)

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


async def flashcard_list(book_id: int) -> list[Flashcard]:
    """
    Flashcards are composed of words and sentences
    """
    flashcards = [
        Flashcard(
            translation.order,
            translation.source,
            translation.text,
            TYPE_WORD,
            translation,
        )
        async for translation in Translation.get_by_book(book_id)
    ] + [
        Flashcard(
            sentence.order, sentence.text, sentence.translation, TYPE_SENTENCE, None
        )
        async for sentence in Sentence.get_by_book(book_id)
    ]

    flashcards.sort(key=lambda f: f.order)

    return flashcards


def get_pattern(word: str) -> str:
    """
    Pattern to find sentences with this word in book
    """
    return r'([^.?!"]*\s' + word + r'[^.?!"]*[.?!]?)|(^' + word + r'[^.?!"]*[.?!]?)'


async def find_word(word_str: str) -> Bword:
    """
    Find word in db
    """
    lemmatizer = nltk.WordNetLemmatizer()
    lem = lemmatizer.lemmatize(word_str)
    bword = Bword(lem=lem)
    await bword.match_first()
    return bword


def get_book_content(book_path: Path) -> str:
    """
    Get whole book content
    """
    with open(book_path) as f:
        book_content = f.read()
    return book_content


async def connect_words_to_sentences() -> None:
    """
    Create relations between words and sentences
    """
    lemmatizer = nltk.WordNetLemmatizer()
    async for sentence in Sentence.all():
        for word_str in nltk.word_tokenize(sentence.text):
            word_lem = lemmatizer.lemmatize(word_str)
            bword = Bword(lem=word_lem)
            await bword.match_first()
            async for translation in bword.get_translations():
                if sentence.id not in translation.sentences:
                    translation.sentences.append(sentence.id)
                await translation.save()


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


def load_translations_cmd(book_id: Optional[int], filename_path: Path) -> None:
    """
    Run asynchronous function which load translations from csv to db
    """
    asyncio.run(load_translations(book_id, filename_path))


async def load_translations(book_id: Optional[int], filename_path: Path) -> None:
    """
    Load csv translation file to db for selected book
    """
    if book_id:
        book = Book(id=book_id)
        await book.match_first()
        if book.title:
            loading_message(book.id, book.title)
        else:
            book_not_found_message(book_id)
            return
    else:
        title_from_filename = filename_path.name.split(".")[0]
        book = Book(
            title=title_from_filename,
            author="",
        )
        await book.match_first()
        if not book.id:
            await book.save()
            book_created_message(book.id, book.title)
        loading_message(book.id, book.title)

    max_order = await max_order_for_book_id(book.id) + 1
    order = itertools.count(start=max_order)
    lemmatizer = nltk.WordNetLemmatizer()

    with open(filename_path) as f:
        csv_data = csv.reader(f, delimiter=";")
        for row in csv_data:
            word_str, translation_str = row[0], row[1]
            lem = lemmatize(lemmatizer, word_str)
            if len(lem.strip().split()) == 1:
                bword = Bword(lem=lem)
                await bword.match_first()
                if not bword.declination:
                    bword.declination = [word_str]
                elif word_str not in bword.declination:
                    bword.declination.append(word_str)
                await bword.save()

                translation = Translation(
                    bword_id=bword.id,
                    source=word_str,
                    text=translation_str,
                )
                await translation.match_first()
                if not translation.id:
                    await translation.save()
                book_translation = BookTranslation(
                    book_id=book.id,
                    translation_id=translation.id,
                )
                await book_translation.match_first()
                if not book_translation.id:
                    book_translation.order = next(order)
                    await book_translation.save()

            else:
                sentence = Sentence(
                    book_id=book.id,
                    text=word_str,
                )
                await sentence.match_first()
                if not sentence.id:
                    sentence.order = next(order)
                    sentence.translation = translation_str
                    await sentence.save()


async def learn(book_id: int, start_line: int) -> tuple[int, int]:
    """
    Print flashcard and read input from user. Compare them and show results.
    """
    correct = 0
    total = 0

    f_list = await flashcard_list(book_id)
    for flashcard in f_list[start_line:]:
        try:
            if flashcard.type == TYPE_WORD:
                bword = Bword(id=flashcard.translation_obj.bword_id)
                async for bc in bword.get_book_contents(book_id=book_id):
                    print('=========================================================')
                    print(bc.sentence)
                    break  # only first sentence is needed
            your_response = input(f"{flashcard.text} - ").strip()
        except KeyboardInterrupt:
            return total, correct

        total += 1

        if your_response == flashcard.translation:
            print("OK")
            correct += 1
        else:
            show_correct_translation(flashcard)
            if flashcard.type == TYPE_WORD:
                print_result = await show_matched_for_translation(
                    flashcard.translation_obj
                )

                if not print_result:
                    await show_not_matched_for_translation(bword)

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


async def add_sentence_book_content(book_id, sentence_nr, sentence, book_contents) -> None:
    if not sentence:
        return

    if sentence.lower().startswith("chapter "):
        book_content = BookContent(
            nr=next(sentence_nr),
            book_id=book_id,
            sentence=sentence.split("\n")[0],
        )
        await book_content.save()
        sentence = "\n".join(sentence.split("\n")[1:])

    book_content = BookContent(
        nr=next(sentence_nr),
        book_id=book_id,
        sentence=sentence,
    )
    await book_content.save()
    await book_contents.put(book_content)


async def split_to_words(book_content, lemmatizer, bwords, relations) -> None:
    bword_ids = set()
    for word in nltk.word_tokenize(book_content.sentence):
        if not word.isalpha():
            continue

        word = word.lower()
        lem = lemmatizer.lemmatize(word)
        if len(lem) < MIN_LEM_WORD:
            continue

        if lem in bwords:
            bword = bwords[lem]
            bword.count += 1
            if word not in bword.declination:
                bword.declination.append(word)
            bword.update_later = True
        else:
            bword = Bword(
                lem=lem,
            )
            await bword.match_first()
            if bword.id:
                bword.count += 1
                if word not in bword.declination:
                    bword.declination.append(word)
                bword.update_later = True
            else:
                bword = Bword(
                    lem=lem,
                    declination=[word],
                    count=1,
                )
                bword.update_later = False
                await bword.save()
            bwords[lem] = bword

        if bword.count < MAX_STEM_OCCURRENCE:
            bword_ids.add(bword)

    for bword2 in bword_ids:
        await relations.put((book_content, bword2))


async def join_word_to_sentence(book_content_id, bword_id) -> None:
    bbc = BwordBookContent(
        book_content_id=book_content_id,
        bword_id=bword_id,
    )
    await bbc.save()


async def save_bwords_to_db(bwords, status) -> None:
    while True:
        if status["r"]:
            for lem, bword in bwords.items():
                if bword.update_later:
                    await bword.save()
            return
        else:
            await asyncio.sleep(0.1)


async def put_sentences(book_raw, sentences: asyncio.Queue, status):
    for sentence in nltk.sent_tokenize(book_raw):
        await sentences.put(sentence)
    status["s"] = True


async def task_add_sentence_book_content(book_id, sentence_nr, sentences: asyncio.Queue, book_contents, status):
    while True:
        try:
            sentence = sentences.get_nowait()
            await add_sentence_book_content(book_id, sentence_nr, sentence, book_contents)
            sentences.task_done()
        except asyncio.QueueEmpty:
            # await sentences.join()
            if status["s"]:
                await sentences.join()
                status["w"] = True
                return
            await asyncio.sleep(0.1)


async def task_split_to_words(book_contents, lemmatizer, bwords, relations, status):
    while True:
        try:
            book_content = book_contents.get_nowait()
            await split_to_words(book_content, lemmatizer, bwords, relations)
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
            book_content, bword = relations.get_nowait()
            await join_word_to_sentence(book_content.id, bword.id)
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


async def process_words(book_contents, lemmatizer, bwords, relations, tasks, status):
    task = asyncio.create_task(
        task_split_to_words(book_contents, lemmatizer, bwords, relations, status),
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
    lemmatizer = nltk.WordNetLemmatizer()
    sentence_nr = itertools.count()

    tasks = []
    status = {"s": False, "w": False, "r": False, "x": False}
    await asyncio.gather(
        put_sentences(book_raw, sentences, status),
        process_sentences(sentences, tasks, book_id, sentence_nr, book_contents, status),
        process_words(book_contents, lemmatizer, bwords, relations, tasks, status),
        process_word_sentence_relation(relations, tasks, status),
        return_exceptions=True,
    )

    await save_bwords_to_db(bwords, status)

    for task in tasks:
        task.cancel()


async def load_book_content_cmd(book_path: Path, book_id: int) -> Book:
    """
    Load book from path, and add book.
    """
    book = Book(id=book_id)
    await book.match_first()
    if book.title is None:
        raise ValueError(f"ERROR: Not found book for id = {book_id}.")

    book_raw = get_book_content(book_path)

    await tokenize_book_content(book_id, book_raw)

    book.sentences_count = await BookContent.count_sentences_for_book(book.id)
    await book.save()
    return book


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
