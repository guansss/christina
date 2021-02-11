from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic.json import ENCODERS_BY_TYPE
from datetime import datetime
from christina import utils
import os

SQLALCHEMY_DATABASE_URL = os.environ['DB_URL']

# override the default datetime encoder to return a numeric timestamp
ENCODERS_BY_TYPE[datetime] = utils.timestamp

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
