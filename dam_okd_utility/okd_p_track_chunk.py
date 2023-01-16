import bitstring
import mido
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.okd_midi import OkdMidiGenericMessage, OkdMidiMessage
from dam_okd_utility.okd_p_track_midi import OkdPTrackMidi
from dam_okd_utility.okd_p_track_info_chunk import OkdPTrackInfoEntry
from dam_okd_utility.okd_extended_p_track_info_chunk import OkdExtendedPTrackInfoEntry


class OkdPTrackChunk(NamedTuple):
    """DAM OKD P-Track Chunk"""

    __logger = getLogger("OkdPTrackChunk")

    @staticmethod
    def read(stream: bitstring.BitStream):
        track = OkdPTrackMidi.read(stream)
        return OkdPTrackChunk(track)

    def load_memory_from_sysex_messages(track: list[OkdMidiMessage]):
        memory = [0x00] * 0x200000

        valid_sysex_exists = False
        for message in track:
            status_byte = message.data[0]
            if status_byte != 0xF0:
                continue
            manufacture_id = message.data[1]
            if manufacture_id != 0x43:
                OkdPTrackChunk.__logger.warning(
                    f"Unknown manufacture ID detected. manufacture_id={manufacture_id}"
                )
                continue
            if message.data[2] & 0x10 != 0x10:
                OkdPTrackChunk.__logger.warning("Invalid Parameter Change detected.")
                continue
            device_number = message.data[2] & 0x0F
            model_id = message.data[3]
            address = message.data[4] << 14 | message.data[5] << 7 | message.data[6]
            data_length = len(message.data) - 9
            data = message.data[7 : 7 + data_length]
            end_mark = message.data[-1]
            if end_mark != 0xF7:
                OkdPTrackChunk.__logger.warning("Invalid SysEx end mark detected.")
                continue

            memory[address : address + data_length] = data

            valid_sysex_exists = True

        return memory if valid_sysex_exists else None

    # def load_program_numbers_from_sysex_messages(track: list[OkdMidiMessage]):
    #     program_numbers = [0x00] * 16

    #     for message in track:
    #         status_byte = message.data[0]
    #         if status_byte != 0xF0:
    #             continue
    #         manufacture_id = message.data[1]
    #         if manufacture_id != 0x43:
    #             OkdPTrackChunk.__logger.warning(
    #                 f"Unknown manufacture ID detected. manufacture_id={manufacture_id}"
    #             )
    #             continue
    #         if message.data[2] & 0x10 != 0x10:
    #             OkdPTrackChunk.__logger.warning("Invalid Parameter Change detected.")
    #             continue

    #         end_mark = message.data[-1]
    #         if end_mark != 0xF7:
    #             OkdPTrackChunk.__logger.warning("Invalid SysEx end mark detected.")
    #             continue

    #         if message.data[4] != 0x02 or message.data[6] != 0x03:
    #             continue

    #         channel_number = message.data[5]
    #         if 16 < channel_number:
    #             continue
    #         program_number = message.data[7]
    #         print(hex(channel_number), hex(program_number))
    #         program_numbers[channel_number] = program_number
        
    #     return program_numbers

    def to_midi(
        self, track_info_entry: OkdPTrackInfoEntry | OkdExtendedPTrackInfoEntry
    ):
        memory = OkdPTrackChunk.load_memory_from_sysex_messages(self.track)
        if memory is not None:
            OkdPTrackChunk.__logger.debug("MIDI device memory dump:")
            OkdPTrackChunk.__logger.debug("\n" + dump_memory(memory))

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

        for channel in range(16):
            track = mido.MidiTrack()
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
