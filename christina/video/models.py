from sqlalchemy import Column, Integer, String, Enum, DateTime
from christina.db import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum('i'))
    src_id = Column(String)
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
