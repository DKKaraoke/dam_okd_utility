import bitstring
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.okd_midi import (
    read_status_byte,
    is_data_bytes,
    read_variable_int,
    read_extended_variable_int,
    OkdMidiGenericMessage,
    OkdMidiMessage,
)
from dam_okd_utility.okd_p_track_info_chunk import (
    OkdPTrackInfoEntry,
)
from dam_okd_utility.okd_extended_p_track_info_chunk import (
    OkdExtendedPTrackInfoEntry,
)


class OkdPTrackAbsoluteTrackMessage(NamedTuple):
    time: int
    port: int
    track: int
    data: bytes


class OkdPTrackMidi:
    PORT_COUNT = 5
    CHANNEL_COUNT_PER_PORT = 16
    TOTAL_CHANNEL_COUNT = CHANNEL_COUNT_PER_PORT * PORT_COUNT

    __logger = getLogger("OkdPTrackMidi")

    @staticmethod
    def __message_to_absolute(
        track_info_entry: OkdPTrackInfoEntry | OkdExtendedPTrackInfoEntry,
        time: int,
        data: bytes,
        is_channel_group_enabled: bool,
    ):
        status_byte = data[0]
        status_type = status_byte & 0xF0

        if status_byte == 0xFE:
            data = data[1:]
            status_byte = data[0]
            status_type = status_byte & 0xF0

        if status_type == 0xF0:
            return []
            # return [
            #     OkdPTrackAbsoluteTrackMessage(
            #         time,
            #         track_info_entry.system_ex_port,
            #         OkdPTrackMidi.CHANNEL_COUNT_PER_PORT * track_number,
            #         data,
            #     )
            # ]
        else:
            absolute_messages: list[OkdPTrackAbsoluteTrackMessage] = []

            channel = status_byte & 0x0F
            channel_info_entry = track_info_entry.channel_info[channel]

            single_channel_group = track_info_entry.single_channel_groups[channel]
            # Fill single channel group
            if single_channel_group == 0x0000:
                single_channel_group = 0x0001 << channel

            for port in range(OkdPTrackMidi.PORT_COUNT):
                # Check target track
                if (channel_info_entry.ports >> port) & 0x0001 != 0x0001:
                    continue

                for grouped_channel in range(OkdPTrackMidi.CHANNEL_COUNT_PER_PORT):
                    if is_channel_group_enabled:
                        if (
                            track_info_entry.channel_groups[channel] >> grouped_channel
                        ) & 0x0001 != 0x0001:
                            continue
                    else:
                        if (single_channel_group >> grouped_channel) & 0x0001 != 0x0001:
                            continue

                    track = (
                        port * OkdPTrackMidi.CHANNEL_COUNT_PER_PORT
                    ) + grouped_channel
                    absolute_message_status_byte = status_type | grouped_channel
                    absolute_message_data = (
                        absolute_message_status_byte.to_bytes(1, byteorder="big")
                        + data[1:]
                    )
                    absolute_messages.append(
                        OkdPTrackAbsoluteTrackMessage(
                            time, port, track, absolute_message_data
                        )
                    )

            return absolute_messages

    @staticmethod
    def __one_track_to_absolute(
        track_info_entry: OkdPTrackInfoEntry | OkdExtendedPTrackInfoEntry,
        track: list[OkdMidiMessage],
    ):
        is_lossless_track = track_info_entry.track_status & 0x08

        absolute_track: list[OkdPTrackAbsoluteTrackMessage] = []
        absolute_time = 0
        is_channel_group_enabled = False
        for message in track:
            if not isinstance(message, OkdMidiGenericMessage):
                continue

            absolute_time += message.delta_time

            status_byte = message.data[0]
            status_type = status_byte & 0xF0

            if status_type == 0x80:
                channel = status_byte & 0x0F
                note_number = message.data[1]
                note_on_velocity = message.data[2]
                note_off_velocity = message.data[3]
                duration = message.duration
                if not is_lossless_track:
                    duration <<= 2

                note_on_bytearray = bytearray(3)
                note_on_bytearray[0] = 0x90 | channel
                note_on_bytearray[1] = note_number
                note_on_bytearray[2] = note_on_velocity
                absolute_track.extend(
                    OkdPTrackMidi.__message_to_absolute(
                        track_info_entry,
                        absolute_time,
                        bytes(note_on_bytearray),
                        is_channel_group_enabled,
                    )
                )

                note_off_bytearray = bytearray(3)
                note_off_bytearray[0] = 0x80 | channel
                note_off_bytearray[1] = note_number
                note_off_bytearray[2] = note_off_velocity
                absolute_track.extend(
                    OkdPTrackMidi.__message_to_absolute(
                        track_info_entry,
                        absolute_time + duration,
                        bytes(note_off_bytearray),
                        is_channel_group_enabled,
                    )
                )
            elif status_type == 0x90:
                channel = status_byte & 0x0F
                note_number = message.data[1]
                note_on_velocity = message.data[2]
                duration = message.duration
                if not is_lossless_track:
                    duration <<= 2

                absolute_track.extend(
                    OkdPTrackMidi.__message_to_absolute(
                        track_info_entry,
                        absolute_time,
                        bytes(message.data),
                        is_channel_group_enabled,
                    )
                )

                note_off_bytearray = bytearray(3)
                note_off_bytearray[0] = 0x80 | channel
                note_off_bytearray[1] = note_number
                note_off_bytearray[2] = 0x40
                absolute_track.extend(
                    OkdPTrackMidi.__message_to_absolute(
                        track_info_entry,
                        absolute_time + duration,
                        bytes(note_off_bytearray),
                        is_channel_group_enabled,
                    )
                )
            elif status_type == 0xA0:
                # CC: channel_info_entry.control_change_ax
                channel = status_byte & 0x0F
                channel_info_entry = track_info_entry.channel_info[channel]

                message_data_bytearray = bytearray(3)
                message_data_bytearray[0] = 0xB0 | channel
                message_data_bytearray[1] = channel_info_entry.control_change_ax
                message_data_bytearray[2] = message.data[1]
                absolute_track.extend(
                    OkdPTrackMidi.__message_to_absolute(
                        track_info_entry,
                        absolute_time,
                        bytes(message_data_bytearray),
                        is_channel_group_enabled,
                    )
                )
            elif status_type == 0xC0:
                # CC: channel_info_entry.control_change_cx
                channel = status_byte & 0x0F
                channel_info_entry = track_info_entry.channel_info[channel]

                message_data_bytearray = bytearray(3)
                message_data_bytearray[0] = 0xB0 | channel
                message_data_bytearray[1] = channel_info_entry.control_change_cx
                message_data_bytearray[2] = message.data[1]
                absolute_track.extend(
                    OkdPTrackMidi.__message_to_absolute(
                        track_info_entry,
                        absolute_time,
                        bytes(message_data_bytearray),
                        is_channel_group_enabled,
                    )
                )
            else:
                absolute_track.extend(
                    OkdPTrackMidi.__message_to_absolute(
                        track_info_entry,
                        absolute_time,
                        bytes(message.data),
                        is_channel_group_enabled,
                    )
                )

            if status_byte == 0xFD:
                is_channel_group_enabled = True
            else:
                is_channel_group_enabled = False

        return absolute_track

    @staticmethod
    def to_absolute(
        tracks: list[tuple[int, list[OkdMidiMessage]]],
        track_info: list[OkdPTrackInfoEntry] | list[OkdExtendedPTrackInfoEntry],
    ):
        merged_absolute_track: list[OkdPTrackAbsoluteTrackMessage] = []
        # midi_device: OkdPTrackMidiDevice | None = None
        for track_number, track in tracks:
            # loaded_midi_device = OkdPTrackMidiDevice.load_from_sysex_messages(track)
            # if loaded_midi_device is not None:
            #     midi_device = loaded_midi_device

            # if midi_device is None:
            #     raise ValueError("P-Track MIDI device is not loaded.")

            track_info_entry: OkdPTrackInfoEntry | OkdExtendedPTrackInfoEntry | None = (
                None
            )
            for entry in track_info:
                if entry.track_number == track_number:
                    track_info_entry = entry
            if track_info_entry is None:
                raise ValueError("P-Track Information Entry not found.")

            absolute_track = OkdPTrackMidi.__one_track_to_absolute(
                track_info_entry, track
            )
            merged_absolute_track.extend(absolute_track)

        merged_absolute_track.sort(key=lambda absolute_message: absolute_message.time)

        return merged_absolute_track

    @staticmethod
    def read(stream: bitstring.BitStream):
        track: list[OkdMidiMessage] = []

        while True:
            try:
                end_of_track: bytes = stream.peek("bytes:4")
                if end_of_track == b"\x00\x00\x00\x00":
                    break

                delta_time = read_extended_variable_int(stream)

                status_byte = read_status_byte(stream)
                status_type = status_byte & 0xF0

                data_length = 0
                # Channel voice messages
                if status_type == 0x80:
                    # Note off
                    data_length = 3
                elif status_type == 0x90:
                    # Note on
                    data_length = 2
                elif status_type == 0xA0:
                    # Expression
                    data_length = 1
                elif status_type == 0xB0:
                    # Control change
                    data_length = 2
                elif status_type == 0xC0:
                    # Modulation
                    data_length = 1
                elif status_type == 0xD0:
                    # Channel pressure
                    data_length = 1
                elif status_type == 0xE0:
                    # Pitch bend
                    data_length = 2
                # System messages
                elif status_byte == 0xF0:
                    start_position = stream.bytepos
                    unterminated_sysex_detected = False
                    while True:
                        byte = stream.read("uint:8")
                        if byte & 0x80 == 0x80:
                            if byte != 0xF7:
                                OkdPTrackMidi.__logger.warning(
                                    f"Unterminated SysEx message detected. stop_byte={hex(byte)}"
                                )
                                unterminated_sysex_detected = True
                            data_length = stream.bytepos - start_position
                            stream.bytepos = start_position
                            break
                    if unterminated_sysex_detected:
                        continue
                    stream.bytepos = start_position
                elif status_byte == 0xF8:
                    data_length = 3
                elif status_byte == 0xF9:
                    data_length = 1
                elif status_byte == 0xFA:
                    data_length = 1
                elif status_byte == 0xFD:
                    data_length = 0
                elif status_byte == 0xFE:
                    byte = stream.peek("uint:8")
                    if byte & 0xF0 == 0xA0:
                        data_length = 4
                    elif byte & 0xF0 == 0xC0:
                        data_length = 3
                    else:
                        data_length = 1
                else:
                    OkdPTrackMidi.__logger.warning(
                        f"Unknown message detected. status_byte={hex(status_byte)}"
                    )

                status_buffer = status_byte.to_bytes(1, byteorder="big")
                data_buffer = stream.read(8 * data_length).bytes
                message_buffer = status_buffer + data_buffer
                if status_byte != 0xF0 and not is_data_bytes(data_buffer):
                    OkdPTrackMidi.__logger.warning(
                        f"Invalid data bytes detected. message_buffer={message_buffer.hex()}"
                    )
                    continue

                duration = 0
                if status_type == 0x80 or status_type == 0x90:
                    duration = read_variable_int(stream)

                track.append(
                    OkdMidiGenericMessage(delta_time, message_buffer, duration)
                )

            except bitstring.ReadError:
                OkdPTrackMidi.__logger.warning(f"Reached to end of stream.")
                # Ignore irregular
                break

            except ValueError as e:
                OkdPTrackMidi.__logger.warning(f'Invalid value detected. error="{e}"')
                # Ignore irregular
                pass

        return track
