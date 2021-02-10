from christina import net, utils
from scrapy.selector import Selector
import urllib.parse
import os.path
import re


video_dir = os.path.join(os.environ['DATA_DIR'], 'iwara/vid')
img_dir = os.path.join(os.environ['DATA_DIR'], 'iwara/img')


class IwaraVideo:
    def __init__(self, id: str, url: str, ext: str, title: str, preview: str, author_id: str, created_time: int):
        self.id = id
        self.url = url
        self.ext = ext
        self.title = title
        self.preview = preview
        self.author_id = author_id
        self.created_time = created_time

    @property
    def name(self):
        return '{title}'.format(**vars(self))


def download(url: str, html: str):
    video = parse_page(url, html)

    downloadable = net.Downloadable(
        url=video.url,
        file=os.path.join(video_dir, video.name + '.' + video.ext),
        use_proxy=True
    )

    net.download(downloadable)

    downloadable = net.Downloadable(
        url=video.preview,
        file=os.path.join(img_dir, video.name + '.' + utils.get_extension(video.preview)),
        use_proxy=True
    )

    net.download(downloadable)

    return video


def parse_page(url: str, html: str) -> IwaraVideo:
    selector = Selector(text=html)

    title = selector.css('.node-info .title::text').get()

    preview_url = selector.css('#video-player::attr(poster)').get()

    # e.g. /users/artypencil
    author_url = selector.css('.node-info .username::attr(href)').get()

    author_id = author_url[author_url.rindex('/'):]

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

    filename = file[file.rindex('/')+1:]

    created_time = int(filename.split('_')[0]) * 1000
    id = filename.split('_')[1]

    # resolve relative URLs
    preview_url = urllib.parse.urljoin(url, preview_url)
    download_url = urllib.parse.urljoin(url, download_url)

    return IwaraVideo(
        id=id,
        url=download_url,
        ext=utils.get_extension(filename),
        title=title,
        preview=preview_url,
        author_id=author_id,
        created_time=created_time
    )
