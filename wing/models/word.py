from sqlmodel import Column, Field, Relationship, SQLModel
from sqlalchemy import JSON

from .base import Base


class WordBase(SQLModel):
    count: int = Field(default=0, nullable=False)
    pos: str = Field(default=None, nullable=True)
    lem: str = Field(nullable=False)
    declination: dict = Field(default_factory=dict, sa_column=Column(JSON))
    definition: str = Field(nullable=True)


class WordCreate(WordBase):
    count: int = 0
    pos: str = None
    lem: str = None
    declination: dict = {}
    definition: str | None = None


class WordUpdate(WordBase):
    count: int | None = None
    lem: str | None = None
    declination: dict = {}
    definition: str | None = None


class Word(Base, WordBase, table=True):
    __tablename__ = "word"

    flashcard_words: list["FlashcardWord"] = Relationship(back_populates="word")
    sentence_words: list["SentenceWord"] = Relationship(back_populates="word")
