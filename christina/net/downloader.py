import os
import xmlrpc.client
from pathlib import Path
from threading import Thread
from time import sleep
from typing import List

from pydantic import BaseModel

from christina import utils
from christina.logger import get_logger
from christina.tools.proxy import HTTP_PROXY

DOWNLOAD_DIR = Path(os.environ['STATIC_DIR'])

logger = get_logger(__name__)

emitter = utils.EventEmitter()


class Downloadable(BaseModel):
    id: str = ''
    url: str
    file: str
    name: str
    use_proxy: bool = False
    meta: dict = {}


aria2_rpc = xmlrpc.client.ServerProxy(os.environ['ARIA2_RPC'], allow_none=True)

aria2_status_keys = ['gid', 'status', 'totalLength', 'completedLength', 'downloadSpeed', 'errorMessage']
update_status_error = ''

pending_targets: List[Downloadable] = []
downloads: List[dict] = []


def add(target: Downloadable):
    logger.info(f'Downloading "{target.url}" to "{target.file}"')

    pending_targets.append(target)


def update_status():
    global downloads, update_status_error

    try:
        if not len(pending_targets):
            return

        multi_call = xmlrpc.client.MultiCall(aria2_rpc)

        registered, unregistered = [], []

        # split the targets into two lists
        for target in pending_targets:
            if target.id:
                registered.append(target)
            else:
                unregistered.append(target)

        for target in registered:
            multi_call.aria2.tellStatus(target.id, aria2_status_keys)

        for target in unregistered:
            multi_call.aria2.addUri([target.url], {
                'dir': str(DOWNLOAD_DIR),
                'out': target.file,
                'all-proxy': prepare_proxy(target),
            })

        results = list(multi_call())
        registered_result = results[:len(registered)]
        unregistered_result = results[len(registered):]

        # save the fetched downloads
        downloads = registered_result

        # bind gids to added targets
        for i, gid in enumerate(unregistered_result):
            logger.info('Download added', gid, unregistered[i].url)

            unregistered[i].id = gid

        if len(unregistered):
            emitter.emit('added', unregistered)

        complete_targets = []

        for download in downloads:
            # an "id" field is more preferable
            download['id'] = download['gid']
            del download['gid']

            for target in pending_targets:
                if download['status'] == 'complete' and download['id'] == target.id:
                    logger.info('Downloaded', target.id, target.url)

                    complete_targets.append(target)
                    break

        if len(complete_targets):
            for target in complete_targets:
                pending_targets.remove(target)

            emitter.emit('loaded', complete_targets)

        # clear the error
        update_status_error = ''

    except Exception as e:
        err = repr(e)

        # only print a newly occurring error
        if err != update_status_error:
            update_status_error = err
            logger.exception(e)


def prepare_proxy(target: Downloadable):
    if target.use_proxy:
        # never use proxy on local host...
        if '127.0.0.1' not in target.url:
            logger.info('Using proxy:', HTTP_PROXY)
            return HTTP_PROXY

        else:
            logger.warn(f'Proxy is ignored for local host ({target.url})')
            return None


def update_thread():
    while True:
        update_status()
        sleep(1)


thread = Thread(name='Downloader', target=update_thread, daemon=True)
thread.start()
