import bitstring

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.okd_midi import read_delta_time, read_extended_delta_time, OkdMidiGenericEvent


class OkdPTrackMidi:
    __logger = getLogger('OkdPTrackMidi')

    @staticmethod
    def __process_system_message(stream: bitstring.BitStream, status_byte: int):
        if status_byte == 0xf0:
            event_data_buffer = status_byte.to_bytes(1, byteorder='big')
            while True:
                byte: int = stream.read('uint:8')
                event_data_buffer += byte.to_bytes(1, byteorder='big')
                if byte & 0x80 == 0x80:
                    if byte != 0xf7:
                        OkdPTrackMidi.__logger.warning(
                            'Unterminated SysEx message detected.')
                    break
            return event_data_buffer
        elif status_byte == 0xf8:
            return 3
        elif status_byte == 0xf9:
            return 1
        elif status_byte == 0xfa:
            return 1
        elif status_byte == 0xfd:
            return 0
        elif status_byte == 0xfe:
            byte_1: int = stream.peek('uint:8')
            if byte_1 & 0xf0 == 0xa0:
                return 4
            elif byte_1 & 0xf0 == 0xc0:
                return 3
            else:
                return 1
        else:
            OkdPTrackMidi.__logger.warning(
                f'Unknown message detected. status_byte={hex(status_byte)}')

    @staticmethod
    def __read_chunk(stream: bitstring.BitStream, absolute_time=0):
        messages: list[OkdMidiGenericEvent] = []

        while True:
            status_byte: int = stream.peek('uint:8')
            if status_byte & 0x80 != 0x80:
                delta_time = read_extended_delta_time(stream)
                absolute_time += delta_time
                break
            stream.bytepos += 1

            status_type = status_byte & 0xf0

            data_length: int
            if status_type == 0xb0:
                data_length = 2
            elif status_byte < 0xb1:
                if status_type == 0x80:
                    event_data_buffer = status_byte.to_bytes(
                        1, byteorder='big')
                    event_data_buffer += stream.read('bytes:3')

                    channel = status_byte & 0x0f
                    note_number = event_data_buffer[1]
                    note_on_velocity = event_data_buffer[2]
                    note_off_velocity = event_data_buffer[3]
                    note_on_buffer = bytearray(3)
                    note_on_buffer[0] = 0x90 | channel
                    note_on_buffer[1] = note_number
                    note_on_buffer[2] = note_on_velocity
                    messages.append(OkdMidiGenericEvent(
                        bytes(note_on_buffer), absolute_time))

                    delta_time = read_delta_time(stream)

                    note_off_buffer = bytearray(3)
                    note_on_buffer[0] = 0x80 | channel
                    note_on_buffer[1] = note_number
                    note_on_buffer[2] = note_off_velocity
                    messages.append(
                        OkdMidiGenericEvent(bytes(note_off_buffer), absolute_time + delta_time))
                    continue
                elif status_type == 0x90:
                    event_data_buffer = status_byte.to_bytes(
                        1, byteorder='big')
                    event_data_buffer += stream.read('bytes:2')
                    messages.append(OkdMidiGenericEvent(
                        event_data_buffer, absolute_time))

                    delta_time = read_delta_time(stream) << 2

                    channel = status_byte & 0x0f
                    note_number = event_data_buffer[1]
                    note_off_buffer = bytearray(3)
                    note_off_buffer[0] = 0x80 | channel
                    note_off_buffer[1] = note_number
                    note_off_buffer[2] = 0x40
                    messages.append(OkdMidiGenericEvent(
                        bytes(note_off_buffer), absolute_time + delta_time))
                    continue
                elif status_type == 0xa0:
                    data_length = 1
                else:
                    process_result = OkdPTrackMidi.__process_system_message(
                        stream, status_byte)
                    if process_result is None:
                        continue
                    elif isinstance(process_result, bytes):
                        messages.append(OkdMidiGenericEvent(
                            process_result, absolute_time))
                        continue
                    else:
                        data_length = process_result
            else:
                if status_type != 0xd0:
                    if status_type == 0xe0:
                        data_length = 2
                    elif status_type == 0xc0:
                        data_length = 1
                    else:
                        process_result = OkdPTrackMidi.__process_system_message(
                            stream, status_byte)
                        if process_result is None:
                            continue
                        elif isinstance(process_result, bytes):
                            messages.append(OkdMidiGenericEvent(
                                process_result, absolute_time))
                            continue
                        else:
                            data_length = process_result
                else:
                    data_length = 2

            data_buffer: bytes = stream.read(8 * data_length).bytes
            message_buffer = status_byte.to_bytes(
                1, byteorder='big') + data_buffer
            messages.append(OkdMidiGenericEvent(message_buffer, absolute_time))

        return messages, absolute_time

    @ staticmethod
    def read(stream: bitstring.BitStream):
        track: list[OkdMidiGenericEvent] = []

        stream.pos = stream.length - 32
        end_of_track_buffer: bytes = stream.read('bytes:4')
        if end_of_track_buffer != b'\x00\x00\x00\x00':
            OkdPTrackMidi.__logger.warning('End of track not found.')
            stream.append(b'\x00\x00\x00\x00\x00\x00\x00')
        stream.pos = 0

        absolute_time = 0
        while True:
            end_of_track_buffer: bytes = stream.peek('bytes:3')
            if end_of_track_buffer == b'\x00\x00\x00':
                break

            chunk = OkdPTrackMidi.__read_chunk(stream, absolute_time)
            messages, absolute_time = chunk
            track.extend(messages)

            if stream.peek('uint:8') == 0x00:
                stream.bytepos += 1

        return track
