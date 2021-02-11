from christina.net.downloader import DownloadTask
from fastapi import APIRouter, WebSocket, HTTPException
from christina import net


router = APIRouter(prefix='/download')

progress_keys = ['id', 'loaded', 'size', 'error']


@router.get('/retry')
def route_retry(id: str):
    task = net.get_task(id)

    if not task:
        raise HTTPException(404, f'Could not find task by ID: {id}.')

    if task.state != DownloadTask.State.FAILED:
        raise HTTPException(400, f'Cannot retry a task that has not failed. (state: {task.state})')

    net.download(task)


@router.websocket_route('/download/')
async def ws_tasks(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()

        tasks = [
            {key: getattr(task, key) for key in progress_keys}
            for task in net.download_tasks
        ]

        await websocket.send_json(tasks)
