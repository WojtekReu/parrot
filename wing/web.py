from collections import defaultdict

from wing.models import Book, Word, Flashcard, User, Sentence


async def all_books() -> dict[int, Book]:
    """
    Get all books
    """
    return {book.id: book async for book in Book.all()}


async def get_book(book_id) -> dict[str, ...]:
    """
    Get book by id
    """
    book = Book(id=book_id)
    await book.match_first()
    return {
        k: v for k, v in book.__dict__.items() if k in ("id", "title", "author", "sentences_count")
    }


async def get_sentences(word_id) -> list[dict]:
    """
    For the word get sentences where this occurred.
    """
    books = defaultdict(dict)
    async for row in Word(id=word_id).get_sentences():
        sentence_book_id = f"{row[1].id}"
        books[sentence_book_id] = row[1]
        if hasattr(books[sentence_book_id], "sentences_list"):
            books[sentence_book_id].sentences_list.append(row[0])
        else:
            books[sentence_book_id].sentences_list = [row[0]]

    return list(books.values())


async def get_sentences_by_book(book_id, flashcard_id) -> list[dict]:
    """
    For the book and flashcard get sentences.
    """
    flashcard = Flashcard(id=flashcard_id)
    await flashcard.match_first()
    return [row async for row in flashcard.get_sentences(book_id)]


async def get_all_flashcards(book_id) -> list[dict]:
    """
    Get list of flashcard ids
    """
    user = User(username="jkowalski")
    await user.match_first()

    flashcard_ids = {}
    async for sf in Flashcard.get_ids_for_book(book_id, user.id):
        if sf.flashcard_id in flashcard_ids:
            flashcard_ids[sf.flashcard_id]["sentence_ids"].append(sf.sentence_id)
        else:
            flashcard_ids[sf.flashcard_id] = {
                "id": sf.id,
                "flashcard_id": sf.flashcard_id,
                "nr": sf.nr,
                "sentence_ids": [sf.sentence_id],
            }

    return list(flashcard_ids.values())


async def get_flashcard(flashcard_id) -> dict:
    """
    Get one flashcard
    """
    flashcard = Flashcard(id=flashcard_id)
    await flashcard.match_first()
    response = {
        "id": flashcard.id,
        "key_word": flashcard.key_word,
        "translations": flashcard.translations,
        "words": [],
    }
    async for word in flashcard.get_words():
        response["words"].append({
            "id": word.id,
            "lem": word.lem,
            "declination": word.declination,
            "definition": word.definition,
        })
    return response


async def get_sentence(sentence_id) -> dict:
    """
    Get one sentence
    """
    sentence = Sentence(id=sentence_id)
    await sentence.match_first()
    return {
        "id": sentence.id,
        "nr": sentence.nr,
        "sentence": sentence.sentence,
    }


async def get_word(word_id: int) -> dict:
    """
    Get one word
    """
    word = Word(id=word_id)
    await word.match_first()
    return {
        "id": word.id,
        "lem": word.lem,
        "declination": word.declination,
        "definition": word.definition,
        "count": word.count,
    }
