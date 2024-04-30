from sqlmodel import Column, Field, Relationship, SQLModel
from sqlalchemy import JSON

from .base import Base
from .user import User


class FlashcardBase(SQLModel):
    user_id: int = Field(foreign_key="user.id")
    keyword: str = Field(nullable=False)
    translations: list = Field(default_factory=list, sa_column=Column(JSON))


class FlashcardCreate(FlashcardBase):
    user_id: int = None
    keyword: str = None
    translations: list = []


class FlashcardUpdate(FlashcardBase):
    user_id: int = None
    keyword: str = None
    translations: list = []


class FlashcardFind(FlashcardBase):
    user_id: int = None
    keyword: str = None
    translations: list = []


class Flashcard(Base, FlashcardBase, table=True):
    __tablename__ = "flashcard"

    user: User = Relationship(back_populates="flashcards")
    sentence_flashcards: list["SentenceFlashcard"] = Relationship(back_populates="flashcard")
    flashcard_words: list["FlashcardWord"] = Relationship(back_populates="flashcard")
