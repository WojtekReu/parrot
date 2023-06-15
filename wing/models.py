from typing import AsyncIterable, Generator, List, Optional, Self
from sqlalchemy import ForeignKey, JSON, select, String, update
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

    @property
    def _column_names(self) -> Generator:
        """
        Generate column names for model
        """
        for column in self.metadata.tables[self.__tablename__].columns:
            yield column.name

    def _set(self):
        """
        Set attributes from object to model
        """
        table_name = self.__mapper__.local_table.description
        self.table = self.__mapper__.local_table

        self.fns_where = []
        for column in self.metadata.tables[table_name].columns:
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

    async def match_first(self):
        """
        Set all model attributes when matched object found
        """
        self._set()
        stmt = select(self.table).where(*self.fns_where)

        async with Session(engine) as s:
            row = (await s.execute(stmt)).first()
            if row:
                for column_name, value in zip(self._column_names, row):
                    setattr(self, column_name, value)

    async def save(self):
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
    sentences_count: Mapped[int | None] = mapped_column(default=None)
    sentences: Mapped[List["Sentence"]] = relationship(back_populates="book")
    bookwords: Mapped[List["BookWord"]] = relationship(back_populates="book")
    contexts: Mapped[List["Context"]] = relationship(back_populates="book")
    book_contents: Mapped[List["BookContent"]] = relationship(back_populates="book")
    book_translations: Mapped[List["BookTranslation"]] = relationship(back_populates="books")

    def __repr__(self):
        return f"<Book {self.id}: {self.title} - {self.author}>"


class BookTranslation(Base):
    """
    Relation translation to book with order occurrence
    """
    __tablename__ = "book_translation"

    order: Mapped[int]
    book_id: Mapped[int] = mapped_column(ForeignKey("book.id"))
    translation_id: Mapped[int] = mapped_column(ForeignKey("translation.id"))
    books: Mapped[List["Book"]] = relationship(back_populates="book_translations")
    translations: Mapped[List["Translation"]] = relationship(back_populates="book_translations")


class BookContent(Base):
    """
    Books content separated to sentences
    """
    __tablename__ = "book_content"

    nr: Mapped[int]
    book_id: Mapped[int] = mapped_column(ForeignKey("book.id"))
    sentence: Mapped[str] = mapped_column(String(1000))
    book: Mapped["Book"] = relationship(back_populates="book_contents")
    bword_book_contents: Mapped[List["BwordBookContent"]] = relationship(
        back_populates="book_contents",
    )

    @classmethod
    async def count_sentences_for_book(cls, book_id):
        stmt = select(func.count()).where(cls.book_id == book_id)
        async with Session(engine) as s:
            return (await s.execute(stmt)).first()[0]


class Bword(Base):
    """
    All wards in books.
    """
    __tablename__ = "bword"

    lem: Mapped[str] = mapped_column(String(255), default=None, nullable=True)
    declination: Mapped[list] = mapped_column(JSON)
    bword_book_contents: Mapped[List["BwordBookContent"]] = relationship(back_populates="bwords")
    translations: Mapped[List["Translation"]] = relationship(back_populates="bwords")
    count: Mapped[int | None] = mapped_column(default=0)

    async def save_for_lem(self):
        bword = self.find_lem()
        if bword:
            bword.declination = list(set(bword.declination + self.declination))
            if bword.count is None:
                bword.count = 1
            bword.count += self.count
            await bword.save()
            self.id = bword.id
        else:
            await self.save()

    async def find_lem(self) -> Optional[Self]:
        stmt = select(self.__class__).where(self.__class__.lem == self.lem)
        async with Session(engine) as s:
            row = (await s.execute(stmt)).first()
            if row:
                return row[0]


class BwordBookContent(Base):
    """
    Relations words and sentences
    """
    __tablename__ = "bword_book_content"

    bword_id: Mapped[int] = mapped_column(ForeignKey("bword.id"))
    book_content_id: Mapped[int] = mapped_column(ForeignKey("book_content.id"))
    bwords: Mapped[List["Bword"]] = relationship(back_populates="bword_book_contents")
    book_contents: Mapped[List["BookContent"]] = relationship(back_populates="bword_book_contents")


class Sentence(Base):
    """
    Sentences to learn.
    """
    __tablename__ = "sentence"

    text: Mapped[str] = mapped_column(String(1000))
    book_id = mapped_column(ForeignKey("book.id"))
    order: Mapped[int]
    book: Mapped["Book"] = relationship(back_populates="sentences")
    translation: Mapped[str] = mapped_column(String(1000), default=None, nullable=True)
    wordsentences: Mapped[List["WordSentence"]] = relationship(back_populates="sentence")

    def __repr__(self) -> str:
        return f"<Sentence {self.id}: {self.text[:20]}>"

    @classmethod
    async def get_by_book(cls, book_id: int) -> AsyncIterable:
        """
        Get sentences ordered by occurrence in text.
        """
        stmt = select(cls).where(cls.book_id == book_id).order_by(cls.order)
        async with Session(engine) as s:
            for sentence_tuple in (await s.execute(stmt)).all():
                yield sentence_tuple[0]

    @classmethod
    async def get_by_word(cls, word_id: int) -> Generator:
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
        async with Session(engine) as s:
            for sentence_tuple in (await s.execute(stmt)).all():
                yield sentence_tuple[0]


class BookWord(Base):
    """
    Book and Work relation with order by occurrence in book.
    """
    __tablename__ = "book_word"

    book_id: Mapped[int] = mapped_column(ForeignKey("book.id"))
    word_id: Mapped[int] = mapped_column(ForeignKey("word.id"))
    order: Mapped[int] = mapped_column(nullable=False)
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
    async def get_by_book(cls, book_id: int) -> Generator:
        stmt = (
            select(cls)
            .join(BookWord)
            .add_columns(BookWord.order)
            .where(BookWord.book_id == book_id)
            .order_by(BookWord.order)
        )
        async with Session(engine) as s:
            for word_tuple in (await s.execute(stmt)).all():
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
    async def get_by_word(cls, word_id: int) -> AsyncIterable:
        stmt = (
            select(cls)
            .where(cls.word_id == word_id)
        )
        async with Session(engine) as s:
            for context_tuple in (await s.execute(stmt)).all():
                yield context_tuple[0]


class Translation(Base):
    """
    Words to learn, each word may have many translations.
    """
    __tablename__ = "translation"

    bword_id: Mapped[int] = mapped_column(ForeignKey("bword.id"))
    source: Mapped[str] = mapped_column(String(100))
    text: Mapped[str] = mapped_column(String(100))
    sentences: Mapped[list] = mapped_column(JSON, default=None, nullable=True)
    book_contents: Mapped[list] = mapped_column(JSON, default=None, nullable=True)
    bwords: Mapped["Bword"] = relationship(back_populates="translations")
    book_translations: Mapped[List["BookTranslation"]] = relationship(
        back_populates="translations",
    )

    @classmethod
    async def get_by_book(cls, book_id: int) -> AsyncIterable:
        """
        Get all translations by book_id, relation is in BookTranslation
        """
        stmt = (
            select(cls)
            .join(BookTranslation)
            .add_columns(BookTranslation.order)
            .where(BookTranslation.book_id == book_id)
            .order_by(BookTranslation.order)
        )
        async with Session(engine) as s:
            for row in (await s.execute(stmt)).all():
                word = row[0]
                word.order = row[1]
                yield word

    async def get_book_contents(self):
        """
        Get all contents for this bword_id, relation is in BwordBookContent
        """
        stmt = (
            select(BookContent)
            .join(BwordBookContent)
            .where(BwordBookContent.bword_id == self.bword_id)
            .order_by(BookContent.nr)
        )
        async with Session(engine) as s:
            for row in (await s.execute(stmt)).all():
                yield row[0]


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


async def max_order_for_book_id(book_id: int) -> int:
    """
    Return max order value for BookWord and Sentence models.
    """
    stmt = select(func.max(BookWord.order)).where(BookWord.book_id == book_id)
    async with Session(engine) as s:
        row = (await s.execute(stmt)).first()
        wb_max = row[0] if row[0] else 0

    stmt = select(func.max(Sentence.order)).where(Sentence.book_id == book_id)
    async with Session(engine) as s:
        row = (await s.execute(stmt)).first()
        s_max = row[0] if row[0] else 0

    return max(wb_max, s_max)
