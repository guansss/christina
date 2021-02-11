from datetime import datetime
from pydantic import BaseModel


class VideoBase(BaseModel):
    type: str
    src_id: str
    url: str
    title: str
    author_id: str
    uploaded: datetime
    thumb_url: str
    file: str = ''
    thumb_file: str = ''
    video_dl_id: str = ''
    thumb_dl_id: str = ''


class Video(VideoBase):
    id: int
    created: datetime

    class Config:
        orm_mode = True


class VideoCreate(BaseModel):
    type: str
    url: str
    html: str
