from sqlmodel import Column, Field, Relationship, SQLModel
from sqlalchemy import JSON

from .base import Base


class WordBase(SQLModel):
    count: int = Field(default=0, nullable=False)
    pos: str = Field(default=None, nullable=True, max_length=1)
    lem: str = Field(nullable=False, max_length=30)
    declination: dict = Field(default_factory=dict, sa_column=Column(JSON))
    definition: str = Field(nullable=True)
    synset: str = Field(default=None, nullable=True, max_length=35)


class WordCreate(WordBase):
    pos: str = Field(nullable=False)
    definition: str | None = None


class WordUpdate(WordBase):
    pos: str | None = None
    lem: str | None = None
    definition: str | None = None


class WordFind(WordBase):
    pos: str = None
    lem: str = None
    declination: dict = {}
    definition: str = None


class Word(Base, WordBase, table=True):
    __tablename__ = "word"

    flashcard_words: list["FlashcardWord"] = Relationship(back_populates="word")
    sentence_words: list["SentenceWord"] = Relationship(back_populates="word")
