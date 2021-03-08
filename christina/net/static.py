import os
import urllib.parse
from pathlib import Path

STATIC_SERVER = os.environ['STATIC_SERVER']
STATIC_DIR = os.environ['STATIC_DIR']

STATIC_DIR_PATH = Path(STATIC_DIR)


# Gets an absolute path where this file should be saved
def static_file(*path: str):
    return str(STATIC_DIR_PATH.joinpath(*path))


# Gets a URL that refers to this file
def static_url(path: str):
    return urllib.parse.urljoin(STATIC_SERVER, path.replace(STATIC_DIR, ''))
