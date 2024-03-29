from sqlmodel import Field, SQLModel


class Base(SQLModel):
    id: int = Field(
        primary_key=True,
        index=True,
        nullable=True,
    )
