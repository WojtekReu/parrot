from pydantic import EmailStr
from sqlmodel import AutoString, Field, Relationship, SQLModel

from .base import Base


class UserBase(SQLModel):
    username: str = Field(
        nullable=False,
        index=True,
        sa_column_kwargs={"unique": True},
    )
    password: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr = Field(
        nullable=False,
        index=True,
        sa_column_kwargs={"unique": True},
        sa_type=AutoString,
    )
    is_active: bool = True


class UserCreate(UserBase):
    username: str = None
    password: str = None
    email: EmailStr = None


class UserUpdate(UserBase):
    first_name: str = None
    last_name: str = None


class User(Base, UserBase, table=True):
    __tablename__ = "user"

    flashcards: list["Flashcard"] = Relationship(back_populates="user")
