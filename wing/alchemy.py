import os
from pathlib import Path
import configparser
from sqlalchemy.ext.asyncio import create_async_engine

#
# Alembic configuration
#

PROJECT_PATH = Path(__file__).parents[1]

config_ini_file = PROJECT_PATH.joinpath("alembic.ini")

config = configparser.ConfigParser()
config.read(config_ini_file)

sqlalchemy_url = config["alembic"]["sqlalchemy.url"]

#
# Parrot project configuration
#

engine = create_async_engine(sqlalchemy_url, echo=False)

# File book_list.csv contains 4 columns: translations.csv;title;author;path_to_book.
BOOKS_PATH = PROJECT_PATH.joinpath("data", "book_list.csv")

# Logs file
API_LOGS_PATH = PROJECT_PATH.joinpath("data", "pons_api.log")

# To obtain access to PONS API go to https://en.pons.com/p/online-dictionary/developers/api
# register using your name and email. Then get key from
# https://en.pons.com/open_dict/public_api/secret
# Secret key for PONS dictionary
PONS_SECRET_KEY = os.environ.get("PONS_SECRET_KEY", '')

# Url to pons dictionary API
API_URL = "https://api.pons.com/v1/dictionary"

# Directory where nltk data is stored
NLTK_DATA_PREFIX = Path("/usr/local/share/nltk_data")

# Pronouns list file
PRONOUNS_FILE = NLTK_DATA_PREFIX.joinpath("corpora", "dolch", "pronouns")

# Prepositions list file
PREPOSITIONS_FILE = NLTK_DATA_PREFIX.joinpath("corpora", "dolch", "prepositions")

# Adverbs list file
ADVERBS_FILE = NLTK_DATA_PREFIX.joinpath("corpora", "dolch", "adverbs")
