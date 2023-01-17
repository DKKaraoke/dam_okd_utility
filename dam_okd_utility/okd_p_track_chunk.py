import bitstring
import mido
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.dump_memory import dump_memory
from dam_okd_utility.okd_midi import OkdMidiMessage
from dam_okd_utility.okd_p_track_midi_device import OkdPTrackMidiDevice
from dam_okd_utility.okd_p_track_midi import OkdPTrackMidi
from dam_okd_utility.okd_p_track_info_chunk import OkdPTrackInfoEntry
from dam_okd_utility.okd_extended_p_track_info_chunk import OkdExtendedPTrackInfoEntry
from dam_okd_utility.okd_p_track_midi_device import OkdPTrackMidiDevice


class OkdPTrackChunk(NamedTuple):
    """DAM OKD P-Track Chunk"""

    __logger = getLogger("OkdPTrackChunk")

    @staticmethod
    def read(stream: bitstring.BitStream):
        messages = OkdPTrackMidi.read(stream)
        return OkdPTrackChunk(messages)

    @staticmethod
    def to_midi(
        raw_tracks: list[tuple[int, list[OkdMidiMessage]]],
        track_info: list[OkdPTrackInfoEntry] | list[OkdExtendedPTrackInfoEntry],
    ):
        midi_devices: list[OkdPTrackMidiDevice] = []
        current_midi_device: OkdPTrackMidiDevice | None = None
        for track_number, raw_track in raw_tracks:
            midi_device = OkdPTrackMidiDevice.load_from_sysex_messages(raw_track)
            if midi_device is not None:
                current_midi_device = midi_device
            if current_midi_device is None:
                raise ValueError("P-Track MIDI device is not loaded.")

            if midi_device is not None:
                midi_devices.append(midi_device)
            else:
                midi_devices.append(current_midi_device)

        midi = mido.MidiFile()
        raw_track_count = len(raw_tracks)
        for port in range(raw_track_count):
            midi_device_status = midi_devices[port].get_state()
            for channel in range(OkdPTrackMidi.CHANNEL_COUNT_PER_PORT):
                midi_parameter_change = midi_device_status.midi_parameter_changes[
                    channel + 1
                ]

                midi_track = mido.MidiTrack()
                # Port
                midi_track.append(
                    mido.MetaMessage(
                        "midi_port",
                        port=port,
                    )
                )
                # Volume
                midi_track.append(
                    mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x07,
                        value=midi_parameter_change.volume,
                    )
                )
                # Program Change
                midi_track.append(
                    mido.Message(
                        "program_change",
                        channel=channel,
                        program=midi_parameter_change.program_number,
                    )
                )
                # Bend Pitch Control
                midi_track.append(
                    mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x65,
                        value=0x00,
                    )
                )
                midi_track.append(
                    mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x64,
                        value=0x00,
                    )
                )
                midi_track.append(
                    mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x06,
                        value=midi_parameter_change.bend_pitch_control,
                    )
                )

                midi.tracks.append(midi_track)

        # Tempo
        midi.tracks[0].append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(125)))

        absolute_messages = OkdPTrackMidi.to_absolute(raw_tracks, track_info)
        # for message in absolute_messages:
        #     print(
        #         f"time={message.time}, port={message.port}, track={message.track}, data={message.data.hex()}"
        #     )
        track_current_times = [0] * OkdPTrackMidi.TOTAL_CHANNEL_COUNT
        for absolute_message in absolute_messages:
            status_byte = absolute_message.data[0]
            try:
                mido.messages.specs.SPEC_BY_STATUS[status_byte]
            except KeyError:
                OkdPTrackChunk.__logger.warning(
                    f"Unknown message detected. status_byte={hex(status_byte)}"
                )

            delta_time = (
                absolute_message.time - track_current_times[absolute_message.track]
            )
            track_current_times[absolute_message.track] = absolute_message.time

            try:
                midi_message = mido.Message.from_bytes(
                    absolute_message.data, delta_time
                )
            except ValueError:
                OkdPTrackChunk.__logger.warning(
                    f"Invalid message data. status_byte={hex(status_byte)}"
                )
                continue
            midi.tracks[absolute_message.track].append(midi_message)

        return midi

    def to_json_serializable(self):
        json_track = []
        for message in self.messages:
            json_track.append(
                {
                    "delta_time": message.delta_time,
                    "data_hex": message.data.hex(),
                    "duration": message.duration,
                }
            )
        return {"track": json_track}

    messages: list[OkdMidiMessage]
