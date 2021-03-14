import json
import os
from typing import Optional

from christina import utils
from christina.logger import get_logger
from christina.video import models

logger = get_logger(__name__)

VIDEO_DIR = 'vid'
IMG_DIR = 'img'


def get_basename(video: models.Video):
    return f'{video.id:04}_{video.type}_{video.title}'


def get_video_file(video: models.Video, ext: str):
    return os.path.join(VIDEO_DIR, get_basename(video) + '.' + ext)


def get_thumb_file(video: models.Video, ext: str):
    return os.path.join(IMG_DIR, get_basename(video) + '.' + ext)


def gen_thumb(video_file: str, image_file: str, seconds: Optional[float] = None, width: int = 1280,
              overwrite_existing: bool = False):
    if seconds is None:
        seconds = get_duration(video_file) * 0.8

    try:
        utils.subprocess([
            'ffmpeg',

            # overwrite existing output file
            '-y' if overwrite_existing else '-n',

            # seek to the position, this option should be used before -i or the decoding will be extremely slow
            '-ss', str(seconds),

            # the input file
            '-i', video_file,

            # fixed width and auto height
            '-filter:v', f'scale={width}:-1',

            # capture a single frame
            '-frames:v', '1',

            # jpeg quality (2-31) https://stackoverflow.com/a/10234065/13237325
            '-qscale:v', '4',

            # the output file
            image_file
        ])

    except ChildProcessError as e:
        if not overwrite_existing and 'already exists. Exiting' not in str(e):
            raise
    except Exception as e:
        logger.error('Error when generating thumbnail for ', video_file)
        logger.exception(e)


def get_duration(video_file: str):
    result = utils.subprocess(
        'ffprobe -v error -show_entries format=duration -print_format json=compact=1 {}', video_file)

    # the duration is in seconds
    return float(json.loads(result)['format']['duration'])
