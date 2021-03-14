from datetime import datetime
from typing import Optional, List, Callable

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from christina import utils
from christina.db import engine, get_db, get_db_ctx
from christina.env import DEV_MODE
from christina.logger import get_logger
from christina.net import downloader, static
from christina.video import parser, crud, models, schemas, tools

models.Base.metadata.create_all(bind=engine)

logger = get_logger(__name__)

router = APIRouter(prefix='/videos')


class ThumbUpdate(BaseModel):
    time: float


@router.get('', response_model=schemas.VideoList)
def route_videos(
        search: Optional[str] = None,
        creator: Optional[int] = None,
        char: Optional[str] = None,
        tag: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
        order: str = '',
        db: Session = Depends(get_db)
):
    # the char and tag can be an array like "1,2,3"
    if char:
        if ',' in char:
            char = map(int, char.split(','))
        else:
            char = int(char)

    if tag:
        if ',' in tag:
            tag = map(int, tag.split(','))
        else:
            tag = int(tag)

    videos, total = crud.get_videos(
        db,
        search=search,
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


@router.get('/random', response_model=schemas.Video)
def route_random_video(exclude: Optional[int], rating: Optional[int] = None, db: Session = Depends(get_db)):
    return crud.get_random_video(db, exclude, rating)


@router.get('/{id}', response_model=schemas.Video)
def route_video(id: int, db: Session = Depends(get_db)):
    return crud.get_video(db, id)


@router.put('/{id}/thumb')
def route_thumb(id: int, update: ThumbUpdate, db: Session = Depends(get_db)):
    video = crud.get_video(db, id)
    video_file = static.static_file(video.file)
    thumb_file = static.static_file(video.thumb_file)

    tools.gen_thumb(video_file, thumb_file, update.time, overwrite_existing=True)


@router.patch('/{id}', response_model=schemas.Video)
def route_update_video(id: int, update: schemas.VideoUpdate, db: Session = Depends(get_db)):
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
        person = crud.find_or_create_person(db, name=info.creator_name, url=info.creator_url)

        creator_id = person.id

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

    file = tools.get_video_file(db_video, info.ext)
    thumb_file = tools.get_thumb_file(db_video, info.thumb_ext)

    crud.update_video(db, db_video, {
        'file': file,
        'thumb_file': thumb_file,
    })

    video_dl_target = downloader.Downloadable(
        url=video.video_dl_url,
        file=file,
        name=video.title,
        use_proxy=True,
        meta={
            'video_id': db_video.id,
            'type': 'video'
        }
    )
    thumb_dl_target = downloader.Downloadable(
        url=video.thumb_dl_url,
        file=thumb_file,
        name=video.title,
        use_proxy=True,
        meta={
            'video_id': db_video.id,
            'type': 'image'
        }
    )

    if DEV_MODE:
        video_dl_target.url = 'http://127.0.0.1/test.mp4'
        thumb_dl_target.url = 'http://127.0.0.1/test.jpg'

    downloader.add(video_dl_target)
    downloader.add(thumb_dl_target)

    return db_video


@downloader.emitter.on('added')
def on_added(targets: List[downloader.Downloadable]):
    update_download_fields(targets, save_dl_id)


@downloader.emitter.on('loaded')
def on_loaded(targets: List[downloader.Downloadable]):
    update_download_fields(targets, clear_dl_fields)


def save_dl_id(target: downloader.Downloadable):
    return {
        'video_dl_id': target.id,
    } if target.meta['type'] == 'video' else {
        'thumb_dl_id': target.id,
    }


def clear_dl_fields(target: downloader.Downloadable):
    return {
        'video_dl_url': None,
        'video_dl_id': None,
    } if target.meta['type'] == 'video' else {
        'thumb_dl_url': None,
        'thumb_dl_id': None,
    }


def update_download_fields(
        targets: List[downloader.Downloadable],
        get_fields: Callable[[downloader.Downloadable], dict]
):
    try:
        # don't bother the database if there's no video-related targets
        if not utils.find(targets, lambda target: 'video_id' in target.meta):
            return

        with get_db_ctx() as db:
            for target in targets:
                if 'video_id' in target.meta:
                    fields = get_fields(target)

                    crud.update_video(db, target.meta['video_id'], fields)

    except Exception as e:
        logger.warn('Could not update download fields by targets', targets)
        logger.exception(e)
