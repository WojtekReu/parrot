import asyncio
import csv
import itertools
import json
import re
from pathlib import Path
from typing import Optional

import nltk
import requests
from urllib3.exceptions import InsecureRequestWarning

from .logging import write_logs
from .models import (
    Book,
    Flashcard,
    ParrotSettings,
    Sentence,
    Word,
    SentenceWord,
    SentenceFlashcard,
    FlashcardWord,
    User,
)
from .alchemy import API_URL, PONS_SECRET_KEY
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


def load_translations_cmd(book_id: Optional[int], filename_path: Path) -> None:
    """
    Run asynchronous function which load translations from csv to db
    """
    asyncio.run(load_translations(book_id, filename_path))


async def load_translations(book_id: Optional[int], filename_path: Path) -> None:
    """
    Load csv flashcard file to db for selected book
    """
    user = User(username="jkowalski")
    await user.match_first()

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

    with open(filename_path) as f:
        csv_data = csv.reader(f, delimiter=";")

        nouns = {}  # n
        verbs = {}  # v
        adverbs = {}  # r
        adjectives = {}  # a

        for row in csv_data:
            source_text, translation_str = row[0], row[1]
            flashcard = Flashcard(
                user_id=user.id,
                key_word=source_text,
            )
            async for result in flashcard.all():
                if result.translations == [translation_str]:
                    flashcard = result
            if not flashcard.id:
                flashcard.translations = [translation_str]
                await flashcard.save()

            sentence_ids = set([s.id async for s in Sentence.get_sentences(source_text)])

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

                create_word(sentence_ids, flashcard.id, word_str.lower(), tag, pos, empty, dest)

        for dest in (nouns, verbs, adverbs, adjectives):
            for lem, word in dest.items():
                word_existed = await word.match_by_lem_pos()
                if word_existed:
                    word_existed.count += 1
                    for tag, declination in word_existed.declination.items():
                        if tag not in word_existed.declination:
                            word_existed.declination[tag] = declination
                    await word_existed.save()
                    sentence_ids = word.sentence_ids
                    flashcard_ids = word.flashcard_ids
                    word = word_existed
                else:
                    await word.save()
                    sentence_ids = word.sentence_ids
                    flashcard_ids = word.flashcard_ids
                for sentence_id in sentence_ids:
                    for flashcard_id in flashcard_ids:
                        sentence_flashcard = SentenceFlashcard(
                            sentence_id=sentence_id,
                            flashcard_id=flashcard_id,
                        )
                    await sentence_flashcard.save()

                for flashcard_id in flashcard_ids:
                    flashcard_word = FlashcardWord(
                        word_id=word.id,
                        flashcard_id=flashcard_id,
                    )
                    await flashcard_word.match_first()
                    if not flashcard_word.id:
                        await flashcard_word.save()


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


def create_word(
    sentence_ids: set[int],
    flashcard_id: [int],
    word_str: str,
    tag: str,
    pos: str,
    empty: bool,
    dest: dict[str, Word],
) -> None:
    """
    Create Word object and add to dest dict
    """
    lem = nltk.corpus.wordnet.morphy(word_str, pos) if pos else None
    word = Word(
        count=1,
        lem=lem if lem else word_str,
        pos=pos,
        declination={} if empty else {tag: word_str},
    )
    if word.lem not in dest:
        word.sentence_ids = sentence_ids
        word.flashcard_ids = set()
        if flashcard_id:
            word.flashcard_ids.add(flashcard_id)
        dest[word.lem] = word
    elif tag not in dest[word.lem].declination and not empty:
        if flashcard_id:
            dest[word.lem].flashcard_ids.add(flashcard_id)
        dest[word.lem].sentence_ids.update(sentence_ids)
        dest[word.lem].declination[tag] = word.declination

async def save_sentence(sentence_nr: ..., book_id: int, sentence_text: str) -> Sentence:
    sentence = Sentence(
        nr=next(sentence_nr),
        book_id=book_id,
        sentence=sentence_text.split("\n")[0],
    )
    await sentence.save()
    return sentence


async def split_to_sentences(book_raw, book_id) -> Sentence:
    sentence_nr = itertools.count()

    for sentence_text in nltk.sent_tokenize(book_raw):
        if sentence_text.lower().startswith("chapter "):
            chapter, *rest = sentence_text.split("\n")
            sentence_text = "\n".join(rest)
            yield await save_sentence(sentence_nr, book_id, chapter)

        if not sentence_text:
            continue

        yield await save_sentence(sentence_nr, book_id, sentence_text)


async def load_book_content_cmd(book_path: Path, book_id: int) -> Book:
    """
    Load book from path, and add book.
    """
    book = Book(id=book_id)
    await book.match_first()
    if book.title is None:
        raise ValueError(f"ERROR: Not found book for id = {book_id}.")

    book_raw = get_book_content(book_path)

    pos_collections = await load_sentences(book_raw, book_id)

    for dest in pos_collections:
        await save_words(dest)

    book.sentences_count = await Sentence.count_sentences_for_book(book.id)
    book.words_count = await Sentence.count_words_for_book(book.id)
    await book.save()

    return book


async def load_sentences(book_raw: str, book_id: int) -> tuple[dict, dict, dict, dict]:
    nouns = {}  # n
    verbs = {}  # v
    adverbs = {}  # r
    adjectives = {}  # a

    async for sentence in split_to_sentences(book_raw, book_id):

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

            create_word({sentence.id}, None, word_str.lower(), tag, pos, empty, dest)

    return nouns, verbs, adverbs, adjectives


async def save_words(dest: dict) -> None:
    for lem, word in dest.items():
        word_existed = await word.match_by_lem_pos()
        if word_existed:
            word_existed.count += 1
            for tag, declination in word_existed.declination.items():
                if tag not in word_existed.declination:
                    word_existed.declination[tag] = declination
            await word_existed.save()
        else:
            await word.save()
        for sentence_id in word.sentence_ids:
            sentence_word = SentenceWord(
                sentence_id=sentence_id,
                word_id=word.id or word_existed.id,
            )
            await sentence_word.save()


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
