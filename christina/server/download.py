from christina.net.downloader import DownloadTask
from fastapi import APIRouter, WebSocket, HTTPException
from websockets.exceptions import ConnectionClosed
from christina import net
from .utils import ConnectionManager
import asyncio

download_ws_manager = ConnectionManager()

router = APIRouter(prefix='/download')


@router.get('/retry/{id}')
def route_retry(id: str):
    try:
        net.retry(id)
    except ValueError as e:
        raise HTTPException(400, repr(e))

    # if succeeded, return something other than null...
    return {"id": id}


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


@net.downloader_emitter.on('added')
def on_added(task: DownloadTask):
    download_ws_manager.broadcast({
        'type': 'added',
        'data': task.id
    })


@net.downloader_emitter.on('loaded')
def on_added(task: DownloadTask):
    download_ws_manager.broadcast({
        'type': 'loaded',
        'data': task.id
    })


task_send_keys = ['id', 'loaded', 'size', 'type', 'name', 'state', 'error']


def get_tasks():
    return [
        {key: getattr(task, key) for key in task_send_keys}
        for task in net.download_tasks
    ]
