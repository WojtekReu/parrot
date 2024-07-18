from sqlmodel import Field, SQLModel, TEXT

from .base import Base


class TranslationBase(SQLModel):
    word: str = Field(max_length=60)
    definition: str = Field(TEXT)


class Translation(Base, TranslationBase, table=True):
    __tablename__ = "translation"
