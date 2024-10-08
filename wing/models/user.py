from pydantic import EmailStr
from sqlmodel import AutoString, Field, Relationship, SQLModel

from .base import Base


class UserBase(SQLModel):
    username: str = Field(
        nullable=False,
        index=True,
        sa_column_kwargs={"unique": True},
    )
    first_name: str | None = None
    last_name: str | None = None


class UserUpdate(UserBase):
    ...

class UserPublic(UserBase):
    id: int


class UserRestricted(UserPublic):
    email: EmailStr = Field(
        nullable=False,
        index=True,
        sa_column_kwargs={"unique": True},
        sa_type=AutoString,
    )
    is_active: bool = True


class UserDb(UserRestricted):
    password: str


class UserCreate(UserBase):
    password: str
    email: EmailStr
    is_active: bool = True


class UserFind(UserBase):
    username: str | None = None
    password: None = None
    email: EmailStr | None = None
    is_active: bool | None = None


class User(Base, UserDb, table=True):
    __tablename__ = "user"

    flashcards: list["Flashcard"] = Relationship(back_populates="user")
    books: list["Book"] = Relationship(back_populates="user")
    currently_readings: list["CurrentlyReading"] = Relationship(back_populates="user")
