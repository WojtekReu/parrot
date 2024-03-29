from sqlmodel import Field, SQLModel, Relationship

from .base import Base
from .book import Book


class SentenceBase(SQLModel):
    nr: int = Field(nullable=False)
    book_id: int = Field(foreign_key="book.id")
    sentence: str = Field(nullable=False)


class SentenceCreate(SentenceBase):
    nr: int = None
    book_id: int = None
    sentence: str = None


class Sentence(Base, SentenceBase, table=True):
    __tablename__ = "sentence"

    book: Book = Relationship(back_populates="sentences")
    sentence_flashcards: list["SentenceFlashcard"] = Relationship(back_populates="sentence")
    sentence_words: list["SentenceWord"] = Relationship(back_populates="sentence")
