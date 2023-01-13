import bitstring
import mido
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.okd_midi import OkdMidiGenericEvent
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
        absolute_track: list[tuple[int, mido.Message]] = []
        for message in self.track:
            status_byte = message.data[0]
            status_type = status_byte & 0xf0

            try:
                mido.messages.specs.SPEC_BY_STATUS[status_byte]
            except KeyError:
                OkdPTrackChunk.__logger.warning(
                    f'Unknown message detected. status_byte={hex(status_byte)}')
                continue
            channel = status_byte & 0x0f

            # Allow note_off, note_on, pitch_bend
            if status_type != 0x80 and status_type != 0x90 and status_type != 0xe0:
                continue

            if status_type == 0xc0:
                program_number = message.data[1]
                midi_message = mido.Message(
                    'program_change', channel=channel, program=program_number)
                absolute_track.append(
                    (message.absolute_tick, midi_message))
                continue

            if status_type == 0xa0:
                velocity = message.data[1]
                midi_message = mido.Message(
                    'polytouch', note=0, channel=channel, value=velocity)
                absolute_track.append(
                    (message.absolute_tick, midi_message))
                continue

            midi_message: mido.Message
            try:
                midi_message = mido.Message.from_bytes(message.data)
            except ValueError:
                OkdPTrackChunk.__logger.warning(f'Invalid message data. status_byte={status_byte}')
                continue
            absolute_track.append((message.absolute_tick, midi_message))

        absolute_track.sort(key=lambda message: message[0])

        midi = mido.MidiFile()
        for channel in range(16):
            track = mido.MidiTrack()
            current_time = 0
            for absolute_time, event in absolute_track:
                if event.channel != channel:
                    continue
                event.time = absolute_time - current_time
                track.append(event)
                current_time = absolute_time
            midi.tracks.append(track)

        return midi

    track: list[OkdMidiGenericEvent]
