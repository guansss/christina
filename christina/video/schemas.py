from datetime import datetime
from pydantic import BaseModel


class VideoBase(BaseModel):
    type: str
    src_id: str
    url: str
    file: str
    title: str
    author_id: str
    uploaded: datetime
    thumb_url: str
    thumb_file: str


class Video(VideoBase):
    id: int
    created: datetime

    class Config:
        orm_mode = True


class VideoCreate(BaseModel):
    type: str
    url: str
    html: str
