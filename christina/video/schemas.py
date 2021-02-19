from datetime import datetime
from pydantic import BaseModel, validator
from typing import List, Optional
from christina import net


class VideoBase(BaseModel):
    type: str
    src_url: str
    title: str
    author_id: str
    uploaded: datetime

    # fields to be assigned after instantiation
    file: str = None
    thumb_file: str = None

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
    chars: List['Character'] = []

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


class CharacterBase(BaseModel):
    name: str
    abbr: str


class Character(CharacterBase):
    id: int

    class Config:
        orm_mode = True


class CharacterCreate(BaseModel):
    name: str
    abbr: str
    video_id: Optional[int] = None


Video.update_forward_refs()
