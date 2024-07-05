from typing import Any

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    VERSION: str = Field("0.0.1")
    PROJECT_NAME: str = Field("Flashcards for books")
    POSTGRES_USER: str = Field("postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field("postgres", env="POSTGRES_PASSWORD")
    POSTGRES_DBNAME: str = Field("postgres", env="POSTGRES_DBNAME")
    POSTGRES_HOST: str = Field("localhost", env="POSTGRES_HOST")
    POSTGRES_PORT: int | str = Field("5432", env="POSTGRES_PORT")
    POSTGRES_ECHO: bool = Field(False, env="POSTGRES_ECHO")
    POSTGRES_POOL_SIZE: int = Field(10, env="POSTGRES_POOL_SIZE")
    ASYNC_POSTGRES_URI: PostgresDsn | None = None
    # configs for external tools:
    # Url to pons dictionary API
    API_URL: str = Field("https://api.pons.com/v1/dictionary", env="API_URL")
    # To obtain access to PONS API go to https://en.pons.com/p/online-dictionary/developers/api
    # register using your name and email. Then get key from
    # https://en.pons.com/open_dict/public_api/secret
    # Secret key for PONS dictionary
    PONS_SECRET_KEY: str = Field("", env="PONS_SECRET_KEY")
    API_LOGS_PATH: str = Field("pons_api.log", env="API_LOGS_PATH")
    NLTK_DATA_PREFIX: str = Field("/usr/local/share/nltk_data", env="NLTK_DATA_PREFIX")

def assemble_db_connection(v: str | None = None, values: dict[str, Any] = None) -> Any:
    if isinstance(v, str):
        return v

    return PostgresDsn.build(
        scheme="postgresql+asyncpg",
        username=values.get("POSTGRES_USER"),
        password=values.get("POSTGRES_PASSWORD"),
        host=values.get("POSTGRES_HOST"),
        port=int(values.get("POSTGRES_PORT")),
        path=values.get("POSTGRES_DBNAME"),
    )


settings = Settings()
settings.ASYNC_POSTGRES_URI = assemble_db_connection(values=settings.dict())
