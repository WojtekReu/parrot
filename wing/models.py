from typing import List, Generator, Optional
from sqlalchemy import ForeignKey, JSON, select, String, update
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from sqlalchemy.sql.expression import func

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
        table_name = self.__mapper__.local_table.description
        self.table = self.__mapper__.local_table

        self.fns_where = []
        self.column_names = []
        for column in self.metadata.tables[table_name].columns:
            self.column_names.append(column.description)
            value = getattr(self, column.description)
            if value:
                fn_where = lambda x, y: x == y
                self.fns_where.append(fn_where(column, value))

    @classmethod
    def all(cls) -> Generator:
        """
        Get all objects
        """
        stmt = select(cls)
        with Session(engine) as s:
            for instance_tuple in s.execute(stmt).all():
                yield instance_tuple[0]

    def match_first(self):
        """
        Set all model attributes when matched object found
        """
        self._set()
        stmt = select(self.table).where(*self.fns_where)

        with Session(engine) as s:
            result = s.execute(stmt).first()
            if result:
                for column_name, value in zip(self.column_names, result):
                    setattr(self, column_name, value)

    def save(self):
        """
        Add or merge object
        """
        with Session(engine) as s:
            if self.id:
                s.merge(self)
            else:
                s.add(self)
            s.commit()
            return self.id

    def save_if_not_exists(self):
        """
        Save object if not exists in DB
        """
        self.match_first()
        if not self.id:
            self.save()

    @classmethod
    def newer_than(cls, obj_id):
        """
        Find objects which ID is larger than give ID
        """
        stmt = select(cls).where(cls.id > obj_id)
        with Session(engine) as s:
            for instance_tuple in s.execute(stmt).all():
                yield instance_tuple[0]

    @classmethod
    def get_max_id(cls) -> int:
        """
        Return max id or 0 for `id` column in the model
        """
        stmt = select(func.max(cls.id))
        with Session(engine) as s:
            row = s.execute(stmt).first()
            return row[0] if row else 0


class Book(Base):
    """
    Books to read
    """
    __tablename__ = "book"

    title: Mapped[str] = mapped_column(String(50))
    author: Mapped[str] = mapped_column(String(50))
    path: Mapped[str | None] = mapped_column(String(100), default=None)
    sentences: Mapped[List["Sentence"]] = relationship(back_populates="book")
    bookwords: Mapped[List["BookWord"]] = relationship(back_populates="book")
    contexts: Mapped[List["Context"]] = relationship(back_populates="book")

    def __repr__(self):
        return f"<Book {self.id}: {self.title} - {self.author}>"


class Sentence(Base):
    """
    Sentences to learn.
    """
    __tablename__ = "sentence"

    text: Mapped[str]
    book_id = mapped_column(ForeignKey("book.id"))
    order: Mapped[int]
    book: Mapped["Book"] = relationship(back_populates="sentences")
    translations: Mapped[list] = mapped_column(JSON)
    wordsentences: Mapped[List["WordSentence"]] = relationship(back_populates="sentence")

    def __repr__(self) -> str:
        return f"<Sentence {self.id}: {self.text[:20]}>"

    @classmethod
    def get_by_book(cls, book_id: int) -> Generator:
        """
        Get sentences ordered by occurrence in text.
        """
        stmt = select(cls).where(cls.book_id == book_id).order_by(cls.order)
        with Session(engine) as s:
            for sentence_tuple in s.execute(stmt).all():
                yield sentence_tuple[0]

    @classmethod
    def get_by_word(cls, word_id: int) -> Generator:
        """
        Get sentences ordered by book_id next by occurrence in text.
        """
        stmt = (
            select(cls)
            .where(
                cls.id == WordSentence.sentence_id,
                WordSentence.word_id == word_id,
            )
            .order_by(
                cls.book_id,
                cls.order,
            )
        )
        with Session(engine) as s:
            for sentence_tuple in s.execute(stmt).all():
                yield sentence_tuple[0]


class BookWord(Base):
    """
    Book and Work relation with order by occurrence in book.
    """
    __tablename__ = "book_word"

    book_id: Mapped[int] = mapped_column(ForeignKey("book.id"))
    word_id: Mapped[int] = mapped_column(ForeignKey("word.id"))
    order: Mapped[int]
    book: Mapped["Book"] = relationship(back_populates="bookwords")
    word: Mapped["Word"] = relationship(back_populates="bookwords")


class Word(Base):
    """
    Words to learn
    """
    __tablename__ = "word"

    key_word: Mapped[str] = mapped_column(String(40))
    translations: Mapped[list] = mapped_column(JSON)
    bookwords: Mapped[List["BookWord"]] = relationship(back_populates="word")
    wordsentences: Mapped[List["WordSentence"]] = relationship(back_populates="word")
    contexts: Mapped[List["Context"]] = relationship(back_populates="word")

    def __repr__(self) -> str:
        return f"<Word {self.id}: {self.key_word}>"

    @classmethod
    def get_by_book(cls, book_id: int) -> Generator:
        stmt = (
            select(cls)
            .join(BookWord)
            .add_columns(BookWord.order)
            .where(BookWord.book_id == book_id)
            .order_by(BookWord.order)
        )
        with Session(engine) as s:
            for word_tuple in s.execute(stmt).all():
                word = word_tuple[0]
                word.order = word_tuple[1]
                yield word

    @classmethod
    def get_by_key_word(cls, key_word) -> Optional[tuple]:
        stmt = (
            select(cls)
            .where(cls.key_word == key_word)
        )
        with Session(engine) as s:
            return s.execute(stmt).first()


class WordSentence(Base):
    """
    Word Sentence relation
    """
    __tablename__ = "word_sentence"

    word_id: Mapped[int] = mapped_column(ForeignKey("word.id"))
    sentence_id: Mapped[int] = mapped_column(ForeignKey("sentence.id"))
    word: Mapped["Word"] = relationship(back_populates="wordsentences")
    sentence: Mapped["Sentence"] = relationship(back_populates="wordsentences")


class Context(Base):
    """
    Sentences with key_word obtained by parsing book.
    """
    __tablename__ = "context"

    content: Mapped[str] = mapped_column(String(255))
    book_id: Mapped[int] = mapped_column(ForeignKey("book.id"))
    word_id: Mapped[int] = mapped_column(ForeignKey("word.id"))
    book: Mapped["Book"] = relationship(back_populates="contexts")
    word: Mapped["Word"] = relationship(back_populates="contexts")

    def __repr__(self) -> str:
        return f"<Context {self.id}: {self.content[:20]}>"

    @classmethod
    def get_by_word(cls, word_id: int) -> Generator:
        stmt = (
            select(cls)
            .where(cls.word_id == word_id)
        )
        with Session(engine) as s:
            for context_tuple in s.execute(stmt).all():
                yield context_tuple[0]


class ParrotSettings(Base):
    """
    Dynamic global settings for parrot project.
    """
    __tablename__ = "parrot_settings"
    last_word_id: Mapped[int] = mapped_column(default=0, nullable=False)

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


def max_order_for_book_id(book_id: int) -> int:
    """
    Return max order value for BookWord and Sentence models.
    """
    stmt = select(func.max(BookWord.order)).where(BookWord.book_id == book_id)
    with Session(engine) as s:
        row = s.execute(stmt).first()
        wb_max = row[0] if row else 0

    stmt = select(func.max(Sentence.order)).where(Sentence.book_id == book_id)
    with Session(engine) as s:
        row = s.execute(stmt).first()
        s_max = row[0] if row else 0

    return max(wb_max, s_max)
