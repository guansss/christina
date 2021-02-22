from sqlalchemy import Column, Boolean, Integer, String, Enum, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from christina.db import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum('i'))
    src_url = Column(String)
    title = Column(String)
    author_id = Column(String)

    file = Column(String)
    thumb_file = Column(String)

    video_dl_url = Column(String)
    thumb_dl_url = Column(String)

    # ID of the download tasks
    video_dl_id = Column(String)
    thumb_dl_id = Column(String)

    created = Column(DateTime)
    uploaded = Column(DateTime)

    deleted = Column(Boolean)

    chars = relationship("Character", secondary='video_char')


class Character(Base):
    __tablename__ = "chars"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    alias = Column(String)


video_char_table = Table(
    'video_char',
    Base.metadata,
    Column('video_id', Integer, ForeignKey('videos.id'), primary_key=True),
    Column('char_id', Integer, ForeignKey('chars.id'), primary_key=True)
)
