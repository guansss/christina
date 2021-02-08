from christina import net
from scrapy.selector import Selector
import urllib.parse
import os.path
import re


video_dir = os.path.join(os.path.expanduser('~'), 'Videos')


class IwaraVideo:
    def __init__(self, id: str, url: str, title: str, file: str, author_id: str, created_time: int):
        self.id = id
        self.url = url
        self.title = title
        self.file = file
        self.author_id = author_id
        self.created_time = created_time


def download(url: str, html: str):
    video = parse_page(url, html)

    downloadable = net.Downloadable(
        url=video.url,
        file=os.path.join(video_dir, video.file),
        use_proxy=True
    )

    net.download(downloadable)

    return video


def parse_page(url: str, html: str) -> IwaraVideo:
    selector = Selector(text=html)

    title = selector.css('.node-info .title::text').get()

    # e.g. /users/artypencil
    author_url = selector.css('.node-info .username::attr(href)').get()

    author_id = author_url[author_url.rindex('/'):]

    download_links = selector.css('#download-options li:first-child a::attr(href)').getall()

    # e.g.
    # //galaco.iwara.tv/file.php?expire=1612634059&hash=71c6e02e2958ea9ddc8e0fa708f640bd20acf118
    # &file=2021%2F01%2F09%2F1610163870_No7lRIgR5YFp5vlpJ_Source.mp4&op=dl&r=0
    download_link = next((link for link in download_links if 'Source' in link), None)

    if not download_link:
        raise ValueError('Could not find download link for Source resolution.')

    file = re.search(r'file=([^&]+)', download_link)[1]

    # e.g. 2021/01/09/1610163870_No7lRIgR5YFp5vlpJ_Source.mp4
    file = urllib.parse.unquote(file)

    filename = file[file.rindex('/')+1:]
    ext = filename[filename.rindex('.')+1:]

    created_time = int(filename.split('_')[0]) * 1000
    id = filename.split('_')[1]

    return IwaraVideo(
        id=id,
        url=download_link,
        title=title,
        file=filename+ext,
        author_id=author_id,
        created_time=created_time
    )
