from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel, Relationship

from .base import Base
from .book import Book
from .user import User


class CurrentlyReading(Base, SQLModel, table=True):
    __tablename__ = "currently_reading"
    __table_args__ = (UniqueConstraint("user_id", "book_id"),)

    user_id: int = Field(foreign_key="user.id")
    book_id: int = Field(foreign_key="book.id")

    user: User = Relationship(back_populates="currently_readings")
    book: Book = Relationship(back_populates="currently_readings")
