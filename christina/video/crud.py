from datetime import datetime
from typing import Union, Tuple, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from christina.db import RecordNotFound, RecordExists
from christina.logger import get_logger
from . import models, schemas

logger = get_logger(__name__)


def get_video(db: Session, id: int):
    return db.query(models.Video).get(id)


def get_random_video(db: Session, exclude: Optional[int], rating: Optional[int]):
    query = db.query(models.Video).filter_by(deleted=None, video_dl_id=None, thumb_dl_id=None)

    if exclude is not None:
        query = query.filter(models.Video.id != exclude)

    if rating is not None:
        query = query.filter_by(rating=rating)

    return query.order_by(func.random()).first()


def get_videos(
        db: Session,
        *,
        creator_id: Optional[int],
        char: Optional[Union[int, List[int]]],
        tag: Optional[Union[int, List[int]]],
        offset: int,
        limit: int,
        order: str
) -> Tuple[models.Video, int]:
    query = db.query(models.Video) \
        .filter(models.Video.deleted == None) \
        .options(selectinload(models.Video.creator), selectinload(models.Video.chars), selectinload(models.Video.tags))

    if creator_id:
        query = query.filter(models.Video.creator_id == creator_id)

    if char:
        if isinstance(char, int):
            query = query.filter(
                models.Video.chars.any(models.Character.id == char)
            )
        else:
            query = query.filter(
                models.Video.chars.any(models.Character.id.in_(char))
            )

    if tag:
        if isinstance(tag, int):
            query = query.filter(models.Video.tags.any(models.Tag.id == tag))
        else:
            query = query.filter(models.Video.tags.any(models.Tag.id.in_(tag)))

    # count without setting the order
    total = query.count()

    if order:
        descend = True

        if '-' in order:
            descend = False
            order = order.replace('-', '')

        if order not in models.Video.__dict__:
            raise ValueError('Invalid order.')

        order_field = getattr(models.Video, order)

        if descend:
            order_field = order_field.desc()

        query = query.order_by(order_field, models.Video.id)

    db_videos = query.offset(offset).limit(limit).all()

    return db_videos, total


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
        raise RecordNotFound

    for field in items:
        setattr(video, field, items[field])


def delete_video(db: Session, id: int):
    db_video = db.query(models.Video).get(id)

    if not db_video:
        raise RecordNotFound

    db_video.deleted = True


# Person


def get_people(db: Session):
    return db.query(models.Person).all()


def find_person(db: Session, **fields):
    return db.query(models.Person).filter_by(**fields).first()


def create_person(db: Session, name: str, url: str = None):
    if find_person(db, name=name, url=url):
        raise RecordExists

    db_person = models.Person(name=name, url=url)
    db.add(db_person)
    db.flush()
    return db_person


# Character


def get_chars(db: Session):
    return db.query(models.Character).all()


def create_char(db: Session, name: str, alias: str = None):
    if exist_char(db, name):
        raise RecordExists

    db_char = models.Character(name=name, alias=alias)
    db.add(db_char)
    db.flush()
    return db_char


def exist_char(db: Session, name: str) -> bool:
    return bool(db.query(models.Character).filter_by(name=name).first())


def add_video_char(db: Session, video_id: int, char_id: int):
    if exist_video_char(db, video_id, char_id):
        raise RecordExists

    clause = models.video_char_table.insert().values(
        video_id=video_id, char_id=char_id)
    db.execute(clause)


def remove_video_char(db: Session, video_id: int, char_id: int):
    if not exist_video_char(db, video_id, char_id):
        raise RecordNotFound

    clause = models.video_char_table.delete().where(
        (models.video_char_table.c.video_id == video_id)
        & (models.video_char_table.c.char_id == char_id)
    )
    db.execute(clause)


def exist_video_char(db: Session, video_id: int, char_id: int) -> bool:
    return bool(
        db.query(models.video_char_table)
            .filter_by(video_id=video_id, char_id=char_id)
            .first()
    )


# Tag


def get_tags(db: Session):
    return db.query(models.Tag).all()


def create_tag(db: Session, name: str, alias: str = None):
    if exist_tag(db, name):
        raise RecordExists

    db_tag = models.Tag(name=name, alias=alias)
    db.add(db_tag)
    db.flush()
    return db_tag


def exist_tag(db: Session, name: str) -> bool:
    return bool(db.query(models.Tag).filter_by(name=name).first())


def add_video_tag(db: Session, video_id: int, tag_id: int):
    if exist_video_tag(db, video_id, tag_id):
        raise RecordExists

    clause = models.video_tag_table.insert().values(video_id=video_id, tag_id=tag_id)
    db.execute(clause)


def remove_video_tag(db: Session, video_id: int, tag_id: int):
    if not exist_video_tag(db, video_id, tag_id):
        raise RecordNotFound

    clause = models.video_tag_table.delete().where(
        (models.video_tag_table.c.video_id == video_id)
        & (models.video_tag_table.c.tag_id == tag_id)
    )
    db.execute(clause)


def exist_video_tag(db: Session, video_id: int, tag_id: int) -> bool:
    return bool(
        db.query(models.video_tag_table)
            .filter_by(video_id=video_id, tag_id=tag_id)
            .first()
    )
