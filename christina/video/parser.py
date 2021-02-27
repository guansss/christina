import re
import urllib.parse
from dataclasses import dataclass
from typing import Optional

from scrapy.selector import Selector

from christina import utils
from . import schemas


@dataclass
class VideoInfo:
    src_url: str
    url: str
    ext: str
    title: str
    thumb_url: str
    thumb_ext: str
    uploaded_time: int
    creator_name: str
    creator_url: Optional[str] = None


def parse_video_source(source: schemas.VideoCreate) -> VideoInfo:
    if source.type == 'i':
        return parse_iwara_page(source.url, source.html)
    else:
        raise TypeError('Unknown video type.')


def parse_iwara_page(url: str, html: str) -> VideoInfo:
    selector = Selector(text=html)

    title = selector.css('.node-info .title::text').get()

    thumb_url = selector.css('#video-player::attr(poster)').get()

    # e.g. /users/artypencil
    creator_url = selector.css('.node-info .username::attr(href)').get()

    creator_name = selector.css('.node-info .username::text').get()

    download_urls = selector.css('#download-options li:first-child a::attr(href)').getall()

    # e.g.
    # //galaco.iwara.tv/file.php?expire=1612634059&hash=71c6e02e2958ea9ddc8e0fa708f640bd20acf118
    # &file=2021%2F01%2F09%2F1610163870_No7lRIgR5YFp5vlpJ_Source.mp4&op=dl&r=0
    download_url = next((link for link in download_urls if 'Source' in link), None)

    if not download_url:
        raise ValueError('Could not find download URL for Source resolution.')

    file = re.search(r'file=([^&]+)', download_url)[1]

    # e.g. 2021/01/09/1610163870_No7lRIgR5YFp5vlpJ_Source.mp4
    file = urllib.parse.unquote(file)

    filename = file[file.rindex('/') + 1:]

    uploaded_time = int(filename.split('_')[0])

    # resolve relative URLs
    thumb_url = urllib.parse.urljoin(url, thumb_url)
    creator_url = urllib.parse.urljoin(url, creator_url)
    download_url = urllib.parse.urljoin(url, download_url)

    return VideoInfo(
        src_url=url,
        url=download_url,
        ext=utils.get_extension(filename),
        title=title,
        thumb_url=thumb_url,
        thumb_ext=utils.get_extension(thumb_url),
        uploaded_time=uploaded_time,
        creator_name=creator_name,
        creator_url=creator_url,
    )
