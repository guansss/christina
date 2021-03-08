from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, validator

from christina import net


class VideoBase(BaseModel):
    type: str
    src_url: str
    title: str
    uploaded: datetime
    rating: int = 0
    deleted: Optional[bool] = None

    # fields to be assigned after instantiation
    file: str = None
    thumb_file: str = None

    # fields that will be deleted after downloads finish
    video_dl_url: Optional[str] = None
    thumb_dl_url: Optional[str] = None
    video_dl_id: Optional[str] = None
    thumb_dl_id: Optional[str] = None

    # foreign key
    creator_id: Optional[int] = None


class Video(VideoBase):
    id: int
    created: datetime
    url: str = None
    thumb: str = None

    creator: 'Person' = None
    chars: List['Character'] = []
    tags: List['Tag'] = []

    @validator("url", always=True)
    def get_url(cls, v, values):
        return net.static_url(values['file'])

    @validator("thumb", always=True)
    def get_thumb(cls, v, values):
        return net.static_url(values['thumb_file'])

    class Config:
        orm_mode = True


class VideoCreate(BaseModel):
    type: str
    url: str
    html: str


class VideoUpdate(BaseModel):
    rating: Optional[int] = None


class VideoList(BaseModel):
    list: List[Video]
    total: int


class PersonBase(BaseModel):
    name: str
    url: Optional[str] = None


class Person(PersonBase):
    id: int

    class Config:
        orm_mode = True


class PersonCreate(PersonBase):
    video_id: Optional[int] = None


class CharacterBase(BaseModel):
    name: str
    alias: Optional[str] = None


class Character(CharacterBase):
    id: int

    class Config:
        orm_mode = True


class CharacterCreate(CharacterBase):
    video_id: Optional[int] = None


class TagBase(BaseModel):
    name: str
    alias: Optional[str] = None


class Tag(TagBase):
    id: int

    class Config:
        orm_mode = True


class TagCreate(TagBase):
    video_id: Optional[int] = None


Video.update_forward_refs()
