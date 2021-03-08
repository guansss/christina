import asyncio
from typing import List

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
def on_added(targets: List[downloader.Downloadable]):
    download_ws_manager.broadcast({
        'type': 'added',
        'data': [target.id for target in targets]
    })


@downloader.emitter.on('loaded')
def on_loaded(targets: List[downloader.Downloadable]):
    download_ws_manager.broadcast({
        'type': 'loaded',
        'data': [target.id for target in targets]
    })
