from sqlmodel import SQLModel


class TokenData(SQLModel):
    username: str | None = None


class Status(SQLModel):
    message: str
