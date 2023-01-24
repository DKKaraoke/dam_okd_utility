import bitstring
import mido
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.dump_memory import dump_memory
from dam_okd_utility.okd_midi import OkdMidiMessage
from dam_okd_utility.yamaha_mmt_tg import YamahaMmtTg
from dam_okd_utility.okd_p_track_midi import OkdPTrackMidi
from dam_okd_utility.okd_p_track_info_chunk import OkdPTrackInfoEntry
from dam_okd_utility.okd_extended_p_track_info_chunk import OkdExtendedPTrackInfoEntry
from dam_okd_utility.yamaha_mmt_tg import YamahaMmtTg


class OkdPTrackChunk(NamedTuple):
    """DAM OKD P-Track Chunk"""

    __logger = getLogger("OkdPTrackChunk")

    @staticmethod
    def read(stream: bitstring.BitStream, chunk_number: int):
        messages = OkdPTrackMidi.read(stream)
        return OkdPTrackChunk(chunk_number, messages)

    def write(self, stream: bitstring.BitStream):
        OkdPTrackMidi.write(stream, self.messages)

    @staticmethod
    def from_midi(midi: mido.MidiFile, chunk_number: int):
        messages = OkdPTrackMidi.midi_to_relative_time_track(midi)
        return OkdPTrackChunk(chunk_number, messages)

    @staticmethod
    def to_midi(
        track_info: list[OkdPTrackInfoEntry] | list[OkdExtendedPTrackInfoEntry],
        relative_time_tracks: list[tuple[int, list[OkdMidiMessage]]],
        general_midi=True,
    ):
        midi = mido.MidiFile()
        for port in range(OkdPTrackMidi.PORT_COUNT):
            for channel in range(OkdPTrackMidi.CHANNEL_COUNT_PER_PORT):
                midi_track = mido.MidiTrack()
                # Port
                midi_track.append(
                    mido.MetaMessage(
                        "midi_port",
                        port=port,
                    )
                )
                midi.tracks.append(midi_track)

        # Tempo
        midi.tracks[0].append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(125)))

        absolute_time_track = (
            OkdPTrackMidi.relative_time_tracks_to_absolute_time_tracks(
                track_info, relative_time_tracks, general_midi
            )
        )
        track_current_times = [0] * OkdPTrackMidi.TOTAL_CHANNEL_COUNT
        for message in absolute_time_track:
            status_byte = message.data[0]
            status_type = status_byte & 0xF0

            if general_midi and status_type == 0xF0:
                continue

            try:
                mido.messages.specs.SPEC_BY_STATUS[status_byte]
            except KeyError:
                OkdPTrackChunk.__logger.warning(
                    f"Unknown message detected. status_byte={hex(status_byte)}"
                )

            delta_time = message.time - track_current_times[message.track]
            track_current_times[message.track] = message.time

            try:
                midi_message = mido.Message.from_bytes(message.data, delta_time)
            except ValueError:
                OkdPTrackChunk.__logger.warning(
                    f"Invalid message data. status_byte={hex(status_byte)}"
                )
                continue
            midi.tracks[message.track].append(midi_message)

        return midi

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
