from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from . import models, schemas
from typing import Union
from christina.logger import get_logger

logger=get_logger(__name__)


def get_video(db: Session, id: int):
    return db.query(models.Video).filter(models.Video.id == id).first()


def get_videos(db: Session, offset: int = 0, limit: int = 10, order: str = ''):
    if order:
        descend = True

        if '*' in order:
            descend = False
            order = order.replace('*', '')

        if order not in models.Video.__dict__:
            raise TypeError('Invalid order.')

        order_field = getattr(models.Video, order)

        if descend:
            order_field = order_field.desc()

        query = db.query(models.Video).order_by(order_field)

    else:
        query = db.query(models.Video)

    return query.offset(offset).limit(limit).all()


def count_videos(db: Session):
    return db.query(func.count(models.Video.id)).scalar()


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
