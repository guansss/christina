from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from . import models, schemas
from typing import Union, Tuple
from christina.logger import get_logger

logger = get_logger(__name__)


def get_video(db: Session, id: int):
    return db.query(models.Video).get(id)


def get_videos(db: Session, char: str, offset: int, limit: int, order: str) -> Tuple[models.Video, int]:
    query = db.query(models.Video) \
        .join(models.video_char_table, isouter=True) \
        .join(models.Character, isouter=True) \
        .filter(models.Video.deleted == None)

    if char:
        # the char can be a array like "1,2,3"
        if ',' in char:
            query = query.filter(models.Character.id.in_(char.split(',')))
        else:
            query = query.filter(models.Character.id == char)

    # count without setting the order
    total = query.count()

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

        query = query.order_by(order_field)

    db_video = query.offset(offset).limit(limit).all()

    return db_video, total


def count_videos(db: Session):
    return db.query(func.count(models.Video.id)).scalar()


def create_video(db: Session, video: schemas.VideoBase):
    created = datetime.now()
    db_video = models.Video(**video.dict(), created=created)
    db.add(db_video)
    db.flush()
    return db_video


def update_video(db: Session, video: Union[int, models.Video], items: dict):
    if isinstance(video, int):
        video = get_video(db, video)

    if not video:
        raise ValueError('Could not find video by ID.')

        for field in items:
            setattr(video, field, items[field])


def delete_video(db: Session, id: int):
    db_video = db.query(models.Video).get(id)

    if not db_video:
        raise ValueError('Video does not exist.')

    db_video.deleted = True


def get_chars(db: Session):
    return db.query(models.Character).all()


def create_char(db: Session, name: str, alias: str = None):
    if exist_char(db, name):
        raise ValueError('Name already exists.')

    db_char = models.Character(name=name, alias=alias)
    db.add(db_char)
    db.flush()
    return db_char


def exist_char(db: Session, name: str) -> bool:
    return bool(db.query(models.Character).filter_by(name=name).first())


def add_video_char(db: Session, video_id: int, char_id: str):
    if exist_video_char(db, video_id, char_id):
        raise ValueError('Record already exists.')

    clause = models.video_char_table.insert().values(video_id=video_id, char_id=char_id)
    db.execute(clause)


def remove_video_char(db: Session, video_id: int, char_id: str):
    if not exist_video_char(db, video_id, char_id):
        raise ValueError('Record does not exist.')

    clause = models.video_char_table.delete().where(
        (models.video_char_table.c.video_id == video_id)
        & (models.video_char_table.c.char_id == char_id)
    )
    db.execute(clause)


def exist_video_char(db: Session, video_id: int, char_id: str) -> bool:
    return bool(
        db.query(models.video_char_table)
        .filter_by(video_id=video_id, char_id=char_id)
        .first()
    )
