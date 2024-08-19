from sqlmodel import SQLModel


class TokenData(SQLModel):
    user_id: int


class Status(SQLModel):
    message: str
