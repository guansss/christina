from datetime import datetime
from pydantic import BaseModel, validator
from typing import List, Optional
from christina import net


class VideoBase(BaseModel):
    type: str
    src_id: str
    title: str
    author_id: str
    uploaded: datetime
    file: str = ''
    thumb_file: str = ''

    # fields that will be deleted after downloads finish
    video_dl_url: Optional[str] = None
    thumb_dl_url: Optional[str] = None
    video_dl_id: Optional[str] = None
    thumb_dl_id: Optional[str] = None


class Video(VideoBase):
    id: int
    created: datetime

    url: str = None
    thumb: str = None

    @validator("url", always=True)
    def get_url(cls, v, values):
        return net.static(values['file'])

    @validator("thumb", always=True)
    def get_thumb(cls, v, values):
        return net.static(values['thumb_file'])

    class Config:
        orm_mode = True


class VideoCreate(BaseModel):
    type: str
    url: str
    html: str


class VideoList(BaseModel):
    list: List[Video]
    total: int
