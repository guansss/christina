from fastapi import APIRouter, WebSocket, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from christina import net
from christina.db import engine, get_db
from christina.video import parser, crud, models, schemas
from christina.logger import get_logger
import asyncio
import os

models.Base.metadata.create_all(bind=engine)

video_dir = os.path.join(os.environ['DATA_DIR'], 'iwara/vid')
img_dir = os.path.join(os.environ['DATA_DIR'], 'iwara/img')

logger = get_logger(__name__)

router = APIRouter(prefix='/videos')


@router.get('/', response_model=List[schemas.Video])
def route_videos(offset: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    videos = crud.get_videos(db, offset, limit)
    return videos


@router.post('/', response_model=schemas.Video)
def download(source: schemas.VideoCreate, db: Session = Depends(get_db)):
    info = parser.parse_video_source(source)

    video = schemas.VideoBase(
        type=source.type,
        src_id=info.src_id,
        url=info.url,
        file='',
        title=info.title,
        author_id=info.author_id,
        uploaded=datetime.fromtimestamp(info.uploaded_time),
        thumb_url=info.thumb_url,
        thumb_file=''
    )

    db_video = crud.create_video(db, video)

    basename = f'{db_video.id}_{info.title}'

    db_video.file = os.path.join(video_dir, f'{basename}.{info.ext}')
    db_video.thumb_file = os.path.join(img_dir, f'{basename}.{info.thumb_ext}')

    db.commit()

    down_video = net.Downloadable(url=db_video.url, file=db_video.file, use_proxy=True)
    down_thumb = net.Downloadable(url=db_video.thumb_url, file=db_video.thumb_file, use_proxy=True)

    net.download(down_video)
    net.download(down_thumb)

    return db_video


@router.websocket('/progress')
async def ws_progress(websocket: WebSocket):
    await websocket.accept()
    while True:
        tasks = [{key: getattr(task, key) for key in ['file', 'loaded', 'size']} for task in net.download_tasks]
        await websocket.send_json(tasks)
        await asyncio.sleep(1)
