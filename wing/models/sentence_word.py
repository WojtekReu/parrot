from sqlmodel import Field, SQLModel, Relationship

from .base import Base
from .sentence import Sentence
from .word import Word


class SentenceWord(Base, SQLModel, table=True):
    __tablename__ = "sentence_word"

    sentence_id: int = Field(foreign_key="sentence.id")
    word_id: int = Field(foreign_key="word.id")

    sentence: Sentence = Relationship(back_populates="sentence_words")
    word: Word = Relationship(back_populates="sentence_words")
