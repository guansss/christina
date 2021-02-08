from christina import net
from scrapy.selector import Selector
import urllib.parse
import os.path
import re


video_dir = os.path.join(os.path.expanduser('~'), 'Videos')


class IwaraVideo:
    def __init__(self, id: str, url: str, title: str, file: str, authorID: str, createdTime: int):
        self.id = id
        self.url = url
        self.title = title
        self.file = file
        self.authorID = authorID
        self.createdTime = createdTime


def download(url: str, html: str):
    video = parsePage(url, html)

    downloadable = net.Downloadable(
        url=video.url,
        file=os.path.join(video_dir, video.file),
        use_proxy=True
    )

    net.download(downloadable)

    return video


def parsePage(url: str, html: str) -> IwaraVideo:
    selector = Selector(text=html)

    title = selector.css('.node-info .title::text').get()

    # e.g. /users/artypencil
    authorURL = selector.css('.node-info .username::attr(href)').get()

    authorID = authorURL[authorURL.rindex('/'):]

    downloadLinks = selector.css(
        '#download-options li:first-child a::attr(href)').getall()

    # e.g.
    # //galaco.iwara.tv/file.php?expire=1612634059&hash=71c6e02e2958ea9ddc8e0fa708f640bd20acf118
    # &file=2021%2F01%2F09%2F1610163870_No7lRIgR5YFp5vlpJ_Source.mp4&op=dl&r=0
    downloadLink = next(
        (link for link in downloadLinks if 'Source' in link), None)

    if not downloadLink:
        raise ValueError('Could not find download link for Source resolution.')

    file = re.search(r'file=([^&]+)', downloadLink)[1]

    # e.g. 2021/01/09/1610163870_No7lRIgR5YFp5vlpJ_Source.mp4
    file = urllib.parse.unquote(file)

    filename = file[file.rindex('/')+1:]

    ext = filename[filename.rindex('.')+1:]

    createdTime = int(filename.split('_')[0]) * 1000
    id = filename.split('_')[1]

    return IwaraVideo(
        id=id,
        url=downloadLink,
        title=title,
        file=filename+ext,
        authorID=authorID,
        createdTime=createdTime
    )
