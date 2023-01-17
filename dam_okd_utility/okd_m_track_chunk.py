import bitstring
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.okd_midi import OkdMidiMessage
from dam_okd_utility.okd_m_track_midi import OkdMTrackMidi


class OkdMTrackChunk(NamedTuple):
    """DAM OKD M-Track Chunk"""

    __logger = getLogger("OkdMTrackChunk")

    @staticmethod
    def read(stream: bitstring.BitStream):
        track = OkdMTrackMidi.read(stream)
        return OkdMTrackChunk(track)

    def to_json_serializable(self):
        json_track = []
        for message in self.track:
            json_track.append(
                {
                    "delta_time": message.delta_time,
                    "data_hex": message.data.hex(),
                    "duration": message.duration,
                }
            )
        return {"track": json_track}

    track: list[OkdMidiMessage]
