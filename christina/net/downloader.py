from christina.logger import get_logger
from threading import Thread
from typing import Callable, Optional
from dataclasses import dataclass
import asyncio
import aiohttp
import os

logger = get_logger(__name__)

loop = asyncio.new_event_loop()

http_session = None


@dataclass
class Downloadable:
    url: str
    file: str
    use_proxy: bool = False
    chunk_size: int = 16384
    onstart: Optional[Callable[[int], None]] = None
    onprogress: Optional[Callable[[int], None]] = None
    onload: Optional[Callable[[], None]] = None
    onerror: Optional[Callable[[Exception], None]] = None


def download(downloadable: Downloadable):
    asyncio.run_coroutine_threadsafe(download_threaded(downloadable), loop)


async def download_threaded(downloadable: Downloadable):
    downloadable.url = 'http://127.0.0.1:8000/test.txt'

    try:
        logger.info(f'Downloading "{downloadable.url}" to "{downloadable.file}"')

        proxy = None

        if downloadable.use_proxy:
            # never use proxy on local host...
            if '127.0.0.1' not in downloadable.url:
                proxy = os.getenv('PROXY', None) or os.getenv('http_proxy', None)

                if proxy:
                    logger.info('Using proxy:', proxy)
                else:
                    raise ValueError('Proxy is requested but could not be found in env')
            else:
                logger.warn(f'Proxy is ignored for local host ({downloadable.url})')

        async with http_session.get(downloadable.url, proxy=proxy) as resp:
            size = int(resp.headers.get('content-length', 0))

            downloadable.onstart and downloadable.onstart(size)

            with open(downloadable.file, 'wb') as fd:
                async for chunk in resp.content.iter_chunked(downloadable.chunk_size):
                    fd.write(chunk)

                    downloadable.onprogress and downloadable.onprogress(fd.tell())

                logger.info(f'Downloaded "{downloadable.url}" (size: {fd.tell()})')

    except Exception as e:
        logger.error(f'Error while downloading {downloadable.url}')
        logger.exception(e)

        downloadable.onerror and downloadable.onerror(e)


def download_thread():
    global http_session

    asyncio.set_event_loop(loop)

    http_session = aiohttp.ClientSession()

    loop.run_forever()
    loop.close()


thread = Thread(target=download_thread, daemon=True)
thread.start()
