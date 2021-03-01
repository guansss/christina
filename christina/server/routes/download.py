import asyncio

from fastapi import APIRouter, WebSocket
from websockets.exceptions import ConnectionClosed

from christina.net import downloader
from ..utils import ConnectionManager

download_ws_manager = ConnectionManager()

router = APIRouter(prefix='/download')


@router.get('/{id}/stop')
def route_stop(id: str):
    downloader.stop(id)


@router.get('/{id}/start')
def route_start(id: str):
    downloader.start(id)


@router.delete('/{id}')
def route_remove(id: str):
    downloader.remove(id)


@router.websocket('/download/')
async def ws_tasks(websocket: WebSocket, interval: int = 1000):
    await download_ws_manager.connect(websocket)

    try:
        while True:
            await websocket.send_json({
                'type': 'tasks',
                'data': get_tasks()
            })
            await asyncio.sleep(interval / 1000)

    except ConnectionClosed:
        download_ws_manager.disconnect(websocket)


@downloader.emitter.on('added')
def on_added(task: downloader.DownloadTask):
    download_ws_manager.broadcast({
        'type': 'added',
        'data': task.id
    })


@downloader.emitter.on('loaded')
def on_added(task: downloader.DownloadTask):
    download_ws_manager.broadcast({
        'type': 'loaded',
        'data': task.id
    })


task_send_attrs = ['id', 'loaded', 'size', 'type', 'name', 'state', 'error']


def get_tasks():
    return [
        {key: getattr(task, key) for key in task_send_attrs}
        for task in downloader.download_tasks
    ]
