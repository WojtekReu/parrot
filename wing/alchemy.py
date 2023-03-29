from pathlib import Path
import configparser
from sqlalchemy import create_engine

config_ini_file = Path("/home/orkan/projekty/parrot/alembic.ini")

config = configparser.ConfigParser()
config.read(config_ini_file)

sqlalchemy_url = config["alembic"]["sqlalchemy.url"]

engine = create_engine(sqlalchemy_url, echo=False)
