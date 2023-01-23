from typing import NamedTuple


class OkdPTrackAbsoluteTimeMessage(NamedTuple):
    time: int
    port: int
    track: int
    data: bytes
