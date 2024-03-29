from sqlmodel import Field, SQLModel, Relationship

from .base import Base


class BookBase(SQLModel):
    title: str = Field(nullable=False)
    author: str = Field(nullable=False)
    sentences_count: int = Field(default=0, nullable=False)
    words_count: int = Field(default=0, nullable=False)


class BookCreate(BookBase):
    title: str = None
    author: str = None


class BookUpdate(BookBase):
    ...


class Book(Base, BookBase, table=True):
    __tablename__ = "book"

    sentences: list["Sentence"] = Relationship(back_populates="book")
