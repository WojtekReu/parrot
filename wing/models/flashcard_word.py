from sqlmodel import Field, SQLModel, Relationship

from .base import Base
from .flashcard import Flashcard
from .word import Word


class FlashcardWord(Base, SQLModel, table=True):
    __tablename__ = "flashcard_word"

    flashcard_id: int = Field(foreign_key="flashcard.id")
    word_id: int = Field(foreign_key="word.id")

    flashcard: Flashcard = Relationship(back_populates="flashcard_words")
    word: Word = Relationship(back_populates="flashcard_words")
