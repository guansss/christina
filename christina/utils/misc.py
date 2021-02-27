import datetime
from typing import Any, Iterator, Optional, Callable, TypeVar

T = TypeVar('T')


def timestamp(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def find(arr: Iterator[T], predicate: Callable[[Any], bool], default=None) -> Optional[T]:
    return next(((item for item in arr if predicate(item))), default)
