from fastapi import APIRouter, WebSocket
from pydantic import BaseModel
from christina import video, net
from christina.logger import get_logger
import asyncio

logger = get_logger(__name__)

router = APIRouter(prefix='/videos')


class DownloadRequest(BaseModel):
    url: str
    html: str


@router.post('/download')
def download(req: DownloadRequest):
    video_model = video.download(req.url, req.html)

    return {'video': video_model.id}


@router.websocket('/progress')
async def ws_progress(websocket: WebSocket):
    await websocket.accept()
    while True:
        tasks = [{key: getattr(task, key) for key in ['file', 'loaded', 'size']} for task in net.download_tasks]
        await websocket.send_json(tasks)
        await asyncio.sleep(1)
