import os
from contextlib import contextmanager
from datetime import datetime

from pydantic.json import ENCODERS_BY_TYPE
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from christina import utils

SQLALCHEMY_DATABASE_URL = os.environ['DB_URL']

# override the default datetime encoder to return a numeric timestamp
ENCODERS_BY_TYPE[datetime] = utils.timestamp

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={
        # may need to wait a while for a spun-down HDD to warm up (~6 sec)
        # or an Aria2 RPC request to respond (~10 sec)
        'timeout': 30,
        "check_same_thread": False,
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()


get_db_ctx = contextmanager(get_db)


class RecordNotFound(Exception):
    pass


class RecordExists(Exception):
    pass
