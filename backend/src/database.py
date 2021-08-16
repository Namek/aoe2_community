from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session as DbSession
from typing import Generator

from . import cfg

# e.g. "sqlite:///./sql_app.db"
SQLALCHEMY_DATABASE_URL = "sqlite:///" + cfg.DB_PATH

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

@contextmanager
def get_db() -> Generator[DbSession, None, None]:
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

# version of get_db() without the contextmanager, needed for FastAPI
def web_db() -> Generator[DbSession, None, None]:
    with get_db() as db:
        yield db