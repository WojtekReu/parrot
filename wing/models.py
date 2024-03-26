from typing import AsyncIterable, Generator, List, Self
from sqlalchemy import ForeignKey, JSON, select, String, update, Text, distinct, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import func
from sqlalchemy.ext.asyncio import AsyncSession as Session
from .alchemy import engine

PARROT_SETTINGS_ID = 1


class Base(DeclarativeBase):
    """
    Abstract class for Model
    """

    id: Mapped[int] = mapped_column(primary_key=True)

    def _set(self):
        """
        Set attributes from object to model
        """
        self.fns_where = []
        for column in self.__table__.columns:
            value = getattr(self, column.description)
            if value:
                fn_where = lambda x, y: x == y
                self.fns_where.append(fn_where(column, value))

    @classmethod
    async def all(cls) -> AsyncIterable:
        """
        Get all objects
        """
        stmt = select(cls).order_by(cls.id)
        async with Session(engine) as s:
            for instance_tuple in (await s.execute(stmt)).all():
                yield instance_tuple[0]

    async def match_first(self) -> None:
        """
        Set all model attributes when matched object found
        """
        self._set()
        stmt = select(self.__table__).where(*self.fns_where)

        async with Session(engine) as s:
            row = (await s.execute(stmt)).first()
            if row:
                for column, value in zip(self.__table__.columns, row):
                    setattr(self, column.description, value)

    async def save(self) -> Self:
        """
        Add or merge object
        """
        async with Session(engine, expire_on_commit=False) as s:
            if self.id:
                await s.merge(self)
            else:
                s.add(self)
            await s.commit()
            return self

    async def save_if_not_exists(self) -> None:
        """
        Save object if not exists in DB
        """
        await self.match_first()
        if not self.id:
            await self.save()

    @classmethod
    async def newer_than(cls, obj_id) -> AsyncIterable[Generator]:
        """
        Find objects which ID is larger than give ID
        """
        stmt = select(cls).where(cls.id > obj_id)
        async with Session(engine) as s:
            for row in (await s.execute(stmt)).all():
                yield row[0]

    @classmethod
    async def get_max_id(cls) -> int:
        """
        Return max id or 0 for `id` column in the model
        """
        stmt = select(func.max(cls.id))
        async with Session(engine) as s:
            row = (await s.execute(stmt)).first()
            return row[0] if row else 0


class Book(Base):
    """
    Books to read
    """

    __tablename__ = "book"

    title: Mapped[str] = mapped_column(String(50))
    author: Mapped[str] = mapped_column(String(50))
    sentences_count: Mapped[int] = mapped_column(default=0)
    words_count: Mapped[int] = mapped_column(default=0, nullable=True)
    # relations
    sentences: Mapped[List["Sentence"]] = relationship(back_populates="book")

    def __repr__(self):
        return f"<Book {self.id}: {self.title} - {self.author}>"


class Sentence(Base):
    """
    All sentences in book ordered by nr
    """

    __tablename__ = "sentence"

    nr: Mapped[int]
    book_id: Mapped[int] = mapped_column(ForeignKey("book.id"))
    sentence: Mapped[str] = mapped_column(Text())
    # relations
    book: Mapped["Book"] = relationship(back_populates="sentences")
    sentence_flashcards: Mapped[List["SentenceFlashcard"]] = relationship(back_populates="sentence")
    sentence_words: Mapped[List["SentenceWord"]] = relationship(back_populates="sentence")

    def __repr__(self):
        return f"<Sentence({self.id}): nr={self.nr} `{self.sentence[:20]}`>"

    @classmethod
    async def count_sentences_for_book(cls, book_id) -> int:
        """
        Count all sentences for book_id
        """
        stmt = select(func.count()).where(cls.book_id == book_id)
        async with Session(engine) as s:
            return (await s.execute(stmt)).first()[0]

    @classmethod
    async def count_words_for_book(cls, book_id) -> int:
        """
        Count all words matched for book_id
        """
        stmt = (
            select(func.count(distinct(SentenceWord.word_id)))
            .select_from(cls)
            .join(SentenceWord)
            .where(cls.book_id == book_id)
        )
        async with Session(engine) as s:
            return (await s.execute(stmt)).first()[0]

    @classmethod
    async def get_sentences(cls, word, book_id=None):
        """
        Find all sentences contained the word
        """
        stmt = select(cls).where(cls.sentence.icontains(word)).order_by(cls.nr)
        if book_id:
            stmt = stmt.where(cls.book_id == book_id)
        async with Session(engine) as s:
            for row in (await s.execute(stmt)).all():
                yield row[0]


class Word(Base):
    """
    All wards in books.
    """

    __tablename__ = "word"

    count: Mapped[int] = mapped_column(default=0)
    pos: Mapped[str] = mapped_column(String(1), default=None, nullable=True)
    lem: Mapped[str] = mapped_column(String(255))
    declination: Mapped[list] = mapped_column(JSON, default=[])
    definition: Mapped[str] = mapped_column(String(255), nullable=True)
    # relations
    flashcard_words: Mapped[List["FlashcardWord"]] = relationship(back_populates="word")
    sentence_words: Mapped[List["SentenceWord"]] = relationship(back_populates="word")

    __table_args__ = (UniqueConstraint("pos", "lem", name="pos_lem_unique"),)

    def __repr__(self):
        return f"<Word({self.id}): {self.lem}, count={self.count}>"

    async def match_by_lem_pos(self) -> Self:
        """
        Return object when found
        """
        stmt = (
            select(Word)
            .where(self.__class__.lem == self.lem)
            .where(self.__class__.pos == self.pos)
        )
        async with Session(engine) as s:
            result = (await s.execute(stmt)).first()
            if result:
                return result[0]


    async def get_flashcards(self) -> AsyncIterable:
        """
        Get flashcards for this word
        """
        stmt = (
            select(Flashcard)
            .join(FlashcardWord)
            .where(FlashcardWord.word_id == self.id)
        )
        async with Session(engine) as s:
            for row in (await s.execute(stmt)).all():
                yield row[0]

    async def get_sentences(self, book_id=None) -> AsyncIterable:
        """
        Get all sentences for this word_id, relation is in SentenceWord
        """
        if self.id is None:
            raise ValueError("Can't select book_contents because bword.id is None.")
        stmt = (
            select(Sentence, Book)
            .join(SentenceWord)
            .where(SentenceWord.word_id == self.id)
            .where(Sentence.book_id == Book.id)
        )
        if book_id:
            stmt = stmt.where(Sentence.book_id == book_id).order_by(func.random())
        else:
            stmt = stmt.order_by(Sentence.book_id, Sentence.nr)

        async with Session(engine) as s:
            for row in (await s.execute(stmt)).all():
                yield row


class SentenceWord(Base):
    """
    Relations words and sentences
    """

    __tablename__ = "sentence_word"

    word_id: Mapped[int] = mapped_column(ForeignKey("word.id"))
    sentence_id: Mapped[int] = mapped_column(ForeignKey("sentence.id"))
    # relations
    word: Mapped["Word"] = relationship(back_populates="sentence_words")
    sentence: Mapped["Sentence"] = relationship(back_populates="sentence_words")

    def __repr__(self):
        return f"<SentenceWord({self.id}): w={self.word_id}, s={self.sentence_id}>"


class Flashcard(Base):
    """
    Words and phrases to learn
    """

    __tablename__ = "flashcard"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    key_word: Mapped[str] = mapped_column(String(200))
    translations: Mapped[list] = mapped_column(JSON, default=[])
    definition: Mapped[str] = mapped_column(String(255), nullable=True)
    # relations
    user: Mapped["User"] = relationship(back_populates="flashcards")
    sentence_flashcards: Mapped[List["SentenceFlashcard"]] = relationship(
        back_populates="flashcard"
    )
    flashcard_words: Mapped[List["FlashcardWord"]] = relationship(back_populates="flashcard")

    def __repr__(self) -> str:
        return f"<Flashcard {self.id}: {self.key_word[:30]}>"

    @classmethod
    async def get_ids_for_book(cls, book_id: int, user_id: int) -> AsyncIterable:
        """
        For book get all IDs (sentence_id and flashcard_id) ordered by sentence in book
        """
        stmt = (
            select(SentenceFlashcard)
            .join(Sentence)
            .join(cls)
            .add_columns(Sentence.nr)
            .where(cls.user_id == user_id)
            .where(Sentence.book_id == book_id)
        )
        async with Session(engine) as s:
            for row in (await s.execute(stmt)).all():
                result = row[0]
                result.nr = row[1]
                yield result

    async def get_words(self) -> AsyncIterable:
        """
        Get words related to this flashcard
        """
        stmt = (
            select(Word)
            .join(FlashcardWord)
            .where(FlashcardWord.flashcard_id == self.id)
        )
        async with Session(engine) as s:
            for row in (await s.execute(stmt)).all():
                yield row[0]

    async def get_sentences(self, book_id) -> AsyncIterable:
        """
        Get sentences for book_id related by sentence_flashcard
        """
        stmt = (
            select(Sentence)
            .join(SentenceFlashcard)
            .where(SentenceFlashcard.flashcard_id == self.id)
            .where(Sentence.book_id == book_id)
            .order_by(Sentence.nr)
        )
        async with Session(engine) as s:
            for row in (await s.execute(stmt)).all():
                yield row[0]


class SentenceFlashcard(Base):
    """
    Relation between Sentence and Flashcard
    """

    __tablename__ = "sentence_flashcard"

    sentence_id: Mapped[int] = mapped_column(ForeignKey("sentence.id"))
    flashcard_id: Mapped[int] = mapped_column(ForeignKey("flashcard.id"))
    # relations
    sentence: Mapped["Sentence"] = relationship(back_populates="sentence_flashcards")
    flashcard: Mapped["Flashcard"] = relationship(back_populates="sentence_flashcards")

    def __repr__(self):
        return f"<SentenceFlashcard({self.id}): s={self.sentence_id}, f={self.flashcard_id}>"


class FlashcardWord(Base):
    """
    Relationship between Flashcard and Word
    """

    __tablename__ = "flashcard_word"

    flashcard_id: Mapped[int] = mapped_column(ForeignKey("flashcard.id"))
    word_id: Mapped[int] = mapped_column(ForeignKey("word.id"))
    # relations
    flashcard: Mapped["Flashcard"] = relationship(back_populates="flashcard_words")
    word: Mapped["Word"] = relationship(back_populates="flashcard_words")

    def __repr__(self):
        return f"<FlashcardWord({self.id}): f={self.flashcard_id}, w={self.word_id}>"


class User(Base):
    """
    User
    """

    __tablename__ = "user"

    username: Mapped[str] = mapped_column(String(40), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    mail: Mapped[str] = mapped_column(String(255), unique=True)
    first_name: Mapped[str] = mapped_column(String(40))
    last_name: Mapped[str] = mapped_column(String(40))
    # relations
    flashcards: Mapped[List["Flashcard"]] = relationship(back_populates="user")


class ParrotSettings(Base):
    """
    Dynamic global settings for parrot project.
    """

    __tablename__ = "parrot_settings"
    last_word_id: Mapped[int] = mapped_column(default=0)
    last_sentence_id: Mapped[int] = mapped_column(default=0)

    @classmethod
    def get_last_word_id(cls) -> int:
        """
        Get max Word id from settings.
        """
        stmt = select(cls).where(cls.id == PARROT_SETTINGS_ID)
        with Session(engine) as s:
            row = s.execute(stmt).first()[0]
            return row.last_word_id

    @classmethod
    def update_last_settings_id(cls):
        """
        Get max id from Word model and save it to settings.
        """
        last_word_id = Word.get_max_id()
        with Session(engine) as s:
            stmt_update = (
                update(cls)
                .where(cls.id == PARROT_SETTINGS_ID)
                .values({"last_word_id": last_word_id})
            )
            s.execute(stmt_update)
            s.commit()
