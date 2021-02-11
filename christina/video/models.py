from sqlalchemy import Column, Integer, String, Enum, DateTime
from christina.db import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum('i'))
    src_id = Column(String)
    url = Column(String)
    file = Column(String)

    title = Column(String)
    author_id = Column(String)
    thumb_url = Column(String)
    thumb_file = Column(String)

    created = Column(DateTime)
    uploaded = Column(DateTime)
