import bitstring
import mido

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.okd_midi import (
    read_status_byte,
    is_data_bytes,
    read_variable_int,
    write_variable_int,
    read_extended_variable_int,
    write_extended_variable_int,
    OkdMidiGenericMessage,
    OkdMidiMessage,
)
from dam_okd_utility.okd_p_track_info_chunk import (
    OkdPTrackInfoEntry,
)
from dam_okd_utility.okd_extended_p_track_info_chunk import (
    OkdExtendedPTrackInfoEntry,
)
from dam_okd_utility.okd_p3_track_info_chunk import (
    OkdP3TrackInfoChunk,
)
from dam_okd_utility.okd_p_track_midi_data import OkdPTrackAbsoluteTimeMessage
from dam_okd_utility.yamaha_mmt_tg import YamahaMmtTg


class OkdPTrackMidi:
    PORT_COUNT = 5
    CHANNEL_COUNT_PER_PORT = 16
    TOTAL_CHANNEL_COUNT = CHANNEL_COUNT_PER_PORT * PORT_COUNT

    __logger = getLogger("OkdPTrackMidi")

    @staticmethod
    def __relocate_message(
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

        absolute_messages: list[OkdPTrackAbsoluteTimeMessage] = []

        if status_type == 0xF0:
            if status_byte == 0xF0:
                for port in range(OkdPTrackMidi.PORT_COUNT):
                    if (track_info_entry.system_ex_ports >> port) & 0x0001 != 0x0001:
                        continue

                    track = port * OkdPTrackMidi.CHANNEL_COUNT_PER_PORT
                    absolute_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            time,
                            port,
                            track,
                            data,
                        )
                    )
        else:
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
                        OkdPTrackAbsoluteTimeMessage(
                            time, port, track, absolute_message_data
                        )
                    )

        return absolute_messages

    @staticmethod
    def __relative_time_track_to_absolute_time_track(
        track_info_entry: OkdPTrackInfoEntry | OkdExtendedPTrackInfoEntry,
        relative_time_track: list[OkdMidiMessage],
    ):
        is_lossless_track = track_info_entry.track_status & 0x08

        absolute_time_track: list[OkdPTrackAbsoluteTimeMessage] = []
        absolute_time = 0
        is_channel_group_enabled = False
        for message in relative_time_track:
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
                absolute_time_track.extend(
                    OkdPTrackMidi.__relocate_message(
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
                absolute_time_track.extend(
                    OkdPTrackMidi.__relocate_message(
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

                absolute_time_track.extend(
                    OkdPTrackMidi.__relocate_message(
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
                absolute_time_track.extend(
                    OkdPTrackMidi.__relocate_message(
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
                absolute_time_track.extend(
                    OkdPTrackMidi.__relocate_message(
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
                absolute_time_track.extend(
                    OkdPTrackMidi.__relocate_message(
                        track_info_entry,
                        absolute_time,
                        bytes(message_data_bytearray),
                        is_channel_group_enabled,
                    )
                )
            else:
                absolute_time_track.extend(
                    OkdPTrackMidi.__relocate_message(
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

        absolute_time_track.sort(key=lambda absolute_message: absolute_message.time)

        return absolute_time_track

    @staticmethod
    def relative_time_tracks_to_absolute_time_tracks(
        track_info: list[OkdPTrackInfoEntry]
        | list[OkdExtendedPTrackInfoEntry]
        | list[OkdP3TrackInfoChunk],
        relative_time_tracks: list[tuple[int, list[OkdMidiMessage]]],
        general_midi: bool,
    ):
        merged_absolute_time_track: list[OkdPTrackAbsoluteTimeMessage] = []
        relative_time_track_count = len(relative_time_tracks)
        for p_track_chunk_number, relative_time_track in relative_time_tracks:
            track_info_entry: tuple[
                int, OkdPTrackInfoEntry | OkdExtendedPTrackInfoEntry
            ] | None = None
            for index, entry in enumerate(track_info):
                if entry.track_number == p_track_chunk_number:
                    track_info_entry = (index, entry)
            if track_info_entry is None:
                raise ValueError("P-Track Information Entry not found.")

            absolute_time_track = (
                OkdPTrackMidi.__relative_time_track_to_absolute_time_track(
                    track_info_entry[1], relative_time_track
                )
            )
            merged_absolute_time_track.extend(absolute_time_track)

            if general_midi:
                is_sysex_track = False
                tracks_per_sysex_track = OkdPTrackMidi.CHANNEL_COUNT_PER_PORT
                if relative_time_track_count <= 2:
                    is_sysex_track = True
                else:
                    if track_info_entry[0] % 2 == 0:
                        is_sysex_track = True
                        tracks_per_sysex_track = (
                            OkdPTrackMidi.CHANNEL_COUNT_PER_PORT * 2
                        )

                if is_sysex_track:
                    midi_device = YamahaMmtTg()
                    port = track_info_entry[0]
                    track_number = (
                        track_info_entry[0] * OkdPTrackMidi.CHANNEL_COUNT_PER_PORT
                    )

                    # Setup tracks
                    general_midi_messages = (
                        midi_device.get_general_midi_track_setup_messages(
                            port, tracks_per_sysex_track
                        )
                    )
                    merged_absolute_time_track.extend(general_midi_messages)

                    # SysEx messages to GM messages
                    general_midi_messages = (
                        midi_device.sysex_messages_to_general_midi_messages(
                            port,
                            track_number,
                            tracks_per_sysex_track,
                            absolute_time_track,
                        )
                    )
                    merged_absolute_time_track.extend(general_midi_messages)

        merged_absolute_time_track.sort(
            key=lambda absolute_time_message: absolute_time_message.time
        )

        return merged_absolute_time_track

    @staticmethod
    def read(stream: bitstring.BitStream):
        track: list[OkdMidiMessage] = []

        while True:
            end_of_track: bytes = stream.peek("bytes:4")
            if end_of_track == b"\x00\x00\x00\x00":
                break

            delta_time = read_extended_variable_int(stream)

            status_byte = stream.read("uint:8")
            if status_byte == 0x00:
                break
            if status_byte & 0x80 != 0x80:
                raise ValueError(f"Invalid status_byte, status_byte={hex(status_byte)}")
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
                # Alternative CC
                data_length = 1
            elif status_type == 0xB0:
                # Control change
                data_length = 2
            elif status_type == 0xC0:
                # Alternative CC
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
                    data_length = 3
                elif byte & 0xF0 == 0xC0:
                    data_length = 2
                else:
                    data_length = 0
            else:
                OkdPTrackMidi.__logger.warning(
                    f"Unknown message detected. status_byte={hex(status_byte)}"
                )

            status_buffer = status_byte.to_bytes(1, byteorder="big")
            data_buffer = stream.read(8 * data_length).bytes
            message_buffer = status_buffer + data_buffer
            if (
                status_byte != 0xF0
                and status_byte != 0xFE
                and not is_data_bytes(data_buffer)
            ):
                OkdPTrackMidi.__logger.warning(
                    f"Invalid data bytes detected. status_byte={hex(status_byte)} message_buffer={message_buffer.hex()}"
                )
                continue

            duration = 0
            if status_type == 0x80 or status_type == 0x90:
                duration = read_variable_int(stream)

            track.append(OkdMidiGenericMessage(delta_time, message_buffer, duration))

        return track

    @staticmethod
    def __get_midi_tempo(midi: mido.MidiFile):
        for track in midi.tracks:
            for midi_message in track:
                if midi_message.type == "set_tempo":
                    return midi_message.tempo

        return 500000

    @staticmethod
    def __is_meta_track(midi_track: mido.MidiTrack):
        for midi_message in midi_track:
            if isinstance(midi_message, mido.Message):
                return False

        return True

    @staticmethod
    def __get_midi_track_port(midi_track: mido.MidiTrack):
        for midi_message in midi_track:
            if midi_message.type == "midi_port":
                return midi_message.port

        return 0

    @staticmethod
    def __midi_to_absolute_time_tracks(midi: mido.MidiFile):
        midi_tempo = OkdPTrackMidi.__get_midi_tempo(midi)
        ppq_conversion_ratio = 480.0 / midi.ticks_per_beat
        tempo_conversion_ratio = 125.0 / mido.tempo2bpm(midi_tempo)
        time_conversion_ratio = ppq_conversion_ratio * tempo_conversion_ratio

        absolute_time_tracks: list[list[OkdPTrackAbsoluteTimeMessage]] = [
            None
        ] * OkdPTrackMidi.PORT_COUNT
        for midi_track in midi.tracks:
            if OkdPTrackMidi.__is_meta_track(midi_track):
                continue

            port = OkdPTrackMidi.__get_midi_track_port(midi_track)
            if absolute_time_tracks[port] is None:
                absolute_time_tracks[port] = []

            absolute_time = 0
            for midi_message in midi_track:
                midi_message_data = bytes(midi_message.bin())
                status_byte = midi_message_data[0]
                status_type = status_byte & 0xF0

                absolute_time += midi_message.time
                converted_absoulte_time = round(absolute_time * time_conversion_ratio)

                if status_type == 0xF0:
                    # if status_byte == 0xF0:
                    track = port * OkdPTrackMidi.CHANNEL_COUNT_PER_PORT
                    absolute_time_tracks[port].append(
                        OkdPTrackAbsoluteTimeMessage(
                            converted_absoulte_time,
                            port,
                            track,
                            midi_message_data,
                        )
                    )
                else:
                    channel = status_byte & 0x0F
                    track = (port * OkdPTrackMidi.CHANNEL_COUNT_PER_PORT) + channel
                    absolute_time_tracks[port].append(
                        OkdPTrackAbsoluteTimeMessage(
                            converted_absoulte_time,
                            port,
                            track,
                            midi_message_data,
                        )
                    )

        for absolute_time_track in absolute_time_tracks:
            if absolute_time_track is None:
                continue

            absolute_time_track.sort(
                key=lambda absolute_time_message: absolute_time_message.time
            )

        return absolute_time_tracks

    @staticmethod
    def __absolute_time_track_to_relative_time_track(
        absolute_time_track: list[OkdPTrackAbsoluteTimeMessage],
    ):
        relative_time_track: list[OkdMidiMessage] = []
        absolute_time_track_length = len(absolute_time_track)
        current_time = 0
        for absolute_time_message_index, absolute_time_message in enumerate(
            absolute_time_track
        ):
            status_byte = absolute_time_message.data[0]
            status_type = status_byte & 0xF0
            delta_time = absolute_time_message.time - current_time

            if status_type == 0x80:
                # Do nothing
                continue
            elif status_type == 0x90:
                channel = status_byte & 0x0F
                note_number = absolute_time_message.data[1]
                note_off_time = absolute_time_message.time
                for i in range(absolute_time_message_index, absolute_time_track_length):
                    note_off_message = absolute_time_track[i]
                    note_off_message_status_byte = note_off_message.data[0]
                    note_off_message_status_type = note_off_message_status_byte & 0xF0
                    note_off_message_channel = note_off_message_status_byte & 0x0F
                    if (
                        note_off_message_status_type == 0x80
                        and note_off_message_channel == channel
                    ):
                        note_off_message_note_number = note_off_message.data[1]
                        if note_off_message_note_number == note_number:
                            note_off_time = note_off_message.time
                            break
                duration = note_off_time - absolute_time_message.time
                relative_time_track.append(
                    OkdMidiGenericMessage(
                        delta_time,
                        absolute_time_message.data,
                        duration,
                    )
                )
            elif status_type == 0xA0 or status_type == 0xC0:
                message_data = b"\xFE" + absolute_time_message.data
                relative_time_track.append(
                    OkdMidiGenericMessage(
                        delta_time,
                        message_data,
                        0,
                    )
                )
            elif status_type == 0xF0:
                if status_byte == 0xF0:
                    relative_time_track.append(
                        OkdMidiGenericMessage(
                            delta_time,
                            absolute_time_message.data,
                            0,
                        )
                    )
                else:
                    continue
            else:
                relative_time_track.append(
                    OkdMidiGenericMessage(
                        delta_time,
                        absolute_time_message.data,
                        0,
                    )
                )

            current_time = absolute_time_message.time

        return relative_time_track

    @staticmethod
    def midi_to_relative_time_tracks(midi: mido.MidiFile):
        absolute_time_tracks = OkdPTrackMidi.__midi_to_absolute_time_tracks(midi)
        relative_time_tracks: list[list[OkdMidiMessage]] = [
            None
        ] * OkdPTrackMidi.PORT_COUNT
        for absolute_time_track_index in range(OkdPTrackMidi.PORT_COUNT):
            absolute_time_track = absolute_time_tracks[absolute_time_track_index]
            if absolute_time_track is None:
                continue

            relative_time_track = (
                OkdPTrackMidi.__absolute_time_track_to_relative_time_track(
                    absolute_time_track
                )
            )
            relative_time_tracks[absolute_time_track_index] = relative_time_track

        return relative_time_tracks

    @staticmethod
    def write(stream: bitstring.BitStream, track: list[OkdMidiMessage]):
        for message in track:
            status_byte = message.data[0]
            status_type = status_byte & 0xF0

            write_extended_variable_int(stream, message.delta_time)
            stream.append(message.data)

            if status_type == 0x80 or status_type == 0x90:
                write_variable_int(stream, message.duration >> 2)

        stream.append(b"\x00\x00\x00\x00\x00")
