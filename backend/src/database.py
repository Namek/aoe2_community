from dictalchemy import DictableModel
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from . import cfg

# e.g. "sqlite:///./sql_app.db"
SQLALCHEMY_DATABASE_URL = "sqlite:///" + cfg.DB_PATH

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
