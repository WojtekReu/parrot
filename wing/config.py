import logging
from pathlib import Path
from typing import Any

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

DOTENV_FILE = Path(".env")  # .env file in main project directory: parrot/.env


class Settings(BaseSettings):
    VERSION: str = Field("0.0.3")
    PROJECT_NAME: str = Field("Flashcards for books")
    # API should use subdomain for PROJECT_DOMAIN ex. for example.com API should be api.example.com
    PROJECT_DOMAIN: str = Field("localhost", env="PROJECT_DOMAIN")
    # This is for development environment, ex. localhost:8000
    PROJECT_DOMAIN_PORT: int | None = Field(None, env="PROJECT_DOMAIN_PORT")
    ENVIRONMENT_TYPE: str = Field("dev", env="ENVIRONMENT_TYPE")
    SSL_ENABLED: bool = Field(False, env="SSL_ENABLED")
    SECRET_KEY: str | None = Field(None, env="SECRET_KEY")
    POSTGRES_USER: str = Field("postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field("postgres", env="POSTGRES_PASSWORD")
    POSTGRES_DBNAME: str = Field("postgres", env="POSTGRES_DBNAME")
    POSTGRES_HOST: str = Field("parrot-db-1", env="POSTGRES_HOST")
    POSTGRES_PORT: int | str = Field("5432", env="POSTGRES_PORT")
    POSTGRES_ECHO: bool = Field(False, env="POSTGRES_ECHO")
    POSTGRES_POOL_SIZE: int = Field(10, env="POSTGRES_POOL_SIZE")
    POSTGRES_URI: str = Field("", env="POSTGRES_URI")
    ASYNC_POSTGRES_URI: PostgresDsn | None = None

    # minutes after which the user will be logged out
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(1440, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # configs for external tools:
    # Url to pons dictionary API
    API_URL: str = Field("https://api.pons.com/v1/dictionary", env="API_URL")
    # To obtain access to PONS API go to https://en.pons.com/p/online-dictionary/developers/api
    # register using your name and email. Then get key from
    # https://en.pons.com/open_dict/public_api/secret
    # Secret key for PONS dictionary
    PONS_SECRET_KEY: str = Field("", env="PONS_SECRET_KEY")
    API_LOGS_PATH: str = Field("pons_api.log", env="API_LOGS_PATH")

    # NLTK storage directory path configuration
    NLTK_DATA_PREFIX: str = Field("/usr/local/share/nltk_data", env="NLTK_DATA_PREFIX")

    # Configuration vocabulary container
    VOCABULARY_HOST: str = Field("parrot-vocabulary-1", env="VOCABULARY_HOST")
    VOCABULARY_PORT: int = Field(2630, env="VOCABULARY_PORT")
    VOCABULARY_BASE: str = Field("../../data/vocabulary.pkl", env="VOCABULARY_BASE")
    VOCABULARY_CONNECTIONS_NUMBER: int = Field(1, env="VOCABULARY_CONNECTIONS_NUMBER")

    # setting dictionary English to Polish, unix command: dict -D
    DICTIONARY_HOST: str = Field("parrot-dict-1", env="DICTIONARY_HOST")
    DICTIONARY_PORT: int = Field(2628, env="DICTIONARY_PORT")
    DICTIONARY_VOCABULARY: str = "fd-eng-pol"
    DICTIONARY_DEFINITION_KEY: str = "definition"

    LOGGING_LEVEL: int = logging.INFO
    model_config = SettingsConfigDict(env_file=DOTENV_FILE)


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
if settings.POSTGRES_URI:
    settings.ASYNC_POSTGRES_URI = assemble_db_connection(v=settings.POSTGRES_URI)
else:
    settings.ASYNC_POSTGRES_URI = assemble_db_connection(values=settings.dict())

import nltk
nltk.data.path.append(settings.NLTK_DATA_PREFIX)
