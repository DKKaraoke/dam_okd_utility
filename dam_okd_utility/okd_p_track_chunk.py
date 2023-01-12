import io
import mido
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.okd_midi import OkdMidiDeltaTime, OkdMidiGenericEvent, OkdMidiMessage
from dam_okd_utility.okd_p_track_midi import OkdPTrackMidi


class OkdPTrackChunk(NamedTuple):
    """DAM OKD P-Track Chunk
    """

    __logger = getLogger('OkdPTrackChunk')

    @staticmethod
    def read(stream: io.BufferedReader):
        messages = OkdPTrackMidi.read(stream)
        return OkdPTrackChunk(messages)

    def to_midi(self):
        midi = mido.MidiFile()

        for _ in range(16):
            midi_track = mido.MidiTrack()
            midi.tracks.append(midi_track)

        delta_time = 0
        while True:
            try:
                message = self.messages.pop(0)
            except IndexError:
                break
            if isinstance(message, OkdMidiGenericEvent):
                status = message.data[0]
                status_type = status & 0xf0
                if 0xf0 <= status:
                    continue
                try:
                    mido.messages.specs.SPEC_BY_STATUS[status]
                except KeyError:
                    raise RuntimeError(
                        f'Invalid message detected. status={hex(status)}')
                channel = status & 0x0f

                midi_message: mido.Message
                if status_type == 0x80 or status_type == 0x90:
                    note_number: int
                    note_on_velocity: int
                    note_off_velocity: int
                    if status_type == 0x80:
                        note_number = message.data[1]
                        note_on_velocity = message.data[2]
                        note_off_velocity = message.data[3]
                        pass
                    elif status_type == 0x90:
                        note_number = message.data[1]
                        note_on_velocity = message.data[2]
                        note_off_velocity = 64
                        pass
                    else:
                        raise RuntimeError('Invalid status_type.')

                    delta_time_message: OkdMidiMessage
                    try:
                        delta_time_message = self.messages.pop(0)
                    except IndexError:
                        raise RuntimeError('Invalid message sequence.')
                    if not isinstance(delta_time_message, OkdMidiDeltaTime):
                        raise RuntimeError('Invalid message sequence.')

                    midi_message = mido.Message(
                        'note_on', channel=channel, note=note_number, velocity=note_on_velocity, time=delta_time)
                    midi.tracks[channel].append(midi_message)
                    midi_message = mido.Message(
                        'note_off', channel=channel, note=note_number, velocity=note_off_velocity, time=delta_time_message.tick)
                    midi.tracks[channel].append(midi_message)
                    continue
                elif status_type == 0xa0:
                    velocity = message.data[1]
                    midi_message = mido.Message(
                        'polytouch', note=0, value=velocity)
                    midi_message.channel = channel
                else:
                    continue
                midi.tracks[channel].append(midi_message)
            elif isinstance(message, OkdMidiDeltaTime):
                delta_time = message.tick
            else:
                raise RuntimeError('Unknown message detected.')

        return midi

    messages: list[OkdMidiMessage]
