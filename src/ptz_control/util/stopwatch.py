from datetime import datetime, timedelta

from logging import getLogger

from typing_extensions import final

log = getLogger(__name__)

@final
class Stopwatch:

    @classmethod
    def started(cls):
        return cls(datetime.now())

    def __init__(self, start_time: datetime):
        self._start_time = start_time

    def elapsed(self) -> timedelta:
        return datetime.now() - self._start_time
