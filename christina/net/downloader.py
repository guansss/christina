import asyncio
import os
import uuid
from dataclasses import dataclass
from enum import IntEnum
from threading import Thread
from typing import Callable, Optional, List

import aiohttp

from christina import utils
from christina.logger import get_logger
from christina.tools.proxy import HTTP_PROXY

logger = get_logger(__name__)
loop = asyncio.new_event_loop()
http_session = None

download_dir = os.environ['DATA_DIR']
download_tasks: List['DownloadTask'] = []

downloader_emitter = utils.EventEmitter()


@dataclass
class Downloadable:
    url: str
    file: str
    type: str
    name: str
    use_proxy: bool = False
    chunk_size: int = 16384
    onload: Optional[Callable[[], None]] = None
    onerror: Optional[Callable[[Exception], None]] = None
    onended: Optional[Callable[[], None]] = None


class DownloadTask:
    def __init__(self, downloadable: Downloadable):
        downloadable.url = 'http://127.0.0.1:8000/test.txt'

        self.downloadable = downloadable

        self.id = uuid.uuid4().hex[:8]
        self.path = os.path.join(download_dir, downloadable.file)
        self.state = DownloadTask.State.INITIAL
        self.loaded = 0
        self.size = 0
        self.error = ''

    def reset(self):
        self.state = DownloadTask.State.INITIAL
        self.loaded = 0
        self.error = ''

    def __getattr__(self, key: str):
        # delegate the downloadable's attributes
        if key in self.__dict__:
            return self.__dict__[key]
        return getattr(self.downloadable, key)

    class State(IntEnum):
        INITIAL = 0
        LOADING = 1
        SUCCEEDED = 2
        FAILED = 3


def get_task(id: str):
    return utils.find(download_tasks, lambda task: task.id == id)


def retry(id: str):
    task = get_task(id)

    if not task:
        raise ValueError(f'Could not find task by ID: {id}.')

    if task.state != DownloadTask.State.FAILED:
        raise ValueError(f'Cannot retry a task that has not failed. (state: {task.state})')

    task.reset()

    asyncio.run_coroutine_threadsafe(download_threaded(task), loop)


def download(downloadable: Downloadable):
    task = DownloadTask(downloadable)
    download_tasks.append(task)
    downloader_emitter.emit_threading('added', task)

    asyncio.run_coroutine_threadsafe(download_threaded(task), loop)

    return task


async def download_threaded(task: DownloadTask):
    fd = None

    try:
        logger.info(f'Downloading "{task.url}"\n...to "{task.path}"')

        task.state = DownloadTask.State.LOADING

        if task.use_proxy:
            # never use proxy on local host...
            if '127.0.0.1' not in task.url:
                if HTTP_PROXY:
                    logger.info('Using proxy:', HTTP_PROXY)
                else:
                    raise ValueError('Proxy is requested but could not be found in env.')
            else:
                logger.warn(f'Proxy is ignored for local host ({task.url})')

        # fake download
        task.size = 123_456_789
        while task.loaded < task.size:
            await asyncio.sleep(1)
            task.loaded += task.size / 5

        raise TypeError('Download failed for some reason.')

        async with http_session.get(task.url, proxy=HTTP_PROXY) as resp:
            task.size = int(resp.headers.get('content-length', 0))

            with open(task.path, 'wb') as fd:
                fd = fd

                async for chunk in resp.content.iter_chunked(task.chunk_size):
                    fd.write(chunk)

                    task.loaded = fd.tell()

                # fake download
                task.size = 123_456_789
                while task.loaded < task.size:
                    await asyncio.sleep(1)
                    task.loaded += task.size / 5

                logger.info(f'Downloaded "{task.url}" (size: {fd.tell()})')

        # is this necessary?
        task.state = DownloadTask.State.SUCCEEDED

        # remove succeeded task
        download_tasks.remove(task)

        task.onload and task.onload()

        downloader_emitter.emit_threading('loaded', task)

    except Exception as e:
        logger.error(f'Error while downloading {task.url}')
        logger.exception(e)

        if fd:
            try:
                os.unlink(fd.name)
            except Exception:
                pass

        task.state = DownloadTask.State.FAILED
        task.error = repr(e)
        task.onerror and task.onerror(e)

        downloader_emitter.emit_threading('failed', task)
    finally:
        task.onended and task.onended()


def downloader_thread():
    global http_session

    asyncio.set_event_loop(loop)

    http_session = aiohttp.ClientSession()

    loop.run_forever()
    loop.close()


thread = Thread(target=downloader_thread, daemon=True)
thread.start()
