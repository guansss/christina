from typing import Union
import datetime


def timestamp(dt: Union[datetime.date, datetime.time]) -> int:
    return int(dt.timestamp() * 1000)
