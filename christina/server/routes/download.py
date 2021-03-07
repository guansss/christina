import asyncio

from fastapi import APIRouter, WebSocket
from websockets.exceptions import ConnectionClosed

from christina.logger import get_logger
from christina.net import downloader
from ..utils import ConnectionManager

download_ws_manager = ConnectionManager()

router = APIRouter(prefix='/download')

logger = get_logger(__name__)


@router.websocket('/download/')
async def ws_tasks(websocket: WebSocket):
    await download_ws_manager.connect(websocket)

    try:
        while True:
            await websocket.send_json({
                'type': 'status',
                'data': downloader.downloads
            })
            await asyncio.sleep(1)

    except ConnectionClosed:
        download_ws_manager.disconnect(websocket)


@downloader.emitter.on('added')
def on_added(gid: str):
    download_ws_manager.broadcast({
        'type': 'added',
        'data': gid
    })


@downloader.emitter.on('loaded')
def on_loaded(gid: str):
    download_ws_manager.broadcast({
        'type': 'loaded',
        'data': gid
    })
