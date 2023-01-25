import bitstring
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.okd_midi import OkdMidiMessage
from dam_okd_utility.okd_m_track_midi import OkdMTrackMidi


class OkdMTrackInterpretation(NamedTuple):
    singing_start_time: int
    hooks: list[tuple[int, int]]
    last_hook: tuple[int, int]
    end_time: int
    w2_cho_fo_time: int


class OkdMTrackChunk(NamedTuple):
    """DAM OKD M-Track Chunk"""

    __logger = getLogger("OkdMTrackChunk")

    @staticmethod
    def read(stream: bitstring.BitStream, chunk_number: int):
        messages = OkdMTrackMidi.read(stream)
        return OkdMTrackChunk(chunk_number, messages)

    @staticmethod
    def to_interpretation(relative_time_track: list[OkdMidiMessage]):
        absolute_time_track = OkdMTrackMidi.relative_time_track_to_absolute_time_track(
            relative_time_track
        )

        singing_start_time = 0
        hooks: list[tuple[int, int]] = []
        last_hook: tuple[int, int] = [0, 0]
        end_time = 0
        w2_cho_fo_time = 0

        current_hook_start_time = 0
        last_hook_start_time = 0

        for absolute_time_message in absolute_time_track:
            status_byte = absolute_time_message.data[0]
            if status_byte == 0xF3:
                mark_type = absolute_time_message.data[1]
                if mark_type == 0x00:
                    current_hook_start_time = absolute_time_message.time
                elif mark_type == 0x01:
                    hooks.append((current_hook_start_time, absolute_time_message.time))
                elif mark_type == 0x02:
                    last_hook_start_time = absolute_time_message.time
                elif mark_type == 0x03:
                    last_hook = (last_hook_start_time, absolute_time_message.time)
            elif status_byte == 0xF5:
                w2_cho_fo_time = absolute_time_message.time
            elif status_byte == 0xF6:
                mark_type = absolute_time_message.data[1]
                if mark_type == 0x00:
                    singing_start_time = absolute_time_message.time
                else:
                    end_time = absolute_time_message.time

        return OkdMTrackInterpretation(
            singing_start_time, hooks, last_hook, end_time, w2_cho_fo_time
        )

    def write(self, stream: bitstring.BitStream):
        OkdMTrackMidi.write(stream, self.messages)

    def to_json_serializable(self):
        json_track = []
        for message in self.messages:
            json_track.append(
                {
                    "delta_time": message.delta_time,
                    "data_hex": message.data.hex(" "),
                    "duration": message.duration,
                }
            )
        return {"track": json_track}

    chunk_number: int
    messages: list[OkdMidiMessage]
