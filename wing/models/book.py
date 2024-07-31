from sqlmodel import Field, Relationship, SQLModel

from .base import Base
from .user import User


class BookCreate(SQLModel):
    title: str = Field(nullable=False)
    author: str = Field(nullable=False)
    is_public: bool = Field(default=False, nullable=False)


class BookUpdate(BookCreate):
    ...


class BookBase(BookCreate):
    user_id: int = Field(foreign_key="user.id")
    sentences_count: int = Field(default=0, nullable=False)
    words_count: int = Field(default=0, nullable=False)


class BookFind(BookBase):
    title: str | None = None
    author: str | None = None
    user_id: int | None = None


class Book(Base, BookBase, table=True):
    __tablename__ = "book"

    user: User = Relationship(back_populates="books")
    sentences: list["Sentence"] = Relationship(back_populates="book")
