from typing import NamedTuple, Union


class OkdMidiDeltaTime(NamedTuple):
    tick: int


class OkdMidiGenericEvent(NamedTuple):
    data: bytes


OkdMidiMessage = Union[OkdMidiDeltaTime, OkdMidiGenericEvent]
