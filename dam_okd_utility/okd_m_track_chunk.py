import io
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.okd_midi import OkdMidiMessage
from dam_okd_utility.okd_m_track_midi import OkdMTrackMidi


class OkdMTrackChunk(NamedTuple):
    """DAM OKD M-TrackChunk
    """

    __logger = getLogger('OkdMTrackChunk')

    @staticmethod
    def read(stream: io.BufferedReader):
        messages = OkdMTrackMidi.read(stream)
        return OkdMTrackChunk(messages)

    messages: list[OkdMidiMessage]
