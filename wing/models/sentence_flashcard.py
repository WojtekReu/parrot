from sqlmodel import Field, SQLModel, Relationship

from .base import Base
from .sentence import Sentence
from .flashcard import Flashcard


class SentenceFlashcard(Base, SQLModel, table=True):
    __tablename__ = "sentence_flashcard"

    sentence_id: int = Field(foreign_key="sentence.id")
    flashcard_id: int = Field(foreign_key="flashcard.id")

    sentence: Sentence = Relationship(back_populates="sentence_flashcards")
    flashcard: Flashcard = Relationship(back_populates="sentence_flashcards")
