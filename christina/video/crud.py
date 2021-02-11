from datetime import datetime
from sqlalchemy.orm import Session
from . import models, schemas
from typing import Union


def get_video(db: Session, id: int):
    return db.query(models.Video).filter(models.Video.id == id).first()


def get_videos(db: Session, offset: int = 0, limit: int = 10):
    return db.query(models.Video).offset(offset).limit(limit).all()


def create_video(db: Session, video: schemas.VideoBase):
    created = datetime.now()
    db_video = models.Video(**video.dict(), created=created)
    db.add(db_video)
    db.commit()
    return db_video


def update_video(db: Session, video: Union[int, models.Video], items: dict):
    if isinstance(video, int):
        video = get_video(db, video)

    if video:
        for field in items:
            setattr(video, field, items[field])

        db.commit()
