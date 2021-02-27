import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from christina import net
from christina.db import engine, get_db, get_db_ctx
from christina.logger import get_logger
from christina.video import parser, crud, models, schemas

models.Base.metadata.create_all(bind=engine)

video_dir = 'vid'
img_dir = 'img'

logger = get_logger(__name__)

router = APIRouter(prefix='/videos')


@router.get('', response_model=schemas.VideoList)
def route_videos(
        creator: Optional[int] = None,
        char: Optional[str] = None,
        tag: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
        order: str = '',
        db: Session = Depends(get_db)
):
    # the char and tag can be an array like "1,2,3"
    try:
        if ',' in char:
            char = map(int, char.split(','))
        else:
            char = int(char)
    except Exception:
        char = None

    try:
        if ',' in tag:
            tag = map(int, tag.split(','))
        else:
            tag = int(tag)
    except Exception:
        tag = None

    videos, total = crud.get_videos(
        db,
        creator_id=creator,
        char=char,
        tag=tag,
        offset=offset,
        limit=limit,
        order=order
    )

    return {
        'list': videos,
        'total': total
    }


@router.get('/{id}', response_model=schemas.Video)
def route_video(id: int, db: Session = Depends(get_db)):
    return crud.get_video(db, id)


@router.patch('/{id}', response_model=schemas.Video)
def route_video(id: int, update: schemas.VideoUpdate, db: Session = Depends(get_db)):
    crud.update_video(db, id, update.dict(exclude_unset=True))

    return crud.get_video(db, id)


@router.delete('/{id}')
def route_delete_video(id: int, db: Session = Depends(get_db)):
    crud.delete_video(db, id)


@router.post('', status_code=201, response_model=schemas.Video)
def route_add_video(source: schemas.VideoCreate, db: Session = Depends(get_db)):
    info = parser.parse_video_source(source)

    creator_id = None

    if info.creator_name:
        creator = crud.find_person(db, name=info.creator_name)

        if not creator:
            creator = crud.create_person(db, name=info.creator_name, url=info.creator_url)

        creator_id = creator.id

    video = schemas.VideoBase(
        type=source.type,
        creator_id=creator_id,
        src_url=info.src_url,
        title=info.title,
        uploaded=datetime.fromtimestamp(info.uploaded_time),
        video_dl_url=info.url,
        thumb_dl_url=info.thumb_url,
    )

    db_video = crud.create_video(db, video)

    basename = f'{db_video.id:04}_{video.type}_{video.title}'

    file = os.path.join(video_dir, f'{basename}.{info.ext}')
    thumb_file = os.path.join(img_dir, f'{basename}.{info.thumb_ext}')

    video_downloadable = net.Downloadable(
        url=video.video_dl_url,
        file=file,
        type='video',
        name=video.title,
        use_proxy=True
    )
    thumb_downloadable = net.Downloadable(
        url=video.thumb_dl_url,
        file=thumb_file,
        type='image',
        name=video.title,
        use_proxy=True
    )

    video_downloadable.onload = clear_fields(db_video.id, 'video_dl_url', 'video_dl_id')
    thumb_downloadable.onload = clear_fields(db_video.id, 'thumb_dl_url', 'thumb_dl_id')
    video_task = net.download(video_downloadable)
    thumb_task = net.download(thumb_downloadable)

    crud.update_video(
        db,
        db_video,
        {
            'file': file,
            'thumb_file': thumb_file,
            'video_dl_id': video_task.id,
            'thumb_dl_id': thumb_task.id,
        }
    )

    return db_video


def clear_fields(video_id: int, *fields: str):
    def fn():
        try:
            with get_db_ctx() as db:
                for field in fields:
                    crud.update_video(db, video_id, {field: None})
        except Exception as e:
            logger.warn('Could not clear fields:', fields)
            logger.exception(e)

    return fn
