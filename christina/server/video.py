from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from christina import net
from christina.db import engine, get_db, get_db_ctx
from christina.video import parser, crud, models, schemas
from christina.logger import get_logger
import os

models.Base.metadata.create_all(bind=engine)

video_dir = 'vid'
img_dir = 'img'

logger = get_logger(__name__)

router = APIRouter(prefix='/videos')


@router.get('/', response_model=schemas.VideoList)
def route_videos(
    char: str = '',
    offset: int = 0,
    limit: int = 100,
    order: str = '',
    db: Session = Depends(get_db)
):
    videos = crud.get_videos(db, char, offset, limit, order)
    total = crud.count_videos(db)

    return {
        'list': videos,
        'total': total
    }


@router.get('/{id}', response_model=schemas.Video)
def route_video(id: str, db: Session = Depends(get_db)):
    video = crud.get_video(db, id)
    return video


@router.delete('/{id}', status_code=200)
def route_delete_video(id: int, db: Session = Depends(get_db)):
    crud.delete_video(db, id)


@router.post('/', status_code=201,response_model=schemas.Video)
def route_add_video(source: schemas.VideoCreate, db: Session = Depends(get_db)):
    info = parser.parse_video_source(source)

    video = schemas.VideoBase(
        type=source.type,
        src_url=info.src_url,
        title=info.title,
        author_id=info.author_id,
        uploaded=datetime.fromtimestamp(info.uploaded_time),
        video_dl_url=info.url,
        thumb_dl_url=info.thumb_url,
    )

    db_video = crud.create_video(db, video)

    basename = f'{video.type}_{db_video.id}_{video.title}'

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


def clear_fields(video_id: str, *fields: str):
    def fn():
        try:
            with get_db_ctx() as db:
                for field in fields:
                    crud.update_video(db, video_id, {field: None})
        except Exception as e:
            logger.warn('Could not clear fields:', fields)
            logger.exception(e)

    return fn
