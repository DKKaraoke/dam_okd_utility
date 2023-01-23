from typing import NamedTuple


class OkdMTrackAbsoluteTimeMessage(NamedTuple):
    time: int
    data: bytes
