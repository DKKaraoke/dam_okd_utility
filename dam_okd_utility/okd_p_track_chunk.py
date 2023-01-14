import bitstring
import mido
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.okd_midi import OkdMidiGenericMessage, OkdMidiMessage
from dam_okd_utility.okd_p_track_midi import OkdPTrackMidi


class OkdPTrackChunk(NamedTuple):
    """DAM OKD P-Track Chunk
    """

    __logger = getLogger('OkdPTrackChunk')

    @staticmethod
    def read(stream: bitstring.BitStream):
        track = OkdPTrackMidi.read(stream)
        return OkdPTrackChunk(track)

    def to_midi(self):
        absolute_track = OkdPTrackMidi.to_absolute_track(self.track)

        raw_track: list[tuple[int, mido.Message]] = []
        for absolute_time, message in absolute_track:
            if not isinstance(message, OkdMidiGenericMessage):
                continue

            status_byte = message.data[0]
            try:
                mido.messages.specs.SPEC_BY_STATUS[status_byte]
            except KeyError:
                OkdPTrackChunk.__logger.warning(
                    f'Unknown message detected. status_byte={hex(status_byte)}')
                continue

            # status_type = status_byte & 0xf0
            # # Allow note_off, note_on, pitch_bend
            # if status_type != 0x80 and status_type != 0x90 and status_type != 0xe0:
            #     continue

            midi_message: mido.Message
            try:
                midi_message = mido.Message.from_bytes(message.data)
            except ValueError:
                OkdPTrackChunk.__logger.warning(
                    f'Invalid message data. status_byte={hex(status_byte)}')
                continue
            raw_track.append((absolute_time, midi_message))

        raw_track.sort(key=lambda message: message[0])

        midi = mido.MidiFile()

        setup_track = mido.MidiTrack()
        current_time = 0
        for absolute_time, message in raw_track:
            if hasattr(message, 'channel'):
                continue

            message.time = absolute_time - current_time
            setup_track.append(message)
            current_time = absolute_time

        midi.tracks.append(setup_track)

        for channel in range(16):
            track = mido.MidiTrack()
            current_time = 0
            for absolute_time, message in raw_track:
                if not hasattr(message, 'channel'):
                    continue
                if message.channel != channel:
                    continue
                message.time = absolute_time - current_time
                track.append(message)
                current_time = absolute_time

            midi.tracks.append(track)

        return midi

    track: list[OkdMidiMessage]
