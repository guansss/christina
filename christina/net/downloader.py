import asyncio
import os
import uuid
from contextlib import suppress
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from threading import Thread
from typing import Callable, Optional, List

import aiohttp

from christina import utils
from christina.logger import get_logger
from christina.tools.proxy import HTTP_PROXY

DEV_MODE = bool(os.getenv('DEV', 0))

DOWNLOAD_DIR = Path(os.environ['DATA_DIR'])
TEMP_DIR = Path(os.environ['TEMP_DIR'])

TEMP_DIR.mkdir(parents=True, exist_ok=True)

logger = get_logger(__name__)
loop = asyncio.new_event_loop()

# session will be initialized in new thread
http_session: aiohttp.ClientSession

download_tasks: List['DownloadTask'] = []

emitter = utils.EventEmitter()


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
    onstop: Optional[Callable[[], None]] = None


class DownloadTaskState(IntEnum):
    INITIAL = 0
    LOADING = 1
    SUCCEEDED = 2
    FAILED = 3
    STOPPED = 4


class DownloadTask:
    def __init__(self, downloadable: Downloadable):
        if downloadable.type == 'video':
            downloadable.url = 'http://127.0.0.1:8000/test.mp4'
        else:
            downloadable.url = 'http://127.0.0.1:8000/test.jpg'

        self.downloadable = downloadable

        id_conflict = True

        while id_conflict:
            self.id = uuid.uuid4().hex[:8]
            id_conflict = bool(get_task(self.id))

        self._file = downloadable.file
        self.file = str(DOWNLOAD_DIR.joinpath(downloadable.file))
        self.temp_file = str(TEMP_DIR.joinpath(self.id))

        self.state = DownloadTaskState.INITIAL
        self.loaded = 0
        self.size = 0
        self.error = ''

        self.fetch_task: Optional[asyncio.Task] = None

    def start(self):
        # a quick validation to raise exception immediately
        if self.state in [DownloadTaskState.LOADING, DownloadTaskState.SUCCEEDED]:
            raise Exception(f'Invalid state: {self.state}')

        self.error = ''

        asyncio.run_coroutine_threadsafe(self.__download(), loop)

    async def __download(self):
        try:
            logger.info(f'Downloading "{self.url}"\n...to "{self.file}"')

            # validate again to prevent race condition
            if self.state in [DownloadTaskState.LOADING, DownloadTaskState.SUCCEEDED]:
                raise Exception(f'Invalid state: {self.state}')

            self.state = DownloadTaskState.LOADING

            self.fetch_task = loop.create_task(self.fetch())

            await self.fetch_task

            self.succeed()

            self.onload and self.onload()

            emitter.emit_threading('loaded', self)

        except asyncio.CancelledError:
            logger.info(f'Aborted downloading {self.url}')
            self.onstop and self.onstop()

        except Exception as e:
            logger.error(f'Error while downloading {self.url}')
            logger.exception(e)

            self.failure(e)

            self.onerror and self.onerror(e)

            emitter.emit_threading('failed', self)

        finally:
            self.fetch_task = None

    async def fetch(self):
        proxy: Optional[str] = None

        if self.use_proxy:
            # never use proxy on local host...
            if '127.0.0.1' not in self.url:
                proxy = HTTP_PROXY

                if proxy:
                    logger.info('Using proxy:', proxy)
                else:
                    raise ValueError('Proxy is requested but could not be found in env.')
            else:
                logger.warn(f'Proxy is ignored for local host ({self.url})')

        # fake download
        self.size = 123_456_789
        while self.loaded < self.size:
            await asyncio.sleep(1)
            logger.log(self.loaded)
            self.loaded += self.size / 30
        self.loaded = self.size

        raise Exception('Download failed for some reason.')

        headers = {}

        with suppress(FileNotFoundError):
            # start from the last position if the last download didn't succeed
            self.loaded = Path(self.temp_file).stat().st_size

            headers['Range'] = f'bytes={self.loaded}-'

        async with http_session.get(self.url, headers=headers, proxy=proxy) as resp:
            resp.raise_for_status()

            content_length = int(resp.headers.get('content-length', '0'))
            self.size = self.loaded + content_length

            with open(self.temp_file, 'ab') as f:
                async for chunk in resp.content.iter_chunked(self.chunk_size):
                    f.write(chunk)

                    self.loaded += len(chunk)

                # correct the size
                self.loaded = self.size = f.tell()

        logger.info(f'Downloaded "{self.url}" (size: {self.size})')

    def succeed(self):
        self.state = DownloadTaskState.SUCCEEDED

        if DEV_MODE:
            # the file can conflict all the time during development
            Path(self.temp_file).replace(self.file)
        else:
            Path(self.temp_file).rename(self.file)

    # this method cannot be named `fail` due to a bug of PyCharm...
    # https://stackoverflow.com/a/21955247/13237325
    def failure(self, e: Exception):
        self.state = DownloadTaskState.FAILED
        self.error = repr(e)

    def stop(self):
        if self.state not in [DownloadTaskState.SUCCEEDED, DownloadTaskState.FAILED, DownloadTaskState.STOPPED]:
            self.state = DownloadTaskState.STOPPED

            if self.fetch_task:
                self.fetch_task.cancel()
                self.fetch_task = None

    def __getattr__(self, key: str):
        # delegate the downloadable's attributes
        if key in self.__dict__:
            return self.__dict__[key]
        return getattr(self.downloadable, key)


def get_task(id: str, mandatory=False):
    task = utils.find(download_tasks, lambda task: task.id == id)

    # the task must exist if mandatory
    if not task and mandatory:
        raise ValueError(f'Could not find task by ID: {id}.')

    return task


def download(downloadable: Downloadable):
    task = DownloadTask(downloadable)

    download_tasks.append(task)
    emitter.emit_threading('added', task)

    task.start()

    return task


def start(id: str):
    get_task(id, mandatory=True).start()


def stop(id: str):
    get_task(id, mandatory=True).stop()


def remove(id: str):
    task = get_task(id, mandatory=True)
    task.stop()

    # remove temp file
    with suppress(FileNotFoundError):
        Path(task.temp_file).unlink()

    download_tasks.remove(task)


def downloader_thread():
    global http_session

    asyncio.set_event_loop(loop)

    http_session = aiohttp.ClientSession()

    loop.run_forever()
    loop.close()


thread = Thread(target=downloader_thread, daemon=True)
thread.start()
