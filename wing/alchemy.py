from pathlib import Path
import configparser
from sqlalchemy import create_engine

PROJECT_PATH = Path(__file__).parents[1]

config_ini_file = PROJECT_PATH.joinpath("alembic.ini")

config = configparser.ConfigParser()
config.read(config_ini_file)

sqlalchemy_url = config["alembic"]["sqlalchemy.url"]

engine = create_engine(sqlalchemy_url, echo=False)
