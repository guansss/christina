import os
import urllib.parse

static_base_url = os.environ['STATIC_SERVER']


def static(path: str):
    return urllib.parse.urljoin(static_base_url, path)
