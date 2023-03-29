from typing import List
from sqlalchemy import ForeignKey, JSON, select, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session

from .alchemy import engine


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)

    def find_first(self):
        table_name = self.__mapper__.local_table.description
        table = self.__mapper__.local_table

        fns_where = []
        column_names = []
        for column in self.metadata.tables[table_name].columns:
            column_names.append(column.description)
            value = getattr(self, column.description)
            if value:
                fn_where = lambda x, y: x == y
                fns_where.append(fn_where(column, value))

        stmt = select(table).where(*fns_where)

        with Session(engine) as s:
            results = s.execute(stmt).all()
            if results:
                first = results[0]
                for column_name, value in zip(column_names, first):
                    setattr(self, column_name, value)

    def save(self):
        with Session(engine) as s:
            if self.id:
                s.merge(self)
            else:
                s.add(self)
            s.commit()
            return self.id


class Book(Base):
    __tablename__ = "book"

    title: Mapped[str] = mapped_column(String(50))
    author: Mapped[str] = mapped_column(String(50))
    sentences: Mapped[List["Sentence"]] = relationship(back_populates="book")
    bookwords: Mapped[List["BookWord"]] = relationship(back_populates="book")

    def __repr__(self):
        return f"<{self.id}: {self.title} - {self.author}>"

    @classmethod
    def get_all(cls):
        stmt = select(cls)
        with Session(engine) as s:
            return s.execute(stmt).all()


class Sentence(Base):
    __tablename__ = "sentence"

    text: Mapped[str]
    book_id = mapped_column(ForeignKey("book.id"))
    order: Mapped[int]
    book: Mapped["Book"] = relationship(back_populates="sentences")
    translations: Mapped[list] = mapped_column(JSON)

    def __repr__(self) -> str:
        return f"<{self.id}: {self.text[:20]}>"

    @classmethod
    def get_by_book(cls, book_id):
        stmt = select(cls).where(cls.book_id == book_id).order_by(cls.order)
        with Session(engine) as s:
            return s.execute(stmt).all()


class BookWord(Base):
    __tablename__ = "book_word"

    book_id: Mapped[int] = mapped_column(ForeignKey("book.id"))
    word_id: Mapped[int] = mapped_column(ForeignKey("word.id"))
    order: Mapped[int]
    book: Mapped["Book"] = relationship(back_populates="bookwords")
    word: Mapped["Word"] = relationship(back_populates="bookwords")


class Word(Base):
    __tablename__ = "word"

    key_word: Mapped[str] = mapped_column(String(40))
    translations: Mapped[list] = mapped_column(JSON)
    bookwords: Mapped[List["BookWord"]] = relationship(back_populates="word")

    def __repr__(self) -> str:
        return f"<{self.id}: {self.key_word}>"

    @classmethod
    def get_by_book(cls, book_id):
        stmt = (
            select(cls)
            .join(BookWord)
            .add_columns(BookWord.order)
            .where(BookWord.book_id == book_id)
            .order_by(BookWord.order)
        )
        with Session(engine) as s:
            return s.execute(stmt).all()
