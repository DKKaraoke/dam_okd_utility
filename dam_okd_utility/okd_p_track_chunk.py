import bitstring
import mido
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.dump_memory import dump_memory
from dam_okd_utility.okd_midi import OkdMidiGenericMessage, OkdMidiMessage
from dam_okd_utility.okd_p_track_midi_device import OkdPTrackMidiDevice
from dam_okd_utility.okd_p_track_midi import OkdPTrackMidi
from dam_okd_utility.okd_p_track_info_chunk import OkdPTrackInfoEntry
from dam_okd_utility.okd_extended_p_track_info_chunk import OkdExtendedPTrackInfoEntry


class OkdPTrackChunk(NamedTuple):
    """DAM OKD P-Track Chunk"""

    __logger = getLogger("OkdPTrackChunk")

    @staticmethod
    def read(stream: bitstring.BitStream):
        track = OkdPTrackMidi.read(stream)
        # for message in track:
        #     print("MSG:", message.data.hex(" "))
        return OkdPTrackChunk(track)

    def to_midi(
        self,
        device: OkdPTrackMidiDevice,
        track_info_entry: OkdPTrackInfoEntry | OkdExtendedPTrackInfoEntry,
        part_number=0,
        total_part_number=0,
    ):
        absolute_track = OkdPTrackMidi.to_absolute_track(self.track)

        raw_track: list[tuple[int, mido.Message]] = []
        for absolute_time, message in absolute_track:
            if not isinstance(message, OkdMidiGenericMessage):
                continue

            status_byte = message.data[0]
            status_type = status_byte & 0xF0
            channel = status_byte & 0x0F
            channel_info_entry = track_info_entry.channel_info[channel]

            if status_type == 0xA0:
                # CC: channel_info_entry.control_change_ax
                message_data_bytearray = bytearray(3)
                message_data_bytearray[0] = 0xB0 | channel
                message_data_bytearray[1] = channel_info_entry.control_change_ax
                message_data_bytearray[2] = message.data[1]
                midi_message = mido.Message.from_bytes(bytes(message_data_bytearray))
                raw_track.append((absolute_time, midi_message))
                continue

            if status_type == 0xC0:
                # CC: channel_info_entry.control_change_cx
                message_data_bytearray = bytearray(3)
                message_data_bytearray[0] = 0xB0 | channel
                message_data_bytearray[1] = channel_info_entry.control_change_cx
                message_data_bytearray[2] = message.data[1]
                midi_message = mido.Message.from_bytes(bytes(message_data_bytearray))
                raw_track.append((absolute_time, midi_message))
                continue

            if status_byte == 0xF8:
                # F8 to CC: 0x14(20) for research
                message_data_bytearray = bytearray(3)
                message_data_bytearray[0] = 0xB0
                message_data_bytearray[1] = 0x14
                message_data_bytearray[2] = message.data[1]
                midi_message = mido.Message.from_bytes(bytes(message_data_bytearray))
                raw_track.append((absolute_time, midi_message))
                continue

            if status_byte == 0xF9:
                # F9 to CC: 0x15(21) for research
                message_data_bytearray = bytearray(3)
                message_data_bytearray[0] = 0xB0
                message_data_bytearray[1] = 0x15
                message_data_bytearray[2] = message.data[1]
                midi_message = mido.Message.from_bytes(bytes(message_data_bytearray))
                raw_track.append((absolute_time, midi_message))
                continue

            if status_byte == 0xFA:
                # FD to CC: 0x16(22) for research
                message_data_bytearray = bytearray(3)
                message_data_bytearray[0] = 0xB0
                message_data_bytearray[1] = 0x16
                message_data_bytearray[2] = message.data[1]
                midi_message = mido.Message.from_bytes(bytes(message_data_bytearray))
                raw_track.append((absolute_time, midi_message))
                continue

            if status_byte == 0xFD:
                # FD to CC: 0x17(23) for research
                message_data_bytearray = bytearray(3)
                message_data_bytearray[0] = 0xB0
                message_data_bytearray[1] = 0x17
                # message_data_bytearray[2] = message.data[1]
                midi_message = mido.Message.from_bytes(bytes(message_data_bytearray))
                raw_track.append((absolute_time, midi_message))
                continue

            if status_byte == 0xFE:
                # FE to CC: 0x18(24) for research
                message_data_bytearray = bytearray(3)
                message_data_bytearray[0] = 0xB0
                message_data_bytearray[1] = 0x18
                message_data_bytearray[2] = message.data[1]
                midi_message = mido.Message.from_bytes(bytes(message_data_bytearray))
                raw_track.append((absolute_time, midi_message))
                continue

            try:
                mido.messages.specs.SPEC_BY_STATUS[status_byte]
            except KeyError:
                OkdPTrackChunk.__logger.warning(
                    f"Unknown message detected. status_byte={hex(status_byte)}"
                )
                continue

            midi_message: mido.Message
            try:
                midi_message = mido.Message.from_bytes(message.data)
            except ValueError:
                OkdPTrackChunk.__logger.warning(
                    f"Invalid message data. status_byte={hex(status_byte)}"
                )
                continue
            raw_track.append((absolute_time, midi_message))

        raw_track.sort(key=lambda message: message[0])

        midi = mido.MidiFile()

        setup_track = mido.MidiTrack()
        setup_track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(125)))
        current_time = 0
        for absolute_time, message in raw_track:
            if hasattr(message, "channel"):
                continue

            message.time = absolute_time - current_time
            setup_track.append(message)
            current_time = absolute_time

        midi.tracks.append(setup_track)

        device_state = device.get_state()

        for channel in range(16):
            track = mido.MidiTrack()

            track.append(
                mido.MetaMessage(
                    "midi_port",
                    port=total_part_number,
                )
            )

            midi_parameter_change_index = 16 * part_number + channel + 1
            midi_parameter_change = device_state.midi_parameter_changes[
                midi_parameter_change_index
            ]
            track.append(
                mido.Message(
                    "program_change",
                    channel=channel,
                    program=midi_parameter_change.program_number,
                )
            )

            current_time = 0
            for absolute_time, message in raw_track:
                if not hasattr(message, "channel"):
                    continue
                if message.channel != channel:
                    continue
                message.time = absolute_time - current_time
                track.append(message)
                current_time = absolute_time

            midi.tracks.append(track)

        return midi

    track: list[OkdMidiMessage]
