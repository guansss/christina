from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class VideoBase(BaseModel):
    type: str
    src_id: str
    title: str
    author_id: str
    uploaded: datetime
    file: str = ''
    thumb_file: str = ''

    # fields that will be deleted after downloads finish
    url: Optional[str] = None
    thumb_url: Optional[str] = None
    video_dl_id: Optional[str] = None
    thumb_dl_id: Optional[str] = None


class Video(VideoBase):
    id: int
    created: datetime

    class Config:
        orm_mode = True


class VideoCreate(BaseModel):
    type: str
    url: str
    html: str
