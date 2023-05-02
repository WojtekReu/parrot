import csv
import itertools
import re
from typing import Generator, Optional

import nltk

from .models import Book, BookWord, Context, Sentence, Word, WordSentence
from .alchemy import BOOKS_PATH
from .structure import (
    BookContent,
    DETERMINERS,
    Flashcard,
    PRONOUNS,
    SENTENCES_LIMIT,
    tag_to_pos,
    TYPE_SENTENCE,
    TYPE_WORD,
)


def flashcard_list(book_id: int) -> list[Flashcard]:
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
        for word in Word.get_by_book(book_id)
    ] + [
        Flashcard(
            sentence.order, sentence.text, sentence.translations, TYPE_SENTENCE, None
        )
        for sentence in Sentence.get_by_book(book_id)
    ]

    flashcards.sort(key=lambda f: f.order)

    return flashcards


def get_context_for_word(word_id: int) -> Generator:
    """
    Get all sentences from book that match to this word.
    """
    for context in Context.get_by_word(word_id):
        yield context


def get_pattern(word: str) -> str:
    """
    Pattern to find sentences with this word in book
    """
    return r'([^.?"]*?' + word + r'*[^.?"]*[.?]?)'


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
                book.find_first()
                if not book.id:
                    book.save()
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
    with open(book.path) as f:
        while True:
            line = f.readline()
            if not line:
                break
            line = line.strip()
            if line:
                book_contents.append(
                    BookContent(
                        line,
                        tuple(stemmer.stem(word) for word in nltk.word_tokenize(line)),
                    )
                )
    return book_contents


def connect_words_to_sentences():
    """
    Create relations between words and sentences
    """
    stemmer = nltk.PorterStemmer()
    sentences = prepare_sentences(stemmer)
    print(f"Loaded {len(sentences)} sentences.")

    for word in Word.all():
        word_stem = stemmer.stem(word.key_word)
        for sentence_tuple in sentences:
            if word_stem in sentence_tuple[1]:
                ws = WordSentence(
                    word_id=word.id,
                    sentence_id=sentence_tuple[0],
                )
                ws.find_first()
                if not ws.id:
                    ws.save()

    print("Connecting words to sentences done.")


def find_words_in_book(book):
    """
    Find words in book using stem word for matching.
    """
    stemmer = nltk.PorterStemmer()
    book_contents = prepare_book_sentences(stemmer, book)
    print(f"Loaded whole book '{book.title}' in parts: {len(book_contents)}")

    # for word in Word.get_by_book(book.id):
    for word in Word.all():
        word_stem = stemmer.stem(word.key_word)
        sentences_count = Context.count_for_word(word.id)
        if sentences_count > SENTENCES_LIMIT:
            break
        for content in book_contents:
            if word_stem in content.stems:
                if sentences_count > SENTENCES_LIMIT:
                    break
                sentences_count += 1

                pattern = get_pattern(word.key_word)
                results = re.findall(pattern, content.sentence, re.IGNORECASE)
                if not results:
                    pattern = get_pattern(word_stem)
                    results = re.findall(pattern, content.sentence, re.IGNORECASE)
                    if not results:
                        results = [content.sentence[:255]]

                for sentence in results:
                    context = Context(
                        content=sentence.strip(),
                        word_id=word.id,
                        book_id=book.id,
                    )
                    context.find_first()
                    if not context.id:
                        context.save()


def find_books():
    """
    For any book in db check is in library
    """
    for book in Book.all():
        if book.path:
            find_words_in_book(book)


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


def load_file(filename_path):
    """
    Load csv translation file to db
    """
    book = find_book(filename_path.parts[-1])
    order = itertools.count(start=1)
    lemmatizer = nltk.WordNetLemmatizer()

    with open(filename_path) as f:
        csv_data = csv.reader(f, delimiter=";")
        for row in csv_data:
            col1, col2 = row[0], row[1]
            col1 = lemmatize(lemmatizer, col1)
            if len(col1.strip().split()) == 1:
                word = Word(key_word=col1)
                word.find_first()
                if word.id:
                    if col2 not in word.translations:
                        word.translations.append(col2)
                        word.save()
                    book_word = BookWord(
                        book_id=book.id,
                        word_id=word.id,
                    )
                    book_word.find_first()
                    if not book_word.id:
                        book_word.order = next(order)
                        book_word.save()
                else:
                    word.translations = [col2]
                    book_word = BookWord(
                        book_id=book.id,
                        word_id=word.save(),
                    )
                    book_word.find_first()
                    if not book_word.id:
                        book_word.order = next(order)
                        book_word.save()

            else:
                sentence = Sentence(
                    book_id=book.id,
                    text=col1,
                )
                sentence.find_first()
                if not sentence.id:
                    sentence.order = next(order)
                    sentence.translations = [col2]
                    sentence.save()
                elif col2 not in sentence.translations:
                    sentence.translations.append(col2)
                    sentence.save()


def show_end_up_result(total, correct):
    """
    Show end up result
    """
    print(f"\n========== Correct words: {correct}/{total} ==========\n")


def print_all_books():
    """
    Print id, title and author for all books.
    """
    for book in Book.all():
        print(f"{book.id}. {book.title} - {book.author}")


def learn(book_id: int, start_line: int) -> tuple[int, int]:
    """
    Print flashcard and read input from user. Compare them and show results.
    """
    correct = 0
    total = 0

    for flashcard in flashcard_list(book_id)[start_line:]:
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
                for nr, context in enumerate(
                    get_context_for_word(flashcard.word_id), start=1
                ):
                    print(f"{context.book_id}, {nr}: {context.content}")

    return total, correct
